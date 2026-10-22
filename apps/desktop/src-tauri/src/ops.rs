//! Document workspace and page/authoring operations. Independent of Tauri so it can be tested.
//!
//! Concurrency model: the `docs` mutex guards the open documents. A document has at most one
//! mutating job at a time (`busy`), and every mutation bumps `revision`; a job that started
//! from revision R only applies its result if the document is still at R. Operations that
//! produce new files never write over an input file (see `atomic::write_atomic`).

use crate::atomic::write_atomic;
use crate::engine::{PageInfo, PdfDoc, PdfEngine, RenderedPage};
use crate::error::{AppError, AppResult};
use crate::jobs::e2e_delay;
use crate::pages::parse_selection;
use crate::worker::{PdfboxWorker, TempPdf};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;

pub(crate) const WORKER_TIMEOUT: Duration = Duration::from_secs(300);

pub struct DocEntry {
    pub path: PathBuf,
    pub doc: Box<dyn PdfDoc>,
    pub dirty: bool,
    pub revision: u64,
    pub busy: bool,
}

#[derive(Default)]
pub struct Workspace {
    engine: Mutex<Option<Arc<dyn PdfEngine>>>,
    worker: Mutex<Option<Arc<PdfboxWorker>>>,
    docs: Mutex<HashMap<u32, DocEntry>>,
    next_id: AtomicU32,
}

#[derive(Debug, Clone, Serialize)]
pub struct DocInfo {
    pub doc_id: u32,
    pub path: String,
    pub file_name: String,
    pub page_count: u32,
    pub pages: Vec<PageInfo>,
    pub dirty: bool,
    pub revision: u64,
    pub has_form: bool,
    pub outline_count: usize,
}

#[derive(Debug, Clone, Serialize)]
pub struct OpResult {
    pub output_path: String,
    pub page_count: u32,
    pub verified: bool,
    pub engine: String,
    pub checks: Vec<String>,
    /// Intended structural changes (e.g. bookmarks to excluded pages removed).
    pub changes: Vec<String>,
    /// Information that is lost or not verified.
    pub limitations: Vec<String>,
}

/// Result of a dry run shown to the user before executing an operation.
#[derive(Debug, Clone, Serialize)]
pub struct Preflight {
    pub engine: String,
    pub changes: Vec<String>,
    pub limitations: Vec<String>,
    pub requires_confirmation: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct AnnotationRequest {
    pub page: u32,
    /// "highlight" | "underline" | "strikeout" | "note" | "freetext"
    pub kind: String,
    /// Displayed-page rectangle in points, origin top-left: [x0, y0, x1, y1].
    pub rect: [f32; 4],
    pub contents: Option<String>,
    pub color: Option<[f32; 3]>,
}

fn file_name(p: &Path) -> String {
    p.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default()
}

/// Reopens `path` with the engine and compares page count, size and rotation with `expected`;
/// optionally also the number of bookmarks (cross-engine check of worker output).
pub fn verify_output(
    engine: &dyn PdfEngine,
    path: &Path,
    expected: &[PageInfo],
    expected_outline: Option<usize>,
) -> AppResult<Vec<String>> {
    let doc = engine
        .open_file(path)
        .map_err(|e| AppError::VerificationFailed(format!("output tidak dapat dibuka ulang: {e}")))?;
    let pages = doc.pages()?;
    if pages.len() != expected.len() {
        return Err(AppError::VerificationFailed(format!(
            "jumlah halaman output {} ≠ yang diharapkan {}",
            pages.len(),
            expected.len()
        )));
    }
    for (i, (got, want)) in pages.iter().zip(expected).enumerate() {
        if (got.width - want.width).abs() > 0.6 || (got.height - want.height).abs() > 0.6 || got.rotation != want.rotation {
            return Err(AppError::VerificationFailed(format!(
                "halaman {} berbeda: {:.1}×{:.1} rot {}° (diharapkan {:.1}×{:.1} rot {}°)",
                i + 1,
                got.width,
                got.height,
                got.rotation,
                want.width,
                want.height,
                want.rotation
            )));
        }
    }
    let mut checks = vec![
        format!("Output dibuka ulang dengan {}", engine.label()),
        format!("{} halaman sesuai harapan", pages.len()),
        "Ukuran dan rotasi setiap halaman sesuai".into(),
    ];
    if let Some(n) = expected_outline {
        let got = doc.outline_count();
        if got != n {
            return Err(AppError::VerificationFailed(format!("jumlah bookmark output {got} ≠ laporan PDFBox {n}")));
        }
        checks.push(format!("{n} bookmark terbaca PDFium, sesuai laporan PDFBox"));
    }
    Ok(checks)
}

fn names(v: &Value) -> Vec<String> {
    v.as_array().map(|a| a.iter().filter_map(|x| x.as_str().map(String::from)).collect()).unwrap_or_default()
}

fn list_preview(items: &[String]) -> String {
    let shown: Vec<&str> = items.iter().take(5).map(|s| s.as_str()).collect();
    let more = if items.len() > 5 { format!(" (+{} lagi)", items.len() - 5) } else { String::new() };
    format!("{}{more}", shown.join(", "))
}

/// Human-readable lines for a PDFBox `extract` report. Everything listed is removed from the output.
fn extract_report_lines(r: &Value) -> (Vec<String>, Vec<String>) {
    let mut changes = Vec::new();
    let mut limits = Vec::new();
    let removed = names(&r["bookmarks_removed"]);
    if !removed.is_empty() {
        changes.push(format!("{} bookmark menuju halaman yang tidak diekstrak dihapus: {}", removed.len(), list_preview(&removed)));
    }
    let detached = names(&r["bookmarks_detached"]);
    if !detached.is_empty() {
        changes.push(format!(
            "{} bookmark dipertahankan tanpa tujuan (tujuannya tidak diekstrak, sub-bookmark masih ada): {}",
            detached.len(),
            list_preview(&detached)
        ));
    }
    let links = r["links_removed"].as_u64().unwrap_or(0);
    if links > 0 {
        changes.push(format!("{links} link internal menuju halaman yang tidak diekstrak dihapus"));
    }
    let fields = names(&r["fields_removed"]);
    if !fields.is_empty() {
        changes.push(format!("Field form yang hanya ada di halaman tidak diekstrak dihapus: {}", list_preview(&fields)));
    }
    let widgets = r["widgets_removed"].as_u64().unwrap_or(0);
    if widgets > 0 {
        changes.push(format!("{widgets} widget field di halaman tidak diekstrak dilepas (field tetap ada)"));
    }
    limits.extend(names(&r["warnings"]));
    (changes, limits)
}

fn merge_report_lines(r: &Value) -> (Vec<String>, Vec<String>) {
    let mut changes = Vec::new();
    let mut limits = names(&r["warnings"]);
    if let Some(map) = r["fields_renamed"].as_object() {
        if !map.is_empty() {
            let pairs: Vec<String> = map.iter().map(|(k, v)| format!("{k} → {}", v.as_str().unwrap_or("?"))).collect();
            changes.push(format!("Field dokumen kedua yang namanya sama diganti nama: {}", list_preview(&pairs)));
        }
    }
    let before = r["bookmarks_before"].as_u64().unwrap_or(0);
    let after = r["bookmarks_after"].as_u64().unwrap_or(0);
    if before > 0 && before == after {
        changes.push(format!("{after} bookmark dari kedua dokumen dipertahankan"));
    }
    if r["fields_before"].as_u64() != r["fields_after"].as_u64() {
        limits.push("Jumlah field form berubah setelah digabung".into());
    }
    (changes, limits)
}

struct Snapshot {
    input: TempPdf,
    revision: u64,
    pages: Vec<PageInfo>,
    path: PathBuf,
}

struct BusyGuard<'a> {
    ws: &'a Workspace,
    id: u32,
}

