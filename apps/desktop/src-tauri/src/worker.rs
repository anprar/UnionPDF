//! Host side of the PDFBox authoring worker (Java process, JSON lines over stdin/stdout).
//!
//! Policy:
//! - One request at a time (the process mutex is held for the whole request).
//! - Cancellation and timeout kill the process; the next request starts a fresh one.
//! - If the process dies, the pending request fails with a structured error.
//! - The worker exits on its own when stdin closes (e.g. the app exits).
//! - Temporary input/output files are owned by `TempPdf` and removed on drop.

use crate::error::{AppError, AppResult};
use serde_json::{json, Value};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::mpsc::{self, Receiver, RecvTimeoutError};
use std::sync::Mutex;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

pub const PROTOCOL: u64 = 1;
const READY_TIMEOUT: Duration = Duration::from_secs(30);

#[derive(Debug, Clone)]
pub struct WorkerConfig {
    pub java: PathBuf,
    pub jar: PathBuf,
}

/// Finds the Java runtime and the worker jar.
///
/// The bundled runtime (`<worker dir>/jre`) is always preferred. Falling back to an external
/// Java (`UNIONPDF_JAVA`, `JAVA_HOME`, `PATH`) is only allowed in development builds or when
/// `UNIONPDF_ALLOW_EXTERNAL_JAVA=1` is set explicitly - a release build must never silently
/// depend on a Java installation that is not part of the package.
pub fn discover(worker_dirs: &[PathBuf]) -> Result<WorkerConfig, String> {
    let jar_dir = worker_dirs.iter().find(|d| d.join("unionpdf-worker.jar").is_file());
    let Some(jar_dir) = jar_dir else {
        let tried: Vec<String> = worker_dirs.iter().map(|d| d.display().to_string()).collect();
        return Err(format!(
            "unionpdf-worker.jar tidak ditemukan (dicari di: {}). Jalankan scripts/prepare-pdfbox.ps1.",
            tried.join("; ")
        ));
    };
    let exe = if cfg!(windows) { "java.exe" } else { "java" };
    let bundled = jar_dir.join("jre").join("bin").join(exe);
    if bundled.is_file() {
        return Ok(WorkerConfig { java: bundled, jar: jar_dir.join("unionpdf-worker.jar") });
    }
    let allow_external = cfg!(debug_assertions) || std::env::var("UNIONPDF_ALLOW_EXTERNAL_JAVA").is_ok();
    if allow_external {
        let mut candidates: Vec<PathBuf> = Vec::new();
        if let Ok(j) = std::env::var("UNIONPDF_JAVA") {
            candidates.push(PathBuf::from(j));
        }
        if let Ok(h) = std::env::var("JAVA_HOME") {
            candidates.push(PathBuf::from(h).join("bin").join(exe));
        }
        if let Some(path) = std::env::var_os("PATH") {
            for dir in std::env::split_paths(&path) {
                candidates.push(dir.join(exe));
            }
        }
        if let Some(java) = candidates.into_iter().find(|p| p.is_file()) {
            return Ok(WorkerConfig { java, jar: jar_dir.join("unionpdf-worker.jar") });
        }
    }
    Err(format!(
        "runtime Java bawaan tidak ditemukan ({}). Jalankan scripts/prepare-java-runtime.ps1 \
         (atau set UNIONPDF_ALLOW_EXTERNAL_JAVA=1 untuk memakai Java eksternal).",
        bundled.display()
    ))
}

enum Msg {
    Line(Value),
    Eof,
}

struct Proc {
    child: Child,
    stdin: ChildStdin,
    rx: Receiver<Msg>,
}

pub struct PdfboxWorker {
    cfg: WorkerConfig,
    proc_: Mutex<Option<Proc>>,
    next_id: AtomicU64,
}

fn worker_failed(msg: impl Into<String>) -> AppError {
    AppError::WorkerFailed(msg.into())
}

impl PdfboxWorker {
    pub fn new(cfg: WorkerConfig) -> Self {
        PdfboxWorker { cfg, proc_: Mutex::new(None), next_id: AtomicU64::new(1) }
    }

