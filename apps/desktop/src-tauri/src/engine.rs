//! Engine boundary. Commands/UI depend only on `PdfEngine` / `PdfDoc`, so the PDF engine
//! can be replaced (e.g. a PDFBox authoring worker) without touching the UI layer.

use crate::error::{AppError, AppResult};
use pdfium_render::prelude::*;
use serde::Serialize;
use std::any::Any;
use std::path::{Path, PathBuf};
use std::sync::OnceLock;

pub const PDFIUM_LABEL: &str = "PDFium 151.0.7881.0 (bblanchon/pdfium-binaries) via pdfium-render 0.9.4";

/// Largest bitmap we are willing to allocate for one page render (RGBA).
pub const MAX_RENDER_PIXELS: u64 = 60_000_000;

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct PageInfo {
    pub index: u32,
    /// Displayed size in PDF points, after /Rotate is applied.
    pub width: f32,
    pub height: f32,
    pub rotation: u16,
}

pub struct RenderedPage {
    pub width: u32,
    pub height: u32,
    pub rgba: Vec<u8>,
}

/// A bookmark entry (outline node) of the document.
#[derive(Debug, Clone, PartialEq, serde::Serialize)]
pub struct OutlineNode {
    pub title: String,
    /// Target page index, if the destination could be resolved.
    pub page: Option<u32>,
    pub children: Vec<OutlineNode>,
}

/// A search match in *displayed page space* (origin top-left, points, /Rotate applied).
#[derive(Debug, Clone, PartialEq, serde::Serialize)]
pub struct SearchHit {
    pub page: u32,
    pub text: String,
    pub left: f32,
    pub top: f32,
    pub width: f32,
    pub height: f32,
}

/// A text run of a page in *displayed page space* (origin top-left, points, /Rotate applied).
/// Used for the selectable text layer and for precise annotation quads.
#[derive(Debug, Clone, PartialEq, serde::Serialize)]
pub struct TextSpan {
    pub text: String,
    pub left: f32,
    pub top: f32,
    pub width: f32,
    pub height: f32,
}

pub trait PdfEngine: Send + Sync {
    fn label(&self) -> &'static str;
    fn open_file(&self, path: &Path) -> AppResult<Box<dyn PdfDoc>>;
    fn open_bytes(&self, bytes: Vec<u8>) -> AppResult<Box<dyn PdfDoc>>;
}

pub trait PdfDoc: Send + Sync {
    fn page_count(&self) -> u32;
    fn pages(&self) -> AppResult<Vec<PageInfo>>;
    fn render(&self, index: u32, scale: f32) -> AppResult<RenderedPage>;
    fn rotate(&mut self, index: u32, delta_degrees: i32) -> AppResult<()>;
    /// Keeps only `keep` (zero-based, any order) and deletes every other page in place.
    fn delete_pages_except(&mut self, keep: &[u32]) -> AppResult<()>;
    /// Appends all pages of `other` (must come from the same engine).
    fn append(&mut self, other: &dyn PdfDoc) -> AppResult<()>;
    fn save_bytes(&self) -> AppResult<Vec<u8>>;
    fn save_file(&self, path: &Path) -> AppResult<()>;
    /// Total number of outline (bookmark) entries.
    fn outline_count(&self) -> usize;
    fn has_form(&self) -> bool;
    /// Converts a point in displayed page space (points, origin top-left, /Rotate applied)
    /// to PDF user space.
    fn display_to_pdf(&self, index: u32, x: f32, y: f32) -> AppResult<(f32, f32)>;
    /// Bounding boxes `[l, b, r, t]` (PDF user space) of text segments overlapping `rect`.
    fn text_boxes(&self, index: u32, rect: [f32; 4]) -> AppResult<Vec<[f32; 4]>>;
    /// Text runs of the page in displayed page space (origin top-left, points).
    fn text_spans(&self, index: u32) -> AppResult<Vec<TextSpan>>;
    /// Finds `query` in the page text (no bitmap involved) and returns the match boxes.
    fn search_text(&self, index: u32, query: &str, case_sensitive: bool, limit: usize) -> AppResult<Vec<SearchHit>>;
    /// Outline (bookmarks) of the document as a tree; `page` is None for destinations that
    /// cannot be resolved (named destinations without a page).
    fn outline(&self) -> AppResult<Vec<OutlineNode>>;
    /// Annotation subtypes on a page. Never calls `stroke_color()` (crashes on annotations
    /// with /AP in pdfium-render 0.9.4 + PDFium 7881 — see regression test in ops.rs).
    fn annotation_kinds(&self, index: u32) -> AppResult<Vec<String>>;
    fn as_any(&self) -> &dyn Any;
}