impl Drop for BusyGuard<'_> {
    fn drop(&mut self) {
        if let Some(e) = self.ws.docs.lock().unwrap_or_else(|p| p.into_inner()).get_mut(&self.id) {
            e.busy = false;
        }
    }
}

impl Workspace {
    pub fn set_engine(&self, engine: Arc<dyn PdfEngine>) {
        *self.engine.lock().unwrap() = Some(engine);
    }

    pub fn set_worker(&self, worker: Arc<PdfboxWorker>) {
        *self.worker.lock().unwrap() = Some(worker);
    }

    pub fn engine(&self) -> AppResult<Arc<dyn PdfEngine>> {
        self.engine
            .lock()
            .unwrap()
            .clone()
            .ok_or_else(|| AppError::EngineUnavailable("pdfium.dll belum dimuat".into()))
    }

    pub fn worker(&self) -> Option<Arc<PdfboxWorker>> {
        self.worker.lock().unwrap().clone()
    }

    fn require_worker(&self) -> AppResult<Arc<PdfboxWorker>> {
        self.worker().ok_or_else(|| AppError::WorkerUnavailable("worker tidak dikonfigurasi".into()))
    }

    fn info_of(id: u32, e: &DocEntry) -> AppResult<DocInfo> {
        let pages = e.doc.pages()?;
        Ok(DocInfo {
            doc_id: id,
            path: e.path.to_string_lossy().to_string(),
            file_name: file_name(&e.path),
            page_count: pages.len() as u32,
            pages,
            dirty: e.dirty,
            revision: e.revision,
            has_form: e.doc.has_form(),
            outline_count: e.doc.outline_count(),
        })
    }

    pub fn open(&self, path: &Path) -> AppResult<DocInfo> {
        let doc = self.engine()?.open_file(path)?;
        if doc.page_count() == 0 {
            return Err(AppError::Corrupt("dokumen tidak memiliki halaman".into()));
        }
        let id = self.next_id.fetch_add(1, Ordering::SeqCst) + 1;
        let entry = DocEntry { path: path.to_path_buf(), doc, dirty: false, revision: 1, busy: false };
        let info = Self::info_of(id, &entry)?;
        self.docs.lock().unwrap().insert(id, entry);
        Ok(info)
    }

    pub fn close(&self, id: u32) -> AppResult<()> {
        self.docs.lock().unwrap().remove(&id).map(|_| ()).ok_or(AppError::DocumentNotOpen(id))
    }

    pub fn render(&self, id: u32, index: u32, scale: f32) -> AppResult<RenderedPage> {
        let docs = self.docs.lock().unwrap();
        docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?.doc.render(index, scale)
    }

    /// Text runs of a page (displayed page space) for the selectable text layer.
    pub fn text_spans(&self, id: u32, index: u32) -> AppResult<Vec<crate::engine::TextSpan>> {
        let docs = self.docs.lock().unwrap();
        docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?.doc.text_spans(index)
    }

    /// Searches the whole document (no bitmaps are loaded) and returns the match boxes.
    pub fn search_document(
        &self,
        id: u32,
        query: &str,
        case_sensitive: bool,
        limit: usize,
        cancel: &AtomicBool,
        progress: &dyn Fn(&str),
    ) -> AppResult<Vec<crate::engine::SearchHit>> {
        let count = {
            let docs = self.docs.lock().unwrap();
            docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?.doc.page_count()
        };
        let mut hits = Vec::new();
        for page in 0..count {
            if cancel.load(Ordering::SeqCst) {
                return Err(AppError::Cancelled);
            }
            if page % 25 == 0 {
                progress(&format!("Mencari di halaman {}", page + 1));
            }
            let found = {
                let docs = self.docs.lock().unwrap();
                docs.get(&id)
                    .ok_or(AppError::DocumentNotOpen(id))?
                    .doc
                    .search_text(page, query, case_sensitive, limit.saturating_sub(hits.len()))?
            };
            hits.extend(found);
            if hits.len() >= limit {
                break;
            }
        }
        Ok(hits)
    }

    /// Runs a conversion on the open document while the document lock is held.
    pub fn convert_open_document(
        &self,
        id: Option<u32>,
        format: crate::convert::ConvertFormat,
        options: &crate::convert::ConvertOptions,
        out_dir: &Path,
        images: &[PathBuf],
        cancel: &AtomicBool,
        progress: &dyn Fn(&str),
    ) -> AppResult<crate::convert::ConvertResult> {
        let docs = self.docs.lock().unwrap();
        let Some(id) = id else {
            return Err(AppError::InvalidInput("buka dokumen terlebih dahulu".into()));
        };
        let e = docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?;
        let pages = e.doc.pages()?;
        let engine = self.engine()?;
        let worker = self.worker();
        crate::convert::convert_document(
            &engine,
            worker.as_ref(),
            e.doc.as_ref(),
            &pages,
            format,
            options,
            out_dir,
            images,
            cancel,
            progress,
        )
    }

    /// Outline (bookmarks) of the open document.
    pub fn document_outline(&self, id: u32) -> AppResult<Vec<crate::engine::OutlineNode>> {
        let docs = self.docs.lock().unwrap();
        docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?.doc.outline()
    }

    pub fn annotation_kinds(&self, id: u32, index: u32) -> AppResult<Vec<String>> {
        let docs = self.docs.lock().unwrap();
        docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?.doc.annotation_kinds(index)
    }

    /// Rotates pages in memory; the change is only persisted with Save As.
    pub fn rotate(&self, id: u32, pages: &[u32], delta: i32) -> AppResult<DocInfo> {
        let mut docs = self.docs.lock().unwrap();
        let e = docs.get_mut(&id).ok_or(AppError::DocumentNotOpen(id))?;
        if e.busy {
            return Err(AppError::Conflict("operasi lain sedang mengubah dokumen ini".into()));
        }
        if pages.is_empty() {
            return Err(AppError::InvalidInput("tidak ada halaman yang dipilih".into()));
        }
        for &p in pages {
            e.doc.rotate(p, delta)?;
        }
        e.dirty = true;
        e.revision += 1;
        Self::info_of(id, e)
    }

    fn snapshot(&self, id: u32, mark_busy: bool) -> AppResult<Snapshot> {
        let mut docs = self.docs.lock().unwrap();
        let e = docs.get_mut(&id).ok_or(AppError::DocumentNotOpen(id))?;
        if mark_busy {
            if e.busy {
                return Err(AppError::Conflict("operasi lain sedang mengubah dokumen ini".into()));
            }
            e.busy = true;
        }
        let result: AppResult<Snapshot> = (|| {
            let input = TempPdf::new("snapshot")?;
            std::fs::write(input.path(), e.doc.save_bytes()?)?;
            Ok(Snapshot { input, revision: e.revision, pages: e.doc.pages()?, path: e.path.clone() })
        })();
        if result.is_err() && mark_busy {
            e.busy = false;
        }
        result
    }