    fn spawn(&self) -> AppResult<Proc> {
        let mut cmd = Command::new(&self.cfg.java);
        cmd.arg("-Dfile.encoding=UTF-8")
            .arg("-Djava.awt.headless=true")
            .arg("-jar")
            .arg(&self.cfg.jar)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            const CREATE_NO_WINDOW: u32 = 0x0800_0000;
            cmd.creation_flags(CREATE_NO_WINDOW);
        }
        let mut child = cmd.spawn().map_err(|e| AppError::WorkerUnavailable(format!("gagal menjalankan Java: {e}")))?;
        let stdin = child.stdin.take().ok_or_else(|| worker_failed("stdin worker tidak tersedia"))?;
        let stdout = child.stdout.take().ok_or_else(|| worker_failed("stdout worker tidak tersedia"))?;
        let stderr = child.stderr.take();
        let (tx, rx) = mpsc::channel();
        std::thread::spawn(move || {
            for line in BufReader::new(stdout).lines() {
                let Ok(line) = line else { break };
                match serde_json::from_str::<Value>(&line) {
                    Ok(v) => {
                        if tx.send(Msg::Line(v)).is_err() {
                            return;
                        }
                    }
                    Err(_) => eprintln!("[pdfbox-worker] baris non-protokol diabaikan ({} byte)", line.len()),
                }
            }
            let _ = tx.send(Msg::Eof);
        });
        if let Some(err) = stderr {
            std::thread::spawn(move || {
                for line in BufReader::new(err).lines().map_while(Result::ok) {
                    let short: String = line.chars().take(300).collect();
                    eprintln!("[pdfbox-worker] {short}");
                }
            });
        }
        let mut p = Proc { child, stdin, rx };
        let start = Instant::now();
        loop {
            match p.rx.recv_timeout(Duration::from_millis(200)) {
                Ok(Msg::Line(v)) if v["type"] == "ready" => {
                    if v["protocol"].as_u64() != Some(PROTOCOL) {
                        let _ = p.child.kill();
                        return Err(worker_failed(format!("versi protokol worker tidak cocok: {}", v["protocol"])));
                    }
                    return Ok(p);
                }
                Ok(Msg::Line(_)) => continue,
                Ok(Msg::Eof) | Err(RecvTimeoutError::Disconnected) => {
                    let status = p.child.wait().ok();
                    return Err(worker_failed(format!("worker berhenti saat start (status {status:?})")));
                }
                Err(RecvTimeoutError::Timeout) if start.elapsed() > READY_TIMEOUT => {
                    let _ = p.child.kill();
                    let _ = p.child.wait();
                    return Err(worker_failed("worker tidak siap dalam 30 detik"));
                }
                Err(RecvTimeoutError::Timeout) => continue,
            }
        }
    }

    fn kill(slot: &mut Option<Proc>) {
        if let Some(mut p) = slot.take() {
            let _ = p.child.kill();
            let _ = p.child.wait();
        }
    }

    /// Sends one request and waits for its result, reporting progress stages.
    pub fn request(
        &self,
        op: &str,
        params: Value,
        timeout: Duration,
        cancel: &AtomicBool,
        progress: &dyn Fn(&str),
    ) -> AppResult<Value> {
        let mut slot = self.proc_.lock().unwrap_or_else(|p| p.into_inner());
        if cancel.load(Ordering::SeqCst) {
            return Err(AppError::Cancelled);
        }
        if slot.is_none() {
            progress("Menyalakan worker PDFBox");
            *slot = Some(self.spawn()?);
        }
        let id = format!("r{}", self.next_id.fetch_add(1, Ordering::SeqCst));
        let line = json!({"id": id, "op": op, "params": params}).to_string();
        let write_ok = {
            let p = slot.as_mut().unwrap();
            writeln!(p.stdin, "{line}").and_then(|_| p.stdin.flush()).is_ok()
        };
        if !write_ok {
            Self::kill(&mut slot);
            return Err(worker_failed("worker tidak menerima request (proses berhenti)"));
        }
        let start = Instant::now();
        loop {
            if cancel.load(Ordering::SeqCst) {
                Self::kill(&mut slot);
                return Err(AppError::Cancelled);
            }
            if start.elapsed() >= timeout {
                Self::kill(&mut slot);
                return Err(worker_failed(format!("worker melewati batas waktu {} detik; proses dihentikan", timeout.as_secs())));
            }
            let msg = slot.as_ref().unwrap().rx.recv_timeout(Duration::from_millis(50));
            match msg {
                Ok(Msg::Line(v)) => {
                    if v["id"].as_str() != Some(id.as_str()) {
                        continue;
                    }
                    match v["type"].as_str() {
                        Some("progress") => progress(v["stage"].as_str().unwrap_or("")),
                        Some("result") => return Ok(v["data"].clone()),
                        Some("error") => return Err(map_worker_error(&v)),
                        _ => {}
                    }
                }
                Ok(Msg::Eof) | Err(RecvTimeoutError::Disconnected) => {
                    let status = slot.as_mut().and_then(|p| p.child.wait().ok());
                    *slot = None;
                    return Err(worker_failed(format!("worker berhenti tak terduga (status {status:?})")));
                }
                Err(RecvTimeoutError::Timeout) => {}
            }
        }
    }

    /// Kills the running process, if any (test hook and shutdown helper).
    pub fn shutdown(&self) {
        Self::kill(&mut self.proc_.lock().unwrap_or_else(|p| p.into_inner()));
    }

    #[cfg(test)]
    pub fn process_id(&self) -> Option<u32> {
        self.proc_.lock().unwrap().as_ref().map(|p| p.child.id())
    }
}

impl Drop for PdfboxWorker {
    fn drop(&mut self) {
        self.shutdown();
    }
}

fn map_worker_error(v: &Value) -> AppError {
    let code = v["code"].as_str().unwrap_or("worker_error").to_string();
    let mut message = v["message"].as_str().unwrap_or("").to_string();
    if let Some(errs) = v["details"]["errors"].as_array() {
        let parts: Vec<String> = errs
            .iter()
            .map(|e| format!("{}: {}", e["name"].as_str().unwrap_or("?"), e["message"].as_str().unwrap_or("")))
            .collect();
        if !parts.is_empty() {
            message = format!("{message} ({})", parts.join("; "));
        }
    }
    match code.as_str() {
        "password_required" => AppError::PasswordRequired,
        _ => AppError::Worker { code, message },
    }
}

/// A temporary PDF path removed on drop.
pub struct TempPdf(PathBuf);

impl TempPdf {
    pub fn new(tag: &str) -> AppResult<Self> {
        let dir = std::env::temp_dir().join("unionpdf");
        std::fs::create_dir_all(&dir)?;
        let nanos = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_nanos()).unwrap_or(0);
        Ok(TempPdf(dir.join(format!("{tag}-{}-{nanos}.pdf", std::process::id()))))
    }

    pub fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TempPdf {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.0);
    }
}