// ---------------------------------------------------------------- PDFium implementation

static PDFIUM: OnceLock<Pdfium> = OnceLock::new();
static INIT_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

/// The process-wide PDFium instance, once initialised.
#[cfg(test)]
pub fn pdfium_instance() -> Option<&'static Pdfium> {
    PDFIUM.get()
}

/// Binds to the first loadable `pdfium.dll` in `candidates`. Can only succeed once per process.
pub fn init_pdfium(candidates: &[PathBuf]) -> Result<(PdfiumEngine, PathBuf), String> {
    let _guard = INIT_LOCK.lock().unwrap_or_else(|p| p.into_inner());
    let mut tried = Vec::new();
    for dir in candidates {
        let lib = Pdfium::pdfium_platform_library_name_at_path(dir);
        if !lib.is_file() {
            tried.push(format!("{} (tidak ada)", lib.display()));
            continue;
        }
        if PDFIUM.get().is_some() {
            return Ok((PdfiumEngine { pdfium: PDFIUM.get().unwrap() }, lib));
        }
        match Pdfium::bind_to_library(&lib) {
            Ok(bindings) => {
                let _ = PDFIUM.set(Pdfium::new(bindings));
                return Ok((PdfiumEngine { pdfium: PDFIUM.get().unwrap() }, lib));
            }
            Err(e) => tried.push(format!("{}: {e:?}", lib.display())),
        }
    }
    Err(format!("pdfium.dll tidak dapat dimuat. Dicoba: {}", tried.join("; ")))
}

pub struct PdfiumEngine {
    pdfium: &'static Pdfium,
}

fn map_load_error(e: PdfiumError) -> AppError {
    let d = format!("{e:?}");
    if d.contains("PasswordError") {
        AppError::PasswordRequired
    } else if d.contains("FileError") {
        AppError::Io(d)
    } else {
        AppError::Corrupt(d)
    }
}

fn internal(e: PdfiumError) -> AppError {
    AppError::Internal(format!("{e:?}"))
}

impl PdfEngine for PdfiumEngine {
    fn label(&self) -> &'static str {
        PDFIUM_LABEL
    }

    fn open_file(&self, path: &Path) -> AppResult<Box<dyn PdfDoc>> {
        if !path.is_file() {
            return Err(AppError::FileNotFound(path.to_path_buf()));
        }
        let doc = self.pdfium.load_pdf_from_file(path, None).map_err(map_load_error)?;
        Ok(Box::new(PdfiumDoc { doc }))
    }

    fn open_bytes(&self, bytes: Vec<u8>) -> AppResult<Box<dyn PdfDoc>> {
        let doc = self.pdfium.load_pdf_from_byte_vec(bytes, None).map_err(map_load_error)?;
        Ok(Box::new(PdfiumDoc { doc }))
    }
}

pub struct PdfiumDoc {
    doc: PdfDocument<'static>,
}

fn rotation_to_degrees(r: PdfPageRenderRotation) -> u16 {
    match r {
        PdfPageRenderRotation::None => 0,
        PdfPageRenderRotation::Degrees90 => 90,
        PdfPageRenderRotation::Degrees180 => 180,
        PdfPageRenderRotation::Degrees270 => 270,
    }
}

fn degrees_to_rotation(d: u16) -> PdfPageRenderRotation {
    match d % 360 {
        90 => PdfPageRenderRotation::Degrees90,
        180 => PdfPageRenderRotation::Degrees180,
        270 => PdfPageRenderRotation::Degrees270,
        _ => PdfPageRenderRotation::None,
    }
}

impl PdfiumDoc {
    fn page(&self, index: u32) -> AppResult<PdfPage<'static>> {
        let count = self.page_count();
        if index >= count {
            return Err(AppError::InvalidInput(format!("halaman {} di luar rentang (1–{count})", index + 1)));
        }
        self.doc.pages().get(index as i32).map_err(internal)
    }
}

impl PdfDoc for PdfiumDoc {
    fn page_count(&self) -> u32 {
        self.doc.pages().len().max(0) as u32
    }

    fn pages(&self) -> AppResult<Vec<PageInfo>> {
        let mut out = Vec::new();
        for (i, p) in self.doc.pages().iter().enumerate() {
            out.push(PageInfo {
                index: i as u32,
                width: p.width().value,
                height: p.height().value,
                rotation: p.rotation().map(rotation_to_degrees).unwrap_or(0),
            });
        }
        Ok(out)
    }