    pub fn save_as(&self, id: u32, dest: &Path, cancel: &AtomicBool, progress: &dyn Fn(&str)) -> AppResult<OpResult> {
        // Hook uji: menunda sebelum lock dokumen (E2E delay). Hook, bukan fitur produksi.
        e2e_delay(cancel)?;
        let engine = self.engine()?;
        // Snapshot singkat di bawah lock; penulisan & verifikasi dilakukan tanpa lock supaya
        // render (dan responsivitas UI) tidak terblokir selama operasi panjang.
        let (expected, source, bytes) = {
            let docs = self.docs.lock().unwrap();
            let e = docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?;
            (e.doc.pages()?, e.path.clone(), e.doc.save_bytes()?)
        };
        progress("Menulis berkas sementara");
        let checks = write_atomic(
            dest,
            &[&source],
            cancel,
            |tmp| {
                std::fs::write(tmp, &bytes)?;
                Ok(())
            },
            |tmp| {
                progress("Memverifikasi output");
                verify_output(engine.as_ref(), tmp, &expected, None)
            },
        )?;
        let mut docs = self.docs.lock().unwrap();
        let e = docs.get_mut(&id).ok_or(AppError::DocumentNotOpen(id))?;
        e.path = dest.to_path_buf();
        e.dirty = false;
        Ok(OpResult {
            output_path: dest.to_string_lossy().to_string(),
            page_count: expected.len() as u32,
            verified: true,
            engine: engine.label().into(),
            checks,
            changes: vec![],
            limitations: vec![],
        })
    }

    // ------------------------------------------------------------------ extract

    pub fn preflight_extract(&self, id: u32, selection: &str, cancel: &AtomicBool, progress: &dyn Fn(&str)) -> AppResult<Preflight> {
        let count = {
            let docs = self.docs.lock().unwrap();
            docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?.doc.page_count()
        };
        let keep = parse_selection(selection, count)?;
        if let Some(worker) = self.worker() {
            let snap = self.snapshot(id, false)?;
            let r = worker.request(
                "extract",
                json!({"input": snap.input.path(), "pages": keep, "dry_run": true}),
                WORKER_TIMEOUT,
                cancel,
                progress,
            )?;
            let (changes, limitations) = extract_report_lines(&r);
            let requires_confirmation = !changes.is_empty() || !limitations.is_empty();
            return Ok(Preflight { engine: "PDFBox".into(), changes, limitations, requires_confirmation });
        }
        let docs = self.docs.lock().unwrap();
        let e = docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?;
        let mut limitations = vec![];
        if e.doc.outline_count() > 0 {
            limitations.push(format!(
                "Engine authoring tidak tersedia: {} bookmark TIDAK dipangkas; bookmark ke halaman yang tidak diekstrak dapat menunjuk halaman yang salah.",
                e.doc.outline_count()
            ));
        }
        if e.doc.has_form() {
            limitations.push("Engine authoring tidak tersedia: field form di halaman yang tidak diekstrak tetap tercatat di form dokumen.".into());
        }
        let requires_confirmation = !limitations.is_empty();
        Ok(Preflight { engine: "PDFium".into(), changes: vec![], limitations, requires_confirmation })
    }

    pub fn extract(&self, id: u32, selection: &str, dest: &Path, cancel: &AtomicBool, progress: &dyn Fn(&str)) -> AppResult<OpResult> {
        e2e_delay(cancel)?;
        let engine = self.engine()?;
        progress("Menyiapkan salinan dokumen");
        let snap = self.snapshot(id, false)?;
        let keep = parse_selection(selection, snap.pages.len() as u32)?;
        let expected: Vec<PageInfo> = keep.iter().map(|&i| snap.pages[i as usize].clone()).collect();
        let output = |checks: Vec<String>, engine_label: String, changes: Vec<String>, limitations: Vec<String>| OpResult {
            output_path: dest.to_string_lossy().to_string(),
            page_count: expected.len() as u32,
            verified: true,
            engine: engine_label,
            checks,
            changes,
            limitations,
        };
        if let Some(worker) = self.worker() {
            let report = std::cell::RefCell::new(Value::Null);
            let checks = write_atomic(
                dest,
                &[&snap.path],
                cancel,
                |tmp| {
                    *report.borrow_mut() = worker.request(
                        "extract",
                        json!({"input": snap.input.path(), "output": tmp, "pages": keep}),
                        WORKER_TIMEOUT,
                        cancel,
                        progress,
                    )?;
                    Ok(())
                },
                |tmp| {
                    progress("Memverifikasi output");
                    let outline = report.borrow()["bookmarks_after"].as_u64().map(|n| n as usize);
                    verify_output(engine.as_ref(), tmp, &expected, outline)
                },
            )?;
            let (changes, limitations) = extract_report_lines(&report.into_inner());
            return Ok(output(checks, "PDFBox 3.0.8 (diverifikasi PDFium)".into(), changes, limitations));
        }
        let mut copy = engine.open_bytes(std::fs::read(snap.input.path())?)?;
        copy.delete_pages_except(&keep)?;
        let checks = write_atomic(
            dest,
            &[&snap.path],
            cancel,
            |tmp| {
                progress("Menulis berkas sementara");
                copy.save_file(tmp)
            },
            |tmp| {
                progress("Memverifikasi output");
                verify_output(engine.as_ref(), tmp, &expected, None)
            },
        )?;
        Ok(output(
            checks,
            engine.label().into(),
            vec![],
            vec!["Diproses PDFium (engine authoring tidak tersedia): bookmark ke halaman yang tidak diekstrak belum dipangkas.".into()],
        ))
    }

    // ------------------------------------------------------------------ merge

    pub fn preflight_merge(&self, id: u32, others: &[PathBuf], cancel: &AtomicBool, progress: &dyn Fn(&str)) -> AppResult<Preflight> {
        let engine = self.engine()?;
        if others.is_empty() {
            return Err(AppError::InvalidInput("pilih setidaknya satu berkas untuk digabung".into()));
        }
        let mut extra = Vec::new();
        for o in others {
            extra.push(engine.open_file(o)?);
        }
        if let Some(worker) = self.worker() {
            let snap = self.snapshot(id, false)?;
            let mut list = vec![snap.input.path().to_string_lossy().to_string()];
            list.extend(others.iter().map(|p| p.to_string_lossy().to_string()));
            let r = worker.request(
                "merge",
                json!({"inputs": list, "dry_run": true}),
                WORKER_TIMEOUT,
                cancel,
                progress,
            )?;
            let (changes, limitations) = merge_report_lines(&r);
            let requires_confirmation = !limitations.is_empty() || r["fields_renamed"].as_object().is_some_and(|m| !m.is_empty());
            return Ok(Preflight { engine: "PDFBox".into(), changes, limitations, requires_confirmation });
        }
        let mut limitations = vec![];
        let outlines: usize = extra.iter().map(|d| d.outline_count()).sum();
        let forms: usize = extra.iter().filter(|d| d.has_form()).count();
        if outlines > 0 {
            limitations.push(format!("{outlines} bookmark dari dokumen lain tidak ikut digabung (engine authoring tidak tersedia)."));
        }
        if forms > 0 {
            limitations.push(format!("{forms} dokumen lain berisi field form yang tidak ikut digabung (engine authoring tidak tersedia)."));
        }
        let requires_confirmation = !limitations.is_empty();
        Ok(Preflight { engine: "PDFium".into(), changes: vec![], limitations, requires_confirmation })
    }

