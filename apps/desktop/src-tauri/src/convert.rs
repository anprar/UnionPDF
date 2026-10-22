//! Document conversions: PDF -> PNG / JPEG / TXT and images -> PDF.
//!
//! The conversions work on the rendered bitmap (PNG/JPEG) or on the extracted text (TXT).
//! Image -> PDF is done by the PDFBox worker (it can embed images in a new document).

use crate::engine::{PageInfo, PdfDoc, PdfEngine, RenderedPage};
use crate::error::{AppError, AppResult};
use crate::worker::PdfboxWorker;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ConvertFormat {
    Png,
    Jpeg,
    Txt,
    Pdf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ConvertOptions {
    /// 1-based page range, e.g. "1-3, 5". Empty = all pages.
    pub range: String,
    /// Output resolution in DPI (raster formats).
    pub dpi: u32,
    /// JPEG quality 1..=100.
    pub quality: u8,
    /// Base name for the produced files (without extension).
    pub base_name: String,
}

impl Default for ConvertOptions {
    fn default() -> Self {
        ConvertOptions { range: String::new(), dpi: 150, quality: 85, base_name: "output".into() }
    }
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ConvertResult {
    pub output_dir: String,
    pub files: Vec<String>,
    pub pages: u32,
}

fn parse_pages(range: &str, total: u32) -> AppResult<Vec<u32>> {
    if range.trim().is_empty() {
        return Ok((0..total).collect());
    }
    crate::pages::parse_selection(range, total)
}

fn safe_name(name: &str) -> String {
    let cleaned: String = name
        .chars()
        .map(|c| if c.is_alphanumeric() || c == '-' || c == '_' { c } else { '_' })
        .collect();
    if cleaned.trim().is_empty() {
        "output".into()
    } else {
        cleaned
    }
}

/// Converts the open document into the requested format inside `out_dir`.
pub fn convert_document(
    engine: &Arc<dyn PdfEngine>,
    worker: Option<&Arc<PdfboxWorker>>,
    doc: &dyn PdfDoc,
    pages: &[PageInfo],
    format: ConvertFormat,
    options: &ConvertOptions,
    out_dir: &Path,
    images: &[PathBuf],
    cancel: &AtomicBool,
    progress: &dyn Fn(&str),
) -> AppResult<ConvertResult> {
    std::fs::create_dir_all(out_dir).map_err(|e| AppError::Io(format!("folder keluaran tidak dapat dibuat: {e}")))?;
    let base = safe_name(&options.base_name);
    let mut files = Vec::new();
    // Apply the page range (1-based, e.g. "1-3, 5"); empty = all pages.
    let selected: Vec<PageInfo> = {
        let total = pages.len() as u32;
        let wanted = parse_pages(&options.range, total)?;
        let mut out: Vec<PageInfo> = Vec::new();
        for p in pages.iter() {
            if wanted.contains(&p.index) {
                out.push(p.clone());
            }
        }
        if out.is_empty() {
            return Err(AppError::InvalidInput("rentang halaman tidak menghasilkan halaman".into()));
        }
        out
    };
    let pages: Vec<PageInfo> = selected;

    match format {
        ConvertFormat::Txt => {
            let mut out = String::new();
            for p in &pages {
                if cancel.load(Ordering::SeqCst) {
                    return Err(AppError::Cancelled);
                }
                progress(&format!("Mengambil teks halaman {}", p.index + 1));
                let spans = doc.text_spans(p.index)?;
                let mut line = String::new();
                for s in &spans {
                    line.push_str(&s.text);
                    line.push(' ');
                }
                out.push_str(&format!("--- Halaman {} ---\n{}\n", p.index + 1, line.trim()));
            }
            let path = out_dir.join(format!("{base}.txt"));
            std::fs::write(&path, out).map_err(|e| AppError::Io(e.to_string()))?;
            files.push(path.to_string_lossy().to_string());
        }
        ConvertFormat::Png | ConvertFormat::Jpeg => {
            let dpi = options.dpi.clamp(36, 1200);
            let scale = dpi as f32 / 72.0;
            for p in &pages {
                if cancel.load(Ordering::SeqCst) {
                    return Err(AppError::Cancelled);
                }
                progress(&format!("Merender halaman {} ke gambar", p.index + 1));
                let rendered: RenderedPage = doc.render(p.index, scale)?;
                let img = image::RgbaImage::from_raw(rendered.width, rendered.height, rendered.rgba)
                    .ok_or_else(|| AppError::Internal("bitmap tidak valid".into()))?;
                let path = out_dir.join(format!("{}-{:04}.{}", base, p.index + 1, if format == ConvertFormat::Png { "png" } else { "jpg" }));
                if format == ConvertFormat::Png {
                    img.save(&path).map_err(|e| AppError::Io(e.to_string()))?;
                } else {
                    let rgb = image::DynamicImage::ImageRgba8(img).to_rgb8();
                    let mut buf = Vec::new();
                    let mut enc = image::codecs::jpeg::JpegEncoder::new_with_quality(&mut buf, options.quality.clamp(1, 100));
                    enc.encode_image(&rgb).map_err(|e| AppError::Io(e.to_string()))?;
                    std::fs::write(&path, buf).map_err(|e| AppError::Io(e.to_string()))?;
                }
                files.push(path.to_string_lossy().to_string());
            }
        }
        ConvertFormat::Pdf => {
            // Image -> PDF is done by the PDFBox worker.
            let Some(worker) = worker else {
                return Err(AppError::WorkerUnavailable("fitur gambar ke PDF membutuhkan mesin authoring".into()));
            };
            if images.is_empty() {
                return Err(AppError::InvalidInput("pilih setidaknya satu berkas gambar".into()));
            }
            progress("Menyusun PDF dari gambar");
            let path = out_dir.join(format!("{base}.pdf"));
            let inputs: Vec<String> = images.iter().map(|p| p.to_string_lossy().to_string()).collect();
            let data = worker.request(
                "images_to_pdf",
                serde_json::json!({ "inputs": inputs, "output": path.to_string_lossy() }),
                crate::ops::WORKER_TIMEOUT,
                cancel,
                progress,
            )?;
            let page_count = data["page_count"].as_u64().unwrap_or(images.len() as u64) as u32;
            files.push(path.to_string_lossy().to_string());
            return Ok(ConvertResult { output_dir: out_dir.to_string_lossy().to_string(), files, pages: page_count });
        }
    }

    let _ = engine;
    let page_count = pages.len() as u32;
    Ok(ConvertResult {
        output_dir: out_dir.to_string_lossy().to_string(),
        files,
        pages: page_count,
    })
}
