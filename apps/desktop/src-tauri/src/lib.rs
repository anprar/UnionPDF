mod atomic;
mod convert;
mod engine;
mod error;
mod jobs;
mod ops;
mod pages;
mod worker;

use error::{AppError, AppResult, ErrorPayload};
use jobs::JobRegistry;
use ops::{AnnotationRequest, DocInfo, OpResult, Preflight, Workspace};
use serde::Serialize;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter, Manager, State};

#[derive(Default)]
pub struct AppState {
    workspace: Workspace,
    jobs: JobRegistry,
    engine_status: Mutex<EngineStatus>,
    /// Last viewport report from the UI (used by automated UI tests and diagnostics).
    view_state: Mutex<Option<serde_json::Value>>,
}

#[derive(Debug, Clone, Default, Serialize)]
pub struct EngineStatus {
    pub available: bool,
    pub engine: Option<String>,
    pub library_path: Option<String>,
    pub error: Option<String>,
    /// PDFBox authoring worker: configured (java + jar found). Started lazily on first use.
    pub authoring_available: bool,
    pub authoring_java: Option<String>,
    pub authoring_error: Option<String>,
}

#[derive(Clone, Serialize)]
struct JobProgress {
    job_id: String,
    stage: String,
}

/// Runs blocking engine work off the UI/IPC thread.
async fn blocking<T: Send + 'static>(
    app: AppHandle,
    f: impl FnOnce(&AppState) -> AppResult<T> + Send + 'static,
) -> Result<T, ErrorPayload> {
    tauri::async_runtime::spawn_blocking(move || {
        let state = app.state::<AppState>();
        f(&state)
    })
    .await
    .map_err(|e| ErrorPayload::from(AppError::Internal(e.to_string())))?
    .map_err(ErrorPayload::from)
}

/// Runs a cancellable job and reports progress through the `job-progress` event.
async fn job<T: Send + 'static>(
    app: AppHandle,
    job_id: String,
    f: impl FnOnce(&AppState, &std::sync::atomic::AtomicBool, &dyn Fn(&str)) -> AppResult<T> + Send + 'static,
) -> Result<T, ErrorPayload> {
    let emitter = app.clone();
    blocking(app, move |st| {
        let cancel = st.jobs.register(&job_id);
        let report = |stage: &str| {
            let _ = emitter.emit("job-progress", JobProgress { job_id: job_id.clone(), stage: stage.to_string() });
        };
        let result = f(st, &cancel, &report);
        st.jobs.finish(&job_id);
        result
    })
    .await
}

#[tauri::command]
fn engine_status(state: State<'_, AppState>) -> EngineStatus {
    state.engine_status.lock().unwrap().clone()
}

#[tauri::command]
async fn open_document(app: AppHandle, path: String) -> Result<DocInfo, ErrorPayload> {
    blocking(app, move |st| st.workspace.open(&PathBuf::from(path))).await
}

#[tauri::command]
fn close_document(state: State<'_, AppState>, doc_id: u32) -> Result<(), ErrorPayload> {
    state.workspace.close(doc_id).map_err(ErrorPayload::from)
}

/// Returns raw RGBA pixels prefixed by an 8-byte header: width (u32 LE), height (u32 LE).
#[tauri::command]
async fn render_page(app: AppHandle, doc_id: u32, page_index: u32, scale: f32) -> Result<tauri::ipc::Response, ErrorPayload> {
    let page = blocking(app, move |st| st.workspace.render(doc_id, page_index, scale)).await?;
    let mut buf = Vec::with_capacity(8 + page.rgba.len());
    buf.extend_from_slice(&page.width.to_le_bytes());
    buf.extend_from_slice(&page.height.to_le_bytes());
    buf.extend_from_slice(&page.rgba);
    Ok(tauri::ipc::Response::new(buf))
}

#[tauri::command]
async fn rotate_pages(app: AppHandle, doc_id: u32, pages: Vec<u32>, delta: i32) -> Result<DocInfo, ErrorPayload> {
    blocking(app, move |st| st.workspace.rotate(doc_id, &pages, delta)).await
}