    pub fn merge(&self, id: u32, others: &[PathBuf], dest: &Path, cancel: &AtomicBool, progress: &dyn Fn(&str)) -> AppResult<OpResult> {
        e2e_delay(cancel)?;
        let engine = self.engine()?;
        if others.is_empty() {
            return Err(AppError::InvalidInput("pilih setidaknya satu berkas untuk digabung".into()));
        }
        progress("Membuka dokumen untuk digabung");
        let mut extra_docs = Vec::new();
        for other in others {
            extra_docs.push(engine.open_file(other)?);
        }
        let snap = self.snapshot(id, false)?;
        let mut expected = snap.pages.clone();
        for d in &extra_docs {
            expected.extend(d.pages()?);
        }
        let result = |checks, engine_label: String, changes, limitations| OpResult {
            output_path: dest.to_string_lossy().to_string(),
            page_count: expected.len() as u32,
            verified: true,
            engine: engine_label,
            checks,
            changes,
            limitations,
        };
        if let Some(worker) = self.worker() {
            let report = std::cell::RefCell::new(Value::Null);
            let inputs: Vec<String> = others.iter().map(|p| p.to_string_lossy().to_string()).collect();
            let checks = write_atomic(
                dest,
                &[&snap.path],
                cancel,
                |tmp| {
                    let mut list = vec![snap.input.path().to_string_lossy().to_string()];
                    list.extend(inputs.iter().cloned());
                    *report.borrow_mut() = worker.request(
                        "merge",
                        json!({"inputs": list, "output": tmp}),
                        WORKER_TIMEOUT,
                        cancel,
                        progress,
                    )?;
                    Ok(())
                },
                |tmp| {
                    progress("Memverifikasi output");
                    let outline = report.borrow()["bookmarks_after"].as_u64().map(|n| n as usize);
                    verify_output(engine.as_ref(), tmp, &expected, outline)
                },
            )?;
            let (changes, limitations) = merge_report_lines(&report.into_inner());
            return Ok(result(checks, "PDFBox 3.0.8 (diverifikasi PDFium)".into(), changes, limitations));
        }
        let mut copy = engine.open_bytes(std::fs::read(snap.input.path())?)?;
        progress("Menggabungkan halaman");
        for d in &extra_docs {
            copy.append(d.as_ref())?;
        }
        let checks = write_atomic(
            dest,
            &[&snap.path],
            cancel,
            |tmp| {
                progress("Menulis berkas sementara");
                copy.save_file(tmp)
            },
            |tmp| {
                progress("Memverifikasi output");
                verify_output(engine.as_ref(), tmp, &expected, None)
            },
        )?;
        Ok(result(
            checks,
            engine.label().into(),
            vec![],
            vec!["Diproses PDFium: bookmark dan field form dari dokumen kedua tidak ikut digabung.".into()],
        ))
    }

    // ------------------------------------------------------------------ authoring (PDFBox worker)

    /// Runs a worker operation on a snapshot of the open document and, if the result verifies,
    /// replaces the in-memory document with it (new revision, unsaved).
    fn apply_authoring(&self, id: u32, op: &str, mut params: Value, cancel: &AtomicBool, progress: &dyn Fn(&str)) -> AppResult<(DocInfo, Value)> {
        let worker = self.require_worker()?;
        let engine = self.engine()?;
        progress("Menyiapkan salinan dokumen");
        let snap = self.snapshot(id, true)?;
        let _busy = BusyGuard { ws: self, id };
        let out = TempPdf::new("authoring")?;
        params["input"] = json!(snap.input.path());
        params["output"] = json!(out.path());
        e2e_delay(cancel)?;
        let data = worker.request(op, params, WORKER_TIMEOUT, cancel, progress)?;
        progress("Memverifikasi hasil");
        let bytes = std::fs::read(out.path())?;
        let new_doc = engine
            .open_bytes(bytes)
            .map_err(|e| AppError::VerificationFailed(format!("hasil PDFBox tidak dapat dibuka PDFium: {e}")))?;
        let new_pages = new_doc.pages()?;
        if new_pages.len() != snap.pages.len() {
            return Err(AppError::VerificationFailed(format!(
                "jumlah halaman berubah ({} → {})",
                snap.pages.len(),
                new_pages.len()
            )));
        }
        if cancel.load(Ordering::SeqCst) {
            return Err(AppError::Cancelled);
        }
        let mut docs = self.docs.lock().unwrap();
        let e = docs.get_mut(&id).ok_or(AppError::DocumentNotOpen(id))?;
        if e.revision != snap.revision {
            return Err(AppError::Conflict(format!("revisi {} → {}", snap.revision, e.revision)));
        }
        e.doc = new_doc;
        e.revision += 1;
        e.dirty = true;
        let info = Self::info_of(id, e)?;
        Ok((info, data))
    }

    pub fn form_fields(&self, id: u32, cancel: &AtomicBool, progress: &dyn Fn(&str)) -> AppResult<Value> {
        let worker = self.require_worker()?;
        let snap = self.snapshot(id, false)?;
        let r = worker.request("inspect", json!({"input": snap.input.path()}), WORKER_TIMEOUT, cancel, progress)?;
        Ok(r["fields"].clone())
    }

    pub fn fill_form(&self, id: u32, values: Value, cancel: &AtomicBool, progress: &dyn Fn(&str)) -> AppResult<DocInfo> {
        if !values.as_object().is_some_and(|m| !m.is_empty()) {
            return Err(AppError::InvalidInput("tidak ada nilai field yang diubah".into()));
        }
        self.apply_authoring(id, "fill_form", json!({"values": values}), cancel, progress).map(|(i, _)| i)
    }

    pub fn add_annotation(&self, id: u32, req: &AnnotationRequest, cancel: &AtomicBool, progress: &dyn Fn(&str)) -> AppResult<DocInfo> {
        let (bbox, quads) = {
            let docs = self.docs.lock().unwrap();
            let e = docs.get(&id).ok_or(AppError::DocumentNotOpen(id))?;
            let [x0, y0, x1, y1] = req.rect;
            let mut xs = vec![];
            let mut ys = vec![];
            for (x, y) in [(x0, y0), (x1, y1), (x0, y1), (x1, y0)] {
                let (px, py) = e.doc.display_to_pdf(req.page, x, y)?;
                xs.push(px);
                ys.push(py);
            }
            let f = |v: &[f32], max: bool| v.iter().cloned().fold(if max { f32::MIN } else { f32::MAX }, |a, b| if max { a.max(b) } else { a.min(b) });
            let bbox = [f(&xs, false), f(&ys, false), f(&xs, true), f(&ys, true)];
            let quads = match req.kind.as_str() {
                "highlight" | "underline" | "strikeout" => e.doc.text_boxes(req.page, bbox)?,
                _ => vec![],
            };
            (bbox, quads)
        };
        let mut a = json!({"type": req.kind, "page": req.page, "contents": req.contents});
        if let Some(c) = req.color {
            a["color"] = json!(c);
        }
        match req.kind.as_str() {
            "highlight" | "underline" | "strikeout" => {
                if quads.is_empty() {
                    return Err(AppError::InvalidInput("tidak ada teks di area yang dipilih (sorot/garis bawah/coret hanya untuk teks)".into()));
                }
                a["quads"] = json!(quads);
            }
            "note" => {
                let (x, top) = (bbox[0], bbox[3]);
                a["rect"] = json!([x, top - 22.0, x + 22.0, top]);
                if req.contents.as_deref().map_or(true, |c| c.trim().is_empty()) {
                    return Err(AppError::InvalidInput("isi catatan kosong".into()));
                }
            }
            "freetext" => {
                if bbox[2] - bbox[0] < 10.0 || bbox[3] - bbox[1] < 10.0 {
                    return Err(AppError::InvalidInput("area teks terlalu kecil (min. 10 pt)".into()));
                }
                if req.contents.as_deref().map_or(true, |c| c.trim().is_empty()) {
                    return Err(AppError::InvalidInput("teks kosong".into()));
                }
                a["rect"] = json!(bbox);
            }
            other => return Err(AppError::InvalidInput(format!("jenis anotasi tidak didukung: {other}"))),
        }
        self.apply_authoring(id, "add_annotations", json!({"annotations": [a]}), cancel, progress).map(|(i, _)| i)
    }
}

#[cfg(test)]
mod tests {
    //! Integration tests against the real PDFium library and (when built) the PDFBox worker.
    //! They are skipped with a message when pdfium.dll / the worker jar are not available.
    use super::*;
    use crate::engine::init_pdfium;
    use crate::worker::discover;
    use pdfium_render::prelude::*;
    use std::fs;