    fn render(&self, index: u32, scale: f32) -> AppResult<RenderedPage> {
        if !scale.is_finite() || !(0.05..=8.0).contains(&scale) {
            return Err(AppError::InvalidInput(format!("skala render {scale} di luar 0,05–8")));
        }
        let page = self.page(index)?;
        let w = (page.width().value * scale).ceil().max(1.0) as u64;
        let h = (page.height().value * scale).ceil().max(1.0) as u64;
        if w * h > MAX_RENDER_PIXELS {
            return Err(AppError::InvalidInput(format!("zoom terlalu besar ({w}×{h} piksel)")));
        }
        let cfg = PdfRenderConfig::new().scale_page_by_factor(scale).render_annotations(true).render_form_data(true);
        let bmp = page.render_with_config(&cfg).map_err(internal)?;
        Ok(RenderedPage { width: bmp.width() as u32, height: bmp.height() as u32, rgba: bmp.as_rgba_bytes() })
    }

    fn rotate(&mut self, index: u32, delta_degrees: i32) -> AppResult<()> {
        if delta_degrees % 90 != 0 {
            return Err(AppError::InvalidInput("rotasi harus kelipatan 90°".into()));
        }
        let mut page = self.page(index)?;
        let current = page.rotation().map(rotation_to_degrees).unwrap_or(0) as i32;
        let next = (current + delta_degrees).rem_euclid(360) as u16;
        page.set_rotation(degrees_to_rotation(next));
        Ok(())
    }

    fn delete_pages_except(&mut self, keep: &[u32]) -> AppResult<()> {
        let count = self.page_count();
        if keep.is_empty() {
            return Err(AppError::InvalidInput("tidak ada halaman yang dipilih".into()));
        }
        if let Some(bad) = keep.iter().find(|&&k| k >= count) {
            return Err(AppError::InvalidInput(format!("halaman {} di luar rentang (1–{count})", bad + 1)));
        }
        for i in (0..count).rev() {
            if !keep.contains(&i) {
                self.doc.pages().get(i as i32).map_err(internal)?.delete().map_err(internal)?;
            }
        }
        Ok(())
    }

    fn append(&mut self, other: &dyn PdfDoc) -> AppResult<()> {
        let other = other
            .as_any()
            .downcast_ref::<PdfiumDoc>()
            .ok_or_else(|| AppError::Internal("dokumen dari engine lain tidak dapat digabung".into()))?;
        self.doc.pages_mut().append(&other.doc).map_err(internal)
    }

    fn save_bytes(&self) -> AppResult<Vec<u8>> {
        self.doc.save_to_bytes().map_err(internal)
    }

    fn save_file(&self, path: &Path) -> AppResult<()> {
        self.doc.save_to_file(path).map_err(|e| AppError::Io(format!("{e:?}")))
    }

    fn outline_count(&self) -> usize {
        self.doc.bookmarks().iter().count()
    }

    fn has_form(&self) -> bool {
        self.doc.form().is_some()
    }

    fn display_to_pdf(&self, index: u32, x: f32, y: f32) -> AppResult<(f32, f32)> {
        // Device space at 10 px/pt keeps sub-point precision with integer pixel arguments.
        const K: f32 = 10.0;
        let page = self.page(index)?;
        let cfg = PdfRenderConfig::new().scale_page_by_factor(K);
        let (px, py) = page
            .pixels_to_points((x * K).round() as Pixels, (y * K).round() as Pixels, &cfg)
            .map_err(internal)?;
        Ok((px.value, py.value))
    }

    fn text_boxes(&self, index: u32, rect: [f32; 4]) -> AppResult<Vec<[f32; 4]>> {
        let page = self.page(index)?;
        let text = page.text().map_err(internal)?;
        let sel = PdfRect::new_from_values(rect[1], rect[0], rect[3], rect[2]);
        let mut out = Vec::new();
        for seg in text.segments().iter() {
            let b = seg.bounds();
            if b.does_overlap(&sel) && !seg.text().trim().is_empty() {
                out.push([b.left().value, b.bottom().value, b.right().value, b.top().value]);
            }
        }
        Ok(out)
    }

    fn annotation_kinds(&self, index: u32) -> AppResult<Vec<String>> {
        let page = self.page(index)?;
        Ok(page.annotations().iter().map(|a| format!("{:?}", a.annotation_type())).collect())
    }