#[tauri::command]
async fn save_as(app: AppHandle, doc_id: u32, dest: String, job_id: String) -> Result<OpResult, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| st.workspace.save_as(doc_id, &PathBuf::from(dest), cancel, progress)).await
}

#[tauri::command]
async fn extract_pages(app: AppHandle, doc_id: u32, selection: String, dest: String, job_id: String) -> Result<OpResult, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| {
        st.workspace.extract(doc_id, &selection, &PathBuf::from(dest), cancel, progress)
    })
    .await
}

#[tauri::command]
async fn merge_documents(
    app: AppHandle,
    doc_id: u32,
    others: Vec<String>,
    dest: String,
    job_id: String,
) -> Result<OpResult, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| {
        let list: Vec<PathBuf> = others.iter().map(PathBuf::from).collect();
        st.workspace.merge(doc_id, &list, &PathBuf::from(dest), cancel, progress)
    })
    .await
}

/// PDF path passed on the command line (e.g. "Open with UnionPDF"), if it exists.
#[tauri::command]
fn startup_file() -> Option<String> {
    std::env::args_os()
        .skip(1)
        .map(PathBuf::from)
        .find(|p| p.is_file() && p.extension().is_some_and(|e| e.eq_ignore_ascii_case("pdf")))
        .map(|p| p.to_string_lossy().to_string())
}

#[tauri::command]
async fn preflight_extract(app: AppHandle, doc_id: u32, selection: String, job_id: String) -> Result<Preflight, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| st.workspace.preflight_extract(doc_id, &selection, cancel, progress)).await
}

#[tauri::command]
async fn preflight_merge(app: AppHandle, doc_id: u32, others: Vec<String>, job_id: String) -> Result<Preflight, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| {
        let list: Vec<PathBuf> = others.iter().map(PathBuf::from).collect();
        st.workspace.preflight_merge(doc_id, &list, cancel, progress)
    })
    .await
}

#[tauri::command]
async fn form_fields(app: AppHandle, doc_id: u32, job_id: String) -> Result<serde_json::Value, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| st.workspace.form_fields(doc_id, cancel, progress)).await
}

#[tauri::command]
async fn fill_form(app: AppHandle, doc_id: u32, values: serde_json::Value, job_id: String) -> Result<DocInfo, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| st.workspace.fill_form(doc_id, values, cancel, progress)).await
}

#[tauri::command]
async fn add_annotation(app: AppHandle, doc_id: u32, request: AnnotationRequest, job_id: String) -> Result<DocInfo, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| st.workspace.add_annotation(doc_id, &request, cancel, progress)).await
}

#[tauri::command]
async fn annotation_kinds(app: AppHandle, doc_id: u32, page_index: u32) -> Result<Vec<String>, ErrorPayload> {
    blocking(app, move |st| st.workspace.annotation_kinds(doc_id, page_index)).await
}

/// Converts the open document (or image files) into another format.
#[tauri::command]
async fn convert_document(
    app: AppHandle,
    doc_id: Option<u32>,
    format: convert::ConvertFormat,
    options: Option<convert::ConvertOptions>,
    out_dir: String,
    images: Option<Vec<String>>,
    job_id: String,
) -> Result<convert::ConvertResult, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| {
        let opts = options.unwrap_or_default();
        let out = PathBuf::from(out_dir);
        let image_paths: Vec<PathBuf> = images.unwrap_or_default().iter().map(PathBuf::from).collect();
        st.workspace.convert_open_document(doc_id, format, &opts, &out, &image_paths, cancel, progress)
    })
    .await
}

/// Outline (bookmarks) of the open document.
#[tauri::command]
async fn document_outline(app: AppHandle, doc_id: u32) -> Result<Vec<engine::OutlineNode>, ErrorPayload> {
    blocking(app, move |st| st.workspace.document_outline(doc_id)).await
}

