use serde::Serialize;
use std::fmt;
use std::path::PathBuf;

/// Errors surfaced to the UI. Messages are user-facing (Indonesian); `code` is stable for the frontend.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AppError {
    EngineUnavailable(String),
    FileNotFound(PathBuf),
    PasswordRequired,
    Corrupt(String),
    Io(String),
    InvalidInput(String),
    WouldOverwriteInput(PathBuf),
    VerificationFailed(String),
    Cancelled,
    DocumentNotOpen(u32),
    WorkerUnavailable(String),
    WorkerFailed(String),
    Worker { code: String, message: String },
    Conflict(String),
    Internal(String),
}

impl AppError {
    pub fn code(&self) -> String {
        if let AppError::Worker { code, .. } = self {
            return format!("worker:{code}");
        }
        match self {
            AppError::EngineUnavailable(_) => "engine_unavailable",
            AppError::FileNotFound(_) => "file_not_found",
            AppError::PasswordRequired => "password_required",
            AppError::Corrupt(_) => "corrupt",
            AppError::Io(_) => "io",
            AppError::InvalidInput(_) => "invalid_input",
            AppError::WouldOverwriteInput(_) => "would_overwrite_input",
            AppError::VerificationFailed(_) => "verification_failed",
            AppError::Cancelled => "cancelled",
            AppError::DocumentNotOpen(_) => "document_not_open",
            AppError::WorkerUnavailable(_) => "worker_unavailable",
            AppError::WorkerFailed(_) => "worker_failed",
            AppError::Worker { .. } => "worker",
            AppError::Conflict(_) => "conflict",
            AppError::Internal(_) => "internal",
        }
        .to_string()
    }
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::EngineUnavailable(d) => write!(f, "Engine PDF tidak tersedia: {d}"),
            AppError::FileNotFound(p) => write!(f, "Berkas tidak ditemukan: {}", p.display()),
            AppError::PasswordRequired => write!(
                f,
                "Dokumen ini dilindungi kata sandi. Membuka dokumen terenkripsi belum didukung di versi ini."
            ),
            AppError::Corrupt(d) => write!(f, "Berkas tidak dapat dibaca sebagai PDF (rusak atau bukan PDF): {d}"),
            AppError::Io(d) => write!(f, "Gagal mengakses berkas: {d}"),
            AppError::InvalidInput(d) => write!(f, "Input tidak valid: {d}"),
            AppError::WouldOverwriteInput(p) => write!(
                f,
                "Tujuan sama dengan berkas sumber ({}). UnionPDF tidak menimpa berkas input; pilih nama lain.",
                p.display()
            ),
            AppError::VerificationFailed(d) => write!(f, "Verifikasi output gagal; berkas tujuan tidak diubah: {d}"),
            AppError::Cancelled => write!(f, "Operasi dibatalkan; berkas tujuan tidak diubah."),
            AppError::DocumentNotOpen(id) => write!(f, "Dokumen #{id} tidak sedang terbuka."),
            AppError::WorkerUnavailable(d) => write!(f, "Engine authoring (PDFBox) tidak tersedia: {d}"),
            AppError::WorkerFailed(d) => write!(f, "Engine authoring (PDFBox) gagal: {d}"),
            AppError::Worker { message, .. } => write!(f, "PDFBox: {message}"),
            AppError::Conflict(d) => write!(f, "Dokumen berubah selama operasi; hasil tidak diterapkan: {d}"),
            AppError::Internal(d) => write!(f, "Kesalahan internal: {d}"),
        }
    }
}

impl std::error::Error for AppError {}

impl From<std::io::Error> for AppError {
    fn from(e: std::io::Error) -> Self {
        AppError::Io(e.to_string())
    }
}

#[derive(Debug, Serialize)]
pub struct ErrorPayload {
    pub code: String,
    pub message: String,
}

impl From<AppError> for ErrorPayload {
    fn from(e: AppError) -> Self {
        ErrorPayload { code: e.code(), message: e.to_string() }
    }
}

pub type AppResult<T> = Result<T, AppError>;