    fn engine() -> Option<Arc<dyn PdfEngine>> {
        let mut c = vec![PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("pdfium").join("bin")];
        if let Ok(d) = std::env::var("UNIONPDF_PDFIUM_DIR") {
            c.insert(0, PathBuf::from(d));
        }
        match init_pdfium(&c) {
            Ok((e, _)) => Some(Arc::new(e)),
            Err(msg) => {
                eprintln!("SKIP: {msg}");
                None
            }
        }
    }

    fn worker() -> Option<Arc<PdfboxWorker>> {
        match discover(&[PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("worker")]) {
            Ok(cfg) => Some(Arc::new(PdfboxWorker::new(cfg))),
            Err(msg) => {
                eprintln!("SKIP worker: {msg}");
                None
            }
        }
    }

    fn workspace(with_worker: bool) -> Option<Workspace> {
        let ws = Workspace::default();
        ws.set_engine(engine()?);
        if with_worker {
            ws.set_worker(worker()?);
        }
        Some(ws)
    }

    fn scratch(name: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("unionpdf-ops-test-{}-{name}", std::process::id()));
        let _ = fs::remove_dir_all(&d);
        fs::create_dir_all(&d).unwrap();
        d
    }

    /// Synthetic fixtures copied from experiments/restart/fixtures (see tests/fixtures/README.md).
    fn fixture_file(name: &str, dir: &Path) -> PathBuf {
        let src = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests").join("fixtures").join(name);
        let dst = dir.join(name);
        fs::copy(&src, &dst).unwrap_or_else(|e| panic!("fixture {name}: {e}"));
        dst
    }

    /// Writes a synthetic PDF with pages of distinct sizes (A4, Letter, A5, A4) via PDFium.
    fn fixture(path: &Path) {
        let p = crate::engine::pdfium_instance().expect("PDFium sudah diinisialisasi oleh engine()");
        let mut doc = p.create_new_pdf().unwrap();
        for (w, h) in [(595.0, 842.0), (612.0, 792.0), (420.0, 595.0), (595.0, 842.0)] {
            doc.pages_mut()
                .create_page_at_end(PdfPagePaperSize::from_points(PdfPoints::new(w), PdfPoints::new(h)))
                .unwrap();
        }
        doc.save_to_file(path).unwrap();
    }

    fn sizes(info: &DocInfo) -> Vec<(i32, i32, u16)> {
        info.pages.iter().map(|p| (p.width.round() as i32, p.height.round() as i32, p.rotation)).collect()
    }

    fn inspect(w: &PdfboxWorker, path: &Path) -> Value {
        w.request("inspect", json!({"input": path}), WORKER_TIMEOUT, &AtomicBool::new(false), &|_| {}).unwrap()
    }

    #[test]
    fn open_render_rotate_save_extract_merge_roundtrip_pdfium() {
        let Some(ws) = workspace(false) else { return };
        let d = scratch("roundtrip");
        let src = d.join("sumber dengan spasi.pdf");
        fixture(&src);
        let src_bytes = fs::read(&src).unwrap();
        let never = AtomicBool::new(false);
        let noop = |_: &str| {};

        let info = ws.open(&src).unwrap();
        assert_eq!(info.page_count, 4);
        assert_eq!(sizes(&info)[1], (612, 792, 0));

        let r = ws.render(info.doc_id, 0, 0.5).unwrap();
        assert_eq!((r.width, r.height), (298, 421));
        assert_eq!(r.rgba.len() as u32, r.width * r.height * 4);

        let rotated = ws.rotate(info.doc_id, &[1], 90).unwrap();
        assert!(rotated.dirty);
        assert_eq!(rotated.revision, info.revision + 1);
        assert_eq!(rotated.pages[1].rotation, 90);

        let saved = d.join("hasil simpan.pdf");
        let res = ws.save_as(info.doc_id, &saved, &never, &noop).unwrap();
        assert!(res.verified);
        assert_eq!(fs::read(&src).unwrap(), src_bytes, "input tidak boleh berubah");
        let reopened = ws.open(&saved).unwrap();
        assert_eq!(reopened.pages[1].rotation, 90);

        let ext = d.join("ekstrak.pdf");
        let res = ws.extract(info.doc_id, "2-3", &ext, &never, &noop).unwrap();
        assert_eq!(res.page_count, 2);
        assert!(!res.limitations.is_empty(), "jalur PDFium wajib melaporkan keterbatasan");
        let e = ws.open(&ext).unwrap();
        assert_eq!(e.pages[0].rotation, 90);
        assert_eq!((e.pages[1].width.round() as i32, e.pages[1].height.round() as i32), (420, 595));

        let merged = d.join("gabung.pdf");
        let res = ws.merge(info.doc_id, &[ext.clone()], &merged, &never, &noop).unwrap();
        assert_eq!(res.page_count, 6);
        assert_eq!(ws.open(&merged).unwrap().page_count, 6);
    }

    #[test]
    fn errors_are_specific() {
        let Some(ws) = workspace(false) else { return };
        let d = scratch("errors");
        assert!(matches!(ws.open(&d.join("tidak-ada.pdf")), Err(AppError::FileNotFound(_))));
        let junk = d.join("bukan.pdf");
        fs::write(&junk, b"ini bukan PDF").unwrap();
        assert!(matches!(ws.open(&junk), Err(AppError::Corrupt(_))));
        let src = d.join("a.pdf");
        fixture(&src);
        let info = ws.open(&src).unwrap();
        let never = AtomicBool::new(false);
        assert!(matches!(ws.save_as(info.doc_id, &src, &never, &|_| {}), Err(AppError::WouldOverwriteInput(_))));
        assert!(matches!(ws.extract(info.doc_id, "9", &d.join("x.pdf"), &never, &|_| {}), Err(AppError::InvalidInput(_))));
        assert!(matches!(ws.render(info.doc_id, 99, 1.0), Err(AppError::InvalidInput(_))));
        assert!(matches!(ws.render(info.doc_id, 0, 50.0), Err(AppError::InvalidInput(_))));
        let cancelled = AtomicBool::new(true);
        assert_eq!(ws.save_as(info.doc_id, &d.join("batal.pdf"), &cancelled, &|_| {}).unwrap_err(), AppError::Cancelled);
        assert!(!d.join("batal.pdf").exists());
    }

    #[cfg(windows)]
    #[test]
    fn save_as_onto_locked_file_fails_and_keeps_it() {
        use std::os::windows::fs::OpenOptionsExt;
        let Some(ws) = workspace(false) else { return };
        let d = scratch("locked");
        let src = d.join("a.pdf");
        fixture(&src);
        let dest = d.join("terkunci.pdf");
        fs::write(&dest, b"ISI LAMA").unwrap();
        let lock = fs::OpenOptions::new().read(true).share_mode(0).open(&dest).unwrap();
        let info = ws.open(&src).unwrap();
        let r = ws.save_as(info.doc_id, &dest, &AtomicBool::new(false), &|_| {});
        assert!(matches!(r, Err(AppError::Io(_))), "{r:?}");
        drop(lock);
        assert_eq!(fs::read(&dest).unwrap(), b"ISI LAMA");
        let temps = fs::read_dir(&d).unwrap().filter(|e| e.as_ref().unwrap().file_name().to_string_lossy().ends_with(".tmp")).count();
        assert_eq!(temps, 0, "file sementara harus dibersihkan");
        // Document state unchanged: still points at the source, Save As to a free name works.
        assert!(ws.save_as(info.doc_id, &d.join("bebas.pdf"), &AtomicBool::new(false), &|_| {}).is_ok());
    }

    #[cfg(windows)]
    #[test]
    fn save_as_replaces_existing_file_atomically() {
        let Some(ws) = workspace(false) else { return };
        let d = scratch("replace");
        let src = d.join("a.pdf");
        fixture(&src);
        let dest = d.join("sudah-ada.pdf");
        fs::write(&dest, b"BUKAN PDF LAMA").unwrap();
        let info = ws.open(&src).unwrap();
        let res = ws.save_as(info.doc_id, &dest, &AtomicBool::new(false), &|_| {}).unwrap();
        assert!(res.verified);
        let head = fs::read(&dest).unwrap();
        assert!(head.starts_with(b"%PDF"), "berkas lama tidak tergantikan: {:?}", &head[..8.min(head.len())]);
        let temps = fs::read_dir(&d).unwrap().filter(|e| e.as_ref().unwrap().file_name().to_string_lossy().ends_with(".tmp")).count();
        assert_eq!(temps, 0, "file sementara harus dibersihkan");
    }

    #[test]
    fn search_finds_matches_in_the_whole_document() {
        let Some(ws) = workspace(false) else { return };
        let d = scratch("search");
        let src = fixture_file("rs05_structure.pdf", &d);
        let info = ws.open(&src).unwrap();
        let never = AtomicBool::new(false);
        let noop = |_: &str| {};

        let hits = ws.search_document(info.doc_id, "page 2", false, 100, &never, &noop).unwrap();
        assert!(!hits.is_empty(), "pencarian harus menemukan 'page 2'");
        assert_eq!(hits[0].page, 1, "match harus di halaman 2 (indeks 1)");
        assert!(hits[0].width > 0.0 && hits[0].height > 0.0, "kotak match tidak valid: {hits:?}");

        // Case-sensitive: huruf besar tidak boleh cocok.
        let none = ws.search_document(info.doc_id, "PAGE 2", true, 100, &never, &noop).unwrap();
        assert!(none.is_empty(), "pencarian case-sensitive tidak boleh cocok: {none:?}");
        // Case-insensitive: harus cocok.
        let some = ws.search_document(info.doc_id, "PAGE 2", false, 100, &never, &noop).unwrap();
        assert_eq!(some.len(), hits.len());

        // Halaman yang belum dirender ikut tercari (dokumen 500 halaman).
        let big = d.join("besar.pdf");
        fs::copy(
            PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("tests")
                .join("fixtures")
                .join("rs01_large_500p.pdf"),
            &big,
        )
        .unwrap();
        let big_info = ws.open(&big).unwrap();
        let big_hits = ws.search_document(big_info.doc_id, "page 250", false, 100, &never, &noop).unwrap();
        assert_eq!(big_hits.len(), 1, "halaman yang belum dirender harus ikut tercari: {big_hits:?}");
        assert_eq!(big_hits[0].page, 249);
    }

    #[test]
    fn document_outline_is_readable() {
        let Some(ws) = workspace(false) else { return };
        let d = scratch("outline");
        let src = fixture_file("rs05_structure.pdf", &d);
        let info = ws.open(&src).unwrap();
        let outline = ws.document_outline(info.doc_id).unwrap();
        assert!(!outline.is_empty(), "bookmark PDF harus terbaca: {outline:?}");
        let titles: Vec<&str> = outline.iter().map(|n| n.title.as_str()).collect();
        assert!(titles.contains(&"Bab 1"), "judul bookmark: {titles:?}");
        let bab1 = outline.iter().find(|n| n.title == "Bab 1").unwrap();
        assert_eq!(bab1.page, Some(0), "Bab 1 harus menunjuk halaman 1");
        // Hierarki: "Sub 3.1 ke hal 4" adalah anak dari "Bab 3".
        let bab3 = outline.iter().find(|n| n.title == "Bab 3").expect("Bab 3");
        assert!(!bab3.children.is_empty(), "Bab 3 harus punya anak");
        assert_eq!(bab3.children[0].title, "Sub 3.1 ke hal 4");
        assert_eq!(bab3.children[0].page, Some(3));
    }

    #[test]
    fn convert_to_png_and_txt_produces_valid_files() {
        let Some(ws) = workspace(false) else { return };
        let d = scratch("convert");
        let src = fixture_file("rs05_structure.pdf", &d);
        let info = ws.open(&src).unwrap();
        let out = d.join("keluaran");
        let never = AtomicBool::new(false);
        let noop = |_: &str| {};

        let opts = crate::convert::ConvertOptions { range: "1-2".into(), dpi: 96, quality: 80, base_name: "uji".into() };
        let res = ws
            .convert_open_document(
                Some(info.doc_id),
                crate::convert::ConvertFormat::Png,
                &opts,
                &out,
                &[],
                &never,
                &noop,
            )
            .unwrap();
        assert_eq!(res.files.len(), 2, "dua PNG harus dibuat: {res:?}");
        for f in &res.files {
            assert!(f.ends_with(".png"), "ekstensi: {f}");
            let bytes = fs::read(f).unwrap();
            assert!(bytes.len() > 1000, "PNG terlalu kecil: {}", bytes.len());
            assert_eq!(&bytes[1..4], b"PNG", "bukan PNG: {f}");
        }
        // Teks: isi dokumen harus terbaca.
        let opts_txt = crate::convert::ConvertOptions { range: "1".into(), ..opts.clone() };
        let res_txt = ws
            .convert_open_document(
                Some(info.doc_id),
                crate::convert::ConvertFormat::Txt,
                &opts_txt,
                &out,
                &[],
                &never,
                &noop,
            )
            .unwrap();
        assert_eq!(res_txt.files.len(), 1);
        let text = fs::read_to_string(&res_txt.files[0]).unwrap();
        assert!(text.contains("RS05 structure page 1"), "teks hasil konversi: {text}");
    }

    // ---------------------------------------------------------------- PDFBox worker

    #[test]
    fn text_spans_are_in_displayed_page_space() {
        let Some(ws) = workspace(false) else { return };
        let d = scratch("spans");
        let src = fixture_file("rs05_structure.pdf", &d);
        let info = ws.open(&src).unwrap();
        let spans = ws.text_spans(info.doc_id, 0).unwrap();
        assert!(!spans.is_empty(), "halaman harus punya text span");
        let joined: String = spans.iter().map(|s| s.text.as_str()).collect::<Vec<_>>().join(" ");
        assert!(joined.contains("RS05"), "teks halaman tidak terbaca: {joined}");
        // Display space: origin top-left, semua span di dalam area halaman (595x842 pt).
        for s in &spans {
            assert!(s.left >= -1.0 && s.top >= -1.0, "span di luar area: {s:?}");
            assert!(s.left + s.width <= 596.0, "span melewati lebar halaman: {s:?}");
            assert!(s.height > 0.0 && s.width > 0.0, "span tidak berukuran: {s:?}");
        }
        // Span pertama (judul) berada di paruh atas halaman.
        let first = &spans[0];
        assert!(first.top < 300.0, "span pertama seharusnya di atas: {first:?}");
    }

    #[test]
    fn annotation_on_second_page_lands_on_that_page() {
        let Some(ws) = workspace(true) else { return };
        let w = ws.worker().unwrap();
        let d = scratch("annotpage");
        let src = fixture_file("rs05_structure.pdf", &d);
        let info = ws.open(&src).unwrap();
        let never = AtomicBool::new(false);
        // Anotasi pada halaman indeks 1 (halaman 2), kotak di area teks.
        let req = AnnotationRequest {
            page: 1,
            kind: "note".into(),
            rect: [300.0, 300.0, 300.0, 300.0],
            contents: Some("Halaman dua".into()),
            color: None,
        };
        ws.add_annotation(info.doc_id, &req, &never, &|_| {}).unwrap();
        let out = d.join("annotasi.pdf");
        ws.save_as(info.doc_id, &out, &never, &|_| {}).unwrap();
        let r = inspect(&w, &out);
        let anns = r["annotations"].as_array().expect("inspect harus melaporkan anotasi");
        // Anotasi kita dibedakan dari isi fixture (catatan bawaan + widget form).
        let mine: Vec<&Value> = anns.iter().filter(|a| a["contents"] == "Halaman dua").collect();
        assert_eq!(mine.len(), 1, "anotasi baru harus ada tepat satu: {anns:?}");
        assert_eq!(mine[0]["page"].as_i64().unwrap(), 1, "anotasi harus di halaman 2 (indeks 1)");
        // Rect anotasi (user space): atas = 842 - 300 = 542, bawah = 542 - 22 (tinggi ikon 22 pt).
        let bbox: Vec<f64> = mine[0]["bbox"].as_array().unwrap().iter().map(|v| v.as_f64().unwrap()).collect();
        assert!((bbox[3] - 542.0).abs() < 2.0, "tepi atas kotak anotasi: {bbox:?}");
        assert!(bbox[1] > 510.0 && bbox[1] < 530.0, "tepi bawah kotak anotasi: {bbox:?}");
        assert!((bbox[0] - 300.0).abs() < 2.0, "lebar kotak anotasi: {bbox:?}");
        // Tidak boleh ada anotasi kita di halaman lain.
        let other_pages: Vec<i64> = anns.iter().filter(|a| a["contents"] == "Halaman dua").map(|a| a["page"].as_i64().unwrap()).collect();
        assert_eq!(other_pages, vec![1]);
    }

    #[test]
    fn worker_extract_prunes_bookmarks_links_and_fields() {
        let Some(ws) = workspace(true) else { return };
        let w = ws.worker().unwrap();
        let d = scratch("wextract");
        let src = fixture_file("rs05_structure.pdf", &d);
        let info = ws.open(&src).unwrap();
        assert_eq!(info.outline_count, 4);
        let never = AtomicBool::new(false);

        // Keep pages 2-4: bookmarks to p1 and p6 must go; "Bab 3" and "Sub 3.1" stay.
        let pre = ws.preflight_extract(info.doc_id, "2-4", &never, &|_| {}).unwrap();
        assert_eq!(pre.engine, "PDFBox");
        assert!(pre.requires_confirmation);
        assert!(pre.changes.iter().any(|c| c.contains("Bab 1") && c.contains("Bab 6")), "{:?}", pre.changes);
        let out = d.join("p2-4.pdf");
        let res = ws.extract(info.doc_id, "2-4", &out, &never, &|_| {}).unwrap();
        assert_eq!(res.changes, pre.changes, "preflight dan eksekusi harus konsisten");
        let r = inspect(&w, &out);
        let titles: Vec<(String, i64)> = r["outline"].as_array().unwrap().iter()
            .map(|o| (o["title"].as_str().unwrap().to_string(), o["page"].as_i64().unwrap_or(-1))).collect();
        assert_eq!(titles, vec![("Bab 3".to_string(), 1), ("Sub 3.1 ke hal 4".to_string(), 2)]);
        assert_eq!(r["fields"][0]["name"], "rs05_field");
        assert_eq!(ws.open(&out).unwrap().outline_count, 2, "PDFium harus membaca 2 bookmark");

        // Keep 1,5-6: link p1->p4 removed, field on p3 removed, Bab 3 (+child) removed.
        let out2 = d.join("p1-5-6.pdf");
        let res = ws.extract(info.doc_id, "1,5-6", &out2, &never, &|_| {}).unwrap();
        assert!(res.changes.iter().any(|c| c.contains("1 link")), "{:?}", res.changes);
        assert!(res.changes.iter().any(|c| c.contains("rs05_field")), "{:?}", res.changes);
        let r = inspect(&w, &out2);
        assert_eq!(r["links"].as_array().unwrap().len(), 0);
        assert_eq!(r["fields"].as_array().unwrap().len(), 0);
        let titles: Vec<&str> = r["outline"].as_array().unwrap().iter().map(|o| o["title"].as_str().unwrap()).collect();
        assert_eq!(titles, vec!["Bab 1", "Bab 6"]);
        let pages: Vec<i64> = r["outline"].as_array().unwrap().iter().map(|o| o["page"].as_i64().unwrap()).collect();
        assert_eq!(pages, vec![0, 2]);
    }

    #[test]
    fn worker_merge_keeps_both_forms_and_renames_conflicts() {
        let Some(ws) = workspace(true) else { return };
        let w = ws.worker().unwrap();
        let d = scratch("wmerge");
        let a = fixture_file("rs03_form.pdf", &d);
        let b = d.join("kedua.pdf");
        fs::copy(&a, &b).unwrap();
        let info = ws.open(&a).unwrap();
        let never = AtomicBool::new(false);
        let pre = ws.preflight_merge(info.doc_id, &[b.clone()], &never, &|_| {}).unwrap();
        assert!(pre.requires_confirmation);
        assert!(pre.changes.iter().any(|c| c.contains("nama → nama_2")), "{:?}", pre.changes);
        let out = d.join("gabung.pdf");
        let res = ws.merge(info.doc_id, &[b.clone()], &out, &never, &|_| {}).unwrap();
        assert_eq!(res.page_count, 2);
        let r = inspect(&w, &out);
        let mut names: Vec<String> = r["fields"].as_array().unwrap().iter().map(|f| f["name"].as_str().unwrap().to_string()).collect();
        names.sort();
        assert_eq!(names, vec!["kota", "kota_2", "nama", "nama_2", "pilihan", "pilihan_2", "setuju", "setuju_2"]);
        let pages_of_nama2 = r["fields"].as_array().unwrap().iter().find(|f| f["name"] == "nama_2").unwrap()["pages"].clone();
        assert_eq!(pages_of_nama2, json!([1]));
    }

    #[test]
    fn worker_fill_form_updates_revision_and_persists() {
        let Some(ws) = workspace(true) else { return };
        let w = ws.worker().unwrap();
        let d = scratch("wfill");
        let src = fixture_file("rs03_form.pdf", &d);
        let info = ws.open(&src).unwrap();
        assert!(info.has_form);
        let never = AtomicBool::new(false);
        let fields = ws.form_fields(info.doc_id, &never, &|_| {}).unwrap();
        let radio = fields.as_array().unwrap().iter().find(|f| f["name"] == "pilihan").unwrap();
        assert_eq!(radio["type"], "radio");
        let after = ws
            .fill_form(info.doc_id, json!({"nama": "Budi Santoso", "setuju": true, "pilihan": "B", "kota": "Surabaya"}), &never, &|_| {})
            .unwrap();
        assert_eq!(after.revision, info.revision + 1);
        assert!(after.dirty);
        // A wrong value fails as a whole and leaves the document untouched.
        let bad = ws.fill_form(info.doc_id, json!({"nama": "x", "pilihan": "Z"}), &never, &|_| {});
        assert!(matches!(bad, Err(AppError::Worker { .. })), "{bad:?}");
        assert_eq!(ws.form_fields(info.doc_id, &never, &|_| {}).unwrap().as_array().unwrap().iter()
            .find(|f| f["name"] == "nama").unwrap()["value"], "Budi Santoso");
        let out = d.join("terisi.pdf");
        ws.save_as(info.doc_id, &out, &never, &|_| {}).unwrap();
        let r = inspect(&w, &out);
        let val = |n: &str| r["fields"].as_array().unwrap().iter().find(|f| f["name"] == n).unwrap()["value"].clone();
        assert_eq!(val("nama"), "Budi Santoso");
        assert_eq!(val("setuju"), "Yes");
        assert_eq!(val("pilihan"), "B");
        assert_eq!(val("kota"), "Surabaya");
        // Appearances were regenerated: PDFium renders the filled form differently from the original.
        let filled = ws.open(&out).unwrap();
        let orig = ws.open(&src).unwrap();
        let a = ws.render(filled.doc_id, 0, 1.0).unwrap();
        let b = ws.render(orig.doc_id, 0, 1.0).unwrap();
        let diff = a.rgba.iter().zip(&b.rgba).filter(|(x, y)| x != y).count();
        assert!(diff > 500, "nilai form harus terlihat di render PDFium (beda {diff} byte)");
    }

    #[test]
    fn worker_annotations_have_appearance_and_survive_save() {
        let Some(ws) = workspace(true) else { return };
        let d = scratch("wannot");
        let src = fixture_file("rs05_structure.pdf", &d);
        let info = ws.open(&src).unwrap();
        let never = AtomicBool::new(false);
        let req = |kind: &str, rect: [f32; 4], contents: Option<&str>| AnnotationRequest {
            page: 0,
            kind: kind.into(),
            rect,
            contents: contents.map(String::from),
            color: None,
        };
        // Empty area: highlight must be refused instead of drawing over nothing.
        let empty = ws.add_annotation(info.doc_id, &req("highlight", [300.0, 600.0, 500.0, 700.0], None), &never, &|_| {});
        assert!(matches!(empty, Err(AppError::InvalidInput(_))), "{empty:?}");
        let top = [30.0, 30.0, 560.0, 200.0];
        ws.add_annotation(info.doc_id, &req("highlight", top, None), &never, &|_| {}).unwrap();
        ws.add_annotation(info.doc_id, &req("underline", top, None), &never, &|_| {}).unwrap();
        ws.add_annotation(info.doc_id, &req("note", [400.0, 300.0, 400.0, 300.0], Some("Catatan uji")), &never, &|_| {}).unwrap();
        let last = ws.add_annotation(info.doc_id, &req("freetext", [60.0, 400.0, 300.0, 440.0], Some("Teks bebas uji")), &never, &|_| {}).unwrap();
        assert_eq!(last.revision, info.revision + 4);
        // Regression (stroke_color crash): enumerating PDFBox annotations with /AP must not crash.
        let kinds = ws.annotation_kinds(info.doc_id, 0).unwrap();
        for k in ["Highlight", "Underline", "Text", "FreeText"] {
            assert!(kinds.iter().any(|x| x == k), "{k} tidak ada di {kinds:?}");
        }
        let out = d.join("anotasi.pdf");
        ws.save_as(info.doc_id, &out, &never, &|_| {}).unwrap();
        let re = ws.open(&out).unwrap();
        let kinds = ws.annotation_kinds(re.doc_id, 0).unwrap();
        assert!(kinds.iter().filter(|k| ["Highlight", "Underline", "Text", "FreeText"].contains(&k.as_str())).count() >= 4, "{kinds:?}");
        // Annotations are visible: the highlighted band differs from the original rendering.
        let before = ws.open(&src).unwrap();
        let a = ws.render(re.doc_id, 0, 1.0).unwrap();
        let b = ws.render(before.doc_id, 0, 1.0).unwrap();
        let diff = a.rgba.iter().zip(&b.rgba).filter(|(x, y)| x != y).count();
        assert!(diff > 1000, "anotasi harus terlihat di render (beda {diff} byte)");
    }

    /// Known pdfium-render 0.9.4 + PDFium 7881 defect: `stroke_color()` on an annotation with /AP
    /// crashes the process. The app never calls it; this canary (run in a child process) fails
    /// once the defect is fixed so the workaround can be revisited.
    #[test]
    fn stroke_color_crash_canary() {
        if let Ok(path) = std::env::var("UNIONPDF_STROKE_CANARY") {
            let Some(_) = engine() else { return };
            let p = crate::engine::pdfium_instance().unwrap();
            let doc = p.load_pdf_from_file(&path, None).unwrap();
            for a in doc.pages().get(0).unwrap().annotations().iter() {
                let _ = a.stroke_color();
            }
            return;
        }
        let Some(ws) = workspace(true) else { return };
        let d = scratch("canary");
        let src = fixture_file("rs05_structure.pdf", &d);
        let info = ws.open(&src).unwrap();
        let never = AtomicBool::new(false);
        let req = AnnotationRequest { page: 0, kind: "note".into(), rect: [100.0, 300.0, 100.0, 300.0], contents: Some("x".into()), color: None };
        ws.add_annotation(info.doc_id, &req, &never, &|_| {}).unwrap();
        let out = d.join("note.pdf");
        ws.save_as(info.doc_id, &out, &never, &|_| {}).unwrap();
        let status = std::process::Command::new(std::env::current_exe().unwrap())
            .args(["ops::tests::stroke_color_crash_canary", "--exact", "--test-threads=1", "--nocapture"])
            .env("UNIONPDF_STROKE_CANARY", &out)
            .output()
            .unwrap()
            .status;
        assert!(!status.success(), "stroke_color() tidak lagi crash (status {status:?}); tinjau ulang workaround");
    }

    #[test]
    fn worker_cancel_timeout_and_crash_recovery() {
        let Some(w) = worker() else { return };
        let ping = |cancel: &AtomicBool, timeout: Duration| w.request("ping", json!({}), timeout, cancel, &|_| {});
        let never = AtomicBool::new(false);
        assert_eq!(ping(&never, WORKER_TIMEOUT).unwrap()["pdfbox"], "3.0.8");
        // Cancellation requested while the request is in flight kills the worker.
        let fx = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests").join("fixtures").join("rs05_structure.pdf");
        let cancel = AtomicBool::new(false);
        let before = w.process_id();
        let r = w.request("extract", json!({"input": fx, "pages": [0], "dry_run": true}), WORKER_TIMEOUT, &cancel, &|_| {
            cancel.store(true, Ordering::SeqCst)
        });
        assert!(matches!(r, Err(AppError::Cancelled)), "{r:?}");
        assert_eq!(w.process_id(), None, "proses worker harus dihentikan saat dibatalkan");
        assert!(before.is_some());
        assert!(ping(&never, WORKER_TIMEOUT).is_ok(), "worker harus pulih setelah dibatalkan");
        // Timeout kills the process; the next request starts a new one.
        assert!(matches!(ping(&never, Duration::ZERO), Err(AppError::WorkerFailed(_))));
        assert!(ping(&never, WORKER_TIMEOUT).is_ok());
        // External crash: next request reports a structured failure, the one after recovers.
        let pid = w.process_id().expect("worker berjalan");
        std::process::Command::new("taskkill").args(["/PID", &pid.to_string(), "/F"]).output().unwrap();
        std::thread::sleep(Duration::from_millis(300));
        assert!(matches!(ping(&never, WORKER_TIMEOUT), Err(AppError::WorkerFailed(_))));
        assert!(ping(&never, WORKER_TIMEOUT).is_ok());
        // Structured error for a missing file.
        let e = w.request("inspect", json!({"input": "tidak-ada.pdf"}), WORKER_TIMEOUT, &never, &|_| {});
        assert!(matches!(&e, Err(AppError::Worker { code, .. }) if code == "file_not_found"), "{e:?}");
    }

    #[test]
    fn concurrent_mutation_is_rejected() {
        let Some(ws) = workspace(false) else { return };
        let d = scratch("busy");
        let src = d.join("a.pdf");
        fixture(&src);
        let info = ws.open(&src).unwrap();
        let snap = ws.snapshot(info.doc_id, true).unwrap();
        assert!(matches!(ws.rotate(info.doc_id, &[0], 90), Err(AppError::Conflict(_))));
        {
            let _g = BusyGuard { ws: &ws, id: info.doc_id };
        }
        drop(snap);
        assert!(ws.rotate(info.doc_id, &[0], 90).is_ok());
    }
}