/// Searches the whole document for `query`; returns match boxes in displayed page space.
#[tauri::command]
async fn search_document(
    app: AppHandle,
    doc_id: u32,
    query: String,
    case_sensitive: Option<bool>,
    limit: Option<usize>,
    job_id: String,
) -> Result<Vec<engine::SearchHit>, ErrorPayload> {
    job(app, job_id, move |st, cancel, progress| {
        st.workspace.search_document(
            doc_id,
            &query,
            case_sensitive.unwrap_or(false),
            limit.unwrap_or(2000),
            cancel,
            progress,
        )
    })
    .await
}

/// Text runs of a page in displayed page space (used by the selectable text layer).
#[tauri::command]
async fn text_spans(app: AppHandle, doc_id: u32, page_index: u32) -> Result<Vec<engine::TextSpan>, ErrorPayload> {
    blocking(app, move |st| st.workspace.text_spans(doc_id, page_index)).await
}

/// Viewport report from the UI (scroll metrics, rendered pages).
#[tauri::command]
fn report_view_state(state: State<'_, AppState>, metrics: serde_json::Value) {
    *state.view_state.lock().unwrap() = Some(metrics);
}

#[tauri::command]
fn view_state(state: State<'_, AppState>) -> Option<serde_json::Value> {
    state.view_state.lock().unwrap().clone()
}

#[tauri::command]
fn cancel_job(state: State<'_, AppState>, job_id: String) -> bool {
    state.jobs.cancel(&job_id)
}

/// Locations searched for the PDFBox worker (`unionpdf-worker.jar`), in order.
fn worker_candidates(app: &tauri::App) -> Vec<PathBuf> {
    let mut c = Vec::new();
    if let Ok(d) = std::env::var("UNIONPDF_WORKER_DIR") {
        c.push(PathBuf::from(d));
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            c.push(dir.join("worker"));
        }
    }
    if let Ok(res) = app.path().resource_dir() {
        c.push(res.join("worker"));
    }
    #[cfg(debug_assertions)]
    c.push(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("worker"));
    c
}

/// Locations searched for pdfium.dll, in order.
fn pdfium_candidates(app: &tauri::App) -> Vec<PathBuf> {
    let mut c = Vec::new();
    if let Ok(d) = std::env::var("UNIONPDF_PDFIUM_DIR") {
        c.push(PathBuf::from(d));
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            c.push(dir.to_path_buf());
        }
    }
    if let Ok(res) = app.path().resource_dir() {
        c.push(res.join("pdfium"));
    }
    #[cfg(debug_assertions)]
    c.push(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("pdfium").join("bin"));
    c
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(AppState::default())
        .setup(|app| {
            let candidates = pdfium_candidates(app);
            let state = app.state::<AppState>();
            let mut status = match engine::init_pdfium(&candidates) {
                Ok((engine, lib)) => {
                    let label = engine::PDFIUM_LABEL.to_string();
                    state.workspace.set_engine(Arc::new(engine));
                    EngineStatus { available: true, engine: Some(label), library_path: Some(lib.display().to_string()), ..Default::default() }
                }
                Err(e) => EngineStatus { available: false, error: Some(e), ..Default::default() },
            };
            match worker::discover(&worker_candidates(app)) {
                Ok(cfg) => {
                    status.authoring_available = true;
                    status.authoring_java = Some(cfg.java.display().to_string());
                    state.workspace.set_worker(Arc::new(worker::PdfboxWorker::new(cfg)));
                }
                Err(e) => status.authoring_error = Some(e),
            }
            *state.engine_status.lock().unwrap() = status;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            engine_status,
            open_document,
            close_document,
            render_page,
            rotate_pages,
            save_as,
            extract_pages,
            merge_documents,
            cancel_job,
            startup_file,
            report_view_state,
            view_state,
            text_spans,
            search_document,
            document_outline,
            convert_document,
            preflight_extract,
            preflight_merge,
            form_fields,
            fill_form,
            add_annotation,
            annotation_kinds
        ])
        .run(tauri::generate_context!())
        .expect("error while running UnionPDF");
}