    fn outline(&self) -> AppResult<Vec<OutlineNode>> {
        fn walk(first: Option<PdfBookmark<'_>>) -> Vec<OutlineNode> {
            let mut out = Vec::new();
            let mut cur = first;
            while let Some(b) = cur {
                let title = b.title().unwrap_or_else(|| "(tanpa judul)".to_string());
                let page = b.destination().and_then(|d| d.page_index().ok()).map(|i| i as u32);
                let children = walk(b.first_child());
                out.push(OutlineNode { title, page, children });
                cur = b.next_sibling();
            }
            out
        }
        Ok(walk(self.doc.bookmarks().root()))
    }

    fn search_text(&self, index: u32, query: &str, case_sensitive: bool, limit: usize) -> AppResult<Vec<SearchHit>> {
        if query.is_empty() {
            return Ok(Vec::new());
        }
        let page = self.page(index)?;
        let text = page.text().map_err(internal)?;
        const K: f32 = 10.0;
        let cfg = PdfRenderConfig::new().scale_page_by_factor(K);
        // Collect the characters with their (unrotated) page boxes.
        let mut chars: Vec<(char, PdfRect)> = Vec::new();
        for c in text.chars().iter() {
            let Some(ch) = c.unicode_char() else { continue };
            let Ok(b) = c.tight_bounds() else { continue };
            chars.push((ch, b));
        }
        let haystack: String = chars.iter().map(|(c, _)| *c).collect();
        let needle: Vec<char> = query.chars().collect();
        let mut hits = Vec::new();
        let hay: Vec<char> = haystack.chars().collect();
        if needle.is_empty() || hay.len() < needle.len() {
            return Ok(hits);
        }
        let cmp = |a: char, b: char| if case_sensitive { a == b } else { a.to_lowercase().eq(b.to_lowercase()) };
        let mut i = 0usize;
        while i + needle.len() <= hay.len() && hits.len() < limit {
            if (0..needle.len()).all(|k| cmp(hay[i + k], needle[k])) {
                // Union box of the matched characters, converted to displayed page space.
                let mut l = f32::MAX;
                let mut b = f32::MAX;
                let mut r = f32::MIN;
                let mut t = f32::MIN;
                for k in 0..needle.len() {
                    let (_, rect) = chars[i + k];
                    l = l.min(rect.left().value);
                    b = b.min(rect.bottom().value);
                    r = r.max(rect.right().value);
                    t = t.max(rect.top().value);
                }
                let (x1, y1) = page
                    .points_to_pixels(PdfPoints::new(l), PdfPoints::new(b), &cfg)
                    .map_err(internal)?;
                let (x2, y2) = page
                    .points_to_pixels(PdfPoints::new(r), PdfPoints::new(t), &cfg)
                    .map_err(internal)?;
                let (x1, y1) = (x1 as f32, y1 as f32);
                let (x2, y2) = (x2 as f32, y2 as f32);
                let left = x1.min(x2) / K;
                let top = y1.min(y2) / K;
                let right = x1.max(x2) / K;
                let bottom = y1.max(y2) / K;
                hits.push(SearchHit {
                    page: index,
                    text: haystack[i..i + needle.len()].to_string(),
                    left,
                    top,
                    width: (right - left).max(0.1),
                    height: (bottom - top).max(0.1),
                });
                i += needle.len();
            } else {
                i += 1;
            }
        }
        Ok(hits)
    }

    fn text_spans(&self, index: u32) -> AppResult<Vec<TextSpan>> {
        let page = self.page(index)?;
        let text = page.text().map_err(internal)?;
        // PDFium reports text in unrotated page space (origin bottom-left); the render config
        // applies /Rotate, so page->device conversion gives the displayed position.
        const K: f32 = 10.0;
        let cfg = PdfRenderConfig::new().scale_page_by_factor(K);
        let mut out = Vec::new();
        for seg in text.segments().iter() {
            let t = seg.text();
            if t.trim().is_empty() {
                continue;
            }
            let b = seg.bounds();
            let (x1, y1) = page
                .points_to_pixels(PdfPoints::new(b.left().value), PdfPoints::new(b.bottom().value), &cfg)
                .map_err(internal)?;
            let (x2, y2) = page
                .points_to_pixels(PdfPoints::new(b.right().value), PdfPoints::new(b.top().value), &cfg)
                .map_err(internal)?;
            let (x1, y1) = (x1 as f32, y1 as f32);
            let (x2, y2) = (x2 as f32, y2 as f32);
            let left = x1.min(x2) / K;
            let top = y1.min(y2) / K;
            let right = x1.max(x2) / K;
            let bottom = y1.max(y2) / K;
            out.push(TextSpan {
                text: t.to_string(),
                left,
                top,
                width: (right - left).max(0.1),
                height: (bottom - top).max(0.1),
            });
        }
        Ok(out)
    }

    fn as_any(&self) -> &dyn Any {
        self
    }
}
