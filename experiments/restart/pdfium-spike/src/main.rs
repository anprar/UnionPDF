//! UnionPDF controlled-restart spike (NOT production code).
//!
//! Subcommands: rs01 | rs02 | rs03 | rs05 | all
//! Run from `experiments/restart` so relative paths resolve:
//!   cargo run --release --manifest-path pdfium-spike/Cargo.toml -- all

use pdfium_render::prelude::*;
use serde_json::{json, Value};
use std::error::Error;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{mpsc, Arc};
use std::time::{Duration, Instant};

type Res<T> = Result<T, Box<dyn Error>>;

// ---------- process memory (Windows, kernel32 K32GetProcessMemoryInfo) ----------
#[repr(C)]
#[allow(non_snake_case)]
struct ProcessMemoryCounters {
    cb: u32,
    PageFaultCount: u32,
    PeakWorkingSetSize: usize,
    WorkingSetSize: usize,
    QuotaPeakPagedPoolUsage: usize,
    QuotaPagedPoolUsage: usize,
    QuotaPeakNonPagedPoolUsage: usize,
    QuotaNonPagedPoolUsage: usize,
    PagefileUsage: usize,
    PeakPagefileUsage: usize,
}

#[link(name = "kernel32")]
extern "system" {
    fn GetCurrentProcess() -> isize;
    fn K32GetProcessMemoryInfo(process: isize, counters: *mut ProcessMemoryCounters, cb: u32) -> i32;
}

fn memory() -> Value {
    let mut c = ProcessMemoryCounters {
        cb: std::mem::size_of::<ProcessMemoryCounters>() as u32,
        PageFaultCount: 0,
        PeakWorkingSetSize: 0,
        WorkingSetSize: 0,
        QuotaPeakPagedPoolUsage: 0,
        QuotaPagedPoolUsage: 0,
        QuotaPeakNonPagedPoolUsage: 0,
        QuotaNonPagedPoolUsage: 0,
        PagefileUsage: 0,
        PeakPagefileUsage: 0,
    };
    let ok = unsafe { K32GetProcessMemoryInfo(GetCurrentProcess(), &mut c, c.cb) };
    if ok == 0 {
        return json!({"error": "K32GetProcessMemoryInfo failed"});
    }
    json!({
        "working_set_bytes": c.WorkingSetSize,
        "peak_working_set_bytes": c.PeakWorkingSetSize,
        "private_bytes": c.PagefileUsage,
        "peak_private_bytes": c.PeakPagefileUsage,
    })
}

// ---------- helpers ----------
struct Ctx {
    root: PathBuf,
    manifest: Value,
}

impl Ctx {
    fn fixture(&self, name: &str) -> PathBuf {
        self.root.join("fixtures").join("generated").join(name)
    }
    fn out_dir(&self, spike: &str) -> Res<PathBuf> {
        let d = self.root.join("raw").join(spike);
        fs::create_dir_all(&d)?;
        Ok(d)
    }
}

fn ms(d: Duration) -> f64 {
    (d.as_secs_f64() * 1000.0 * 1000.0).round() / 1000.0
}

fn norm(s: &str) -> String {
    s.split_whitespace().collect::<Vec<_>>().join(" ")
}

fn write_json(path: &Path, v: &Value) -> Res<()> {
    fs::write(path, serde_json::to_string_pretty(v)?)?;
    Ok(())
}

fn rect_json(r: &PdfRect) -> Value {
    json!([r.left().value, r.bottom().value, r.right().value, r.top().value])
}

fn color_json(c: Result<PdfColor, PdfiumError>) -> Value {
    match c {
        Ok(c) => json!([c.red(), c.green(), c.blue(), c.alpha()]),
        Err(e) => json!(format!("error: {e:?}")),
    }
}

fn pdf_rect(l: f32, b: f32, r: f32, t: f32) -> PdfRect {
    PdfRect::new(PdfPoints::new(b), PdfPoints::new(l), PdfPoints::new(t), PdfPoints::new(r))
}

fn rotation_deg(p: &PdfPage) -> Value {
    match p.rotation() {
        Ok(PdfPageRenderRotation::None) => json!(0),
        Ok(PdfPageRenderRotation::Degrees90) => json!(90),
        Ok(PdfPageRenderRotation::Degrees180) => json!(180),
        Ok(PdfPageRenderRotation::Degrees270) => json!(270),
        Err(e) => json!(format!("error: {e:?}")),
    }
}

fn describe_document(doc: &PdfDocument) -> Res<Value> {
    let mut pages = vec![];
    for (i, page) in doc.pages().iter().enumerate() {
        let mut annots = vec![];
        for a in page.annotations().iter() {
            annots.push(json!({
                "type": format!("{:?}", a.annotation_type()),
                "bounds": a.bounds().map(|r| rect_json(&r)).unwrap_or(json!(null)),
                "contents": a.contents(),
            }));
        }
        pages.push(json!({
            "index": i,
            "width": page.width().value,
            "height": page.height().value,
            "rotation": rotation_deg(&page),
            "text": page.text().map(|t| t.all()).unwrap_or_default(),
            "annotations": annots,
        }));
    }
    Ok(json!({"page_count": doc.pages().len(), "pages": pages}))
}

// ---------- RS-01 ----------
fn rs01(pdfium: &Pdfium, ctx: &Ctx, init_ms: f64) -> Res<Value> {
    let out = ctx.out_dir("rs01")?;
    let mut fixtures_out = vec![];
    let mem_after_init = memory();

    // Time-to-first-render: load first fixture + render page 0 at scale 1.5 (library already bound).
    let t = Instant::now();
    let first = pdfium.load_pdf_from_file(&ctx.fixture("rs01_mixed_sizes.pdf"), None)?;
    let p0 = first.pages().get(0)?;
    let _bmp = p0.render_with_config(&PdfRenderConfig::new().scale_page_by_factor(1.5))?;
    let first_render_ms = ms(t.elapsed());
    drop(_bmp);
    drop(p0);
    drop(first);

    let names = [
        "rs01_mixed_sizes",
        "rs01_latin",
        "rs01_unicode_arabic",
        "rs01_images",
        "rs01_large_500p",
    ];
    for key in names {
        let fx = &ctx.manifest["fixtures"][key];
        let file = fx["file"].as_str().ok_or("manifest file")?;
        let expected = fx["expected_lines"].as_array().ok_or("expected_lines")?;
        let t_load = Instant::now();
        let doc = pdfium.load_pdf_from_file(&ctx.fixture(file), None)?;
        let load_ms = ms(t_load.elapsed());
        let count = doc.pages().len() as usize;
        let mut rendered_ok = 0usize;
        let mut render_errors = vec![];
        let mut text_mismatch = vec![];
        let mut render_ms_total = 0.0;
        let mut pages_detail = vec![];
        let t_all = Instant::now();
        for (i, page) in doc.pages().iter().enumerate() {
            let t_r = Instant::now();
            match page.render_with_config(&PdfRenderConfig::new().scale_page_by_factor(1.0)) {
                Ok(_) => rendered_ok += 1,
                Err(e) => render_errors.push(format!("page {i}: {e:?}")),
            }
            render_ms_total += ms(t_r.elapsed());
            let text = page.text().map(|t| t.all()).unwrap_or_default();
            let ntext = norm(&text);
            let missing: Vec<String> = expected
                .get(i)
                .and_then(|v| v.as_array())
                .map(|lines| {
                    lines
                        .iter()
                        .filter_map(|l| l.as_str())
                        .filter(|l| !ntext.contains(&norm(l)))
                        .map(|l| l.to_string())
                        .collect()
                })
                .unwrap_or_default();
            if !missing.is_empty() {
                text_mismatch.push(json!({"page": i, "missing": missing, "extracted": text}));
            }
            // PNG at scale 2.0 for cross-engine pixel comparison (small docs: all pages; large: first 3).
            if count <= 10 || i < 3 {
                let img = page
                    .render_with_config(&PdfRenderConfig::new().scale_page_by_factor(2.0))?
                    .as_image()?;
                let png = out.join(format!("{key}_p{i}_x2.png"));
                img.save(&png)?;
                pages_detail.push(json!({"page": i, "png_x2": png.file_name().unwrap().to_string_lossy(), "text": text}));
            }
        }
        let all_pages_ms = ms(t_all.elapsed());

        // Zoom levels and thumbnail on page 0.
        let page0 = doc.pages().get(0)?;
        let mut zoom = vec![];
        for scale in [0.5f32, 1.0, 2.0, 4.0] {
            let t_z = Instant::now();
            let bmp = page0.render_with_config(&PdfRenderConfig::new().scale_page_by_factor(scale))?;
            zoom.push(json!({"scale": scale, "width": bmp.width(), "height": bmp.height(), "ms": ms(t_z.elapsed())}));
        }
        let t_th = Instant::now();
        let thumb = page0.render_with_config(&PdfRenderConfig::new().set_target_width(160))?;
        let thumb_ms = ms(t_th.elapsed());
        let thumb_png = out.join(format!("{key}_p0_thumb160.png"));
        thumb.as_image()?.save(&thumb_png)?;

        let mem_now = memory();
        fixtures_out.push(json!({
            "fixture": file,
            "page_count": count,
            "load_ms": load_ms,
            "render_scale1_all_pages_ok": rendered_ok,
            "render_errors": render_errors,
            "render_scale1_total_ms": render_ms_total,
            "all_pages_loop_ms (render x1 + text + png)": all_pages_ms,
            "text_mismatches": text_mismatch,
            "zoom_page0": zoom,
            "thumbnail_160_ms": thumb_ms,
            "thumbnail_png": thumb_png.file_name().unwrap().to_string_lossy(),
            "pages_detail": pages_detail,
            "memory_after": mem_now,
        }));
    }

    // Search token on rs01_latin page index 1.
    let latin = &ctx.manifest["fixtures"]["rs01_latin"];
    let token = latin["search_token"].as_str().unwrap_or("");
    let doc = pdfium.load_pdf_from_file(&ctx.fixture(latin["file"].as_str().unwrap()), None)?;
    let mut search_hits = vec![];
    for (i, page) in doc.pages().iter().enumerate() {
        let txt = page.text()?.all();
        if txt.contains(token) {
            search_hits.push(i);
        }
    }
    drop(doc);

    // Cancellation of stale render requests (request-level, cross-thread).
    let cancel = rs01_cancel(pdfium, ctx)?;

    let result = json!({
        "spike": "RS-01",
        "engine": "PDFium chromium/7881 via pdfium-render 0.9.4",
        "library_bind_and_init_ms": init_ms,
        "time_to_first_render_ms (load rs01_mixed_sizes + render p0 x1.5, library already initialised)": first_render_ms,
        "memory_after_init": mem_after_init,
        "fixtures": fixtures_out,
        "search": {"token": token, "expected_page": latin["search_token_page"], "found_on_pages": search_hits},
        "cancel": cancel,
        "memory_end": memory(),
        "not_tested": [
            "mid-page progressive render cancellation (FPDF_RenderPageBitmap_Start + IFSDK_PAUSE)",
            "Arabic shaping (generator inserts logical-order glyphs without shaping)"
        ],
    });
    write_json(&out.join("result_pdfium.json"), &result)?;
    Ok(result)
}

fn rs01_cancel(pdfium: &Pdfium, ctx: &Ctx) -> Res<Value> {
    let file = ctx.manifest["fixtures"]["rs01_large_500p"]["file"].as_str().unwrap().to_string();
    let doc = pdfium.load_pdf_from_file(&ctx.fixture(&file), None)?;
    let cancel = Arc::new(AtomicBool::new(false));
    let done = Arc::new(AtomicUsize::new(0));
    let (tx, rx) = mpsc::channel::<u16>();
    let requested = 60u16;
    let cancel_after = 5usize;
    let mut cancel_set_at: Option<Instant> = None;
    let mut worker_stopped_at: Option<Instant> = None;
    let mut rendered_pages: Vec<u16> = vec![];
    std::thread::scope(|s| -> Res<()> {
        let c = cancel.clone();
        let d = done.clone();
        let docref = &doc;
        let h = s.spawn(move || -> (Vec<u16>, Instant) {
            let mut out = vec![];
            for idx in rx {
                if c.load(Ordering::SeqCst) {
                    break; // stale request: dropped without rendering
                }
                if let Ok(page) = docref.pages().get(idx as i32) {
                    let _ = page.render_with_config(&PdfRenderConfig::new().scale_page_by_factor(1.5));
                    out.push(idx);
                    d.fetch_add(1, Ordering::SeqCst);
                }
            }
            (out, Instant::now())
        });
        for i in 0..requested {
            tx.send(i)?;
        }
        drop(tx);
        while done.load(Ordering::SeqCst) < cancel_after {
            std::thread::sleep(Duration::from_micros(200));
        }
        cancel.store(true, Ordering::SeqCst);
        cancel_set_at = Some(Instant::now());
        let (pages, stopped) = h.join().map_err(|_| "worker panicked")?;
        rendered_pages = pages;
        worker_stopped_at = Some(stopped);
        Ok(())
    })?;
    let latency = match (cancel_set_at, worker_stopped_at) {
        (Some(a), Some(b)) if b >= a => ms(b - a),
        _ => 0.0,
    };
    Ok(json!({
        "requests_queued": requested,
        "cancel_signalled_after_completed": cancel_after,
        "rendered_count": rendered_pages.len(),
        "rendered_pages": rendered_pages,
        "dropped_without_render": requested as usize - rendered_pages.len(),
        "cancel_to_worker_stop_ms": latency,
        "granularity": "between requests (a page already being rendered completes)",
    }))
}

// ---------- RS-02 (PDFium part) ----------
fn rs02(pdfium: &Pdfium, raw: &dyn PdfiumLibraryBindings, ctx: &Ctx) -> Res<Value> {
    let out = ctx.out_dir("rs02")?;
    let fx = &ctx.manifest["fixtures"]["rs02_annot_base"];
    let src = ctx.fixture(fx["file"].as_str().unwrap());
    let doc = pdfium.load_pdf_from_file(&src, None)?;
    let mut created = vec![];
    let mut errors = vec![];

    // Page index 1: text-markup annotations over measured target lines.
    {
        let mut page = doc.pages().get(1)?;
        let targets = &fx["markup_targets_pdf_rect"];
        let colors = [
            ("highlight", PdfColor::new(255, 230, 0, 255)),
            ("underline", PdfColor::new(0, 120, 255, 255)),
            ("strikeout", PdfColor::new(220, 0, 0, 255)),
            ("squiggly", PdfColor::new(0, 160, 60, 255)),
        ];
        for (kind, color) in colors {
            let r = &targets[kind];
            let rect = pdf_rect(
                r[0].as_f64().unwrap() as f32,
                r[1].as_f64().unwrap() as f32,
                r[2].as_f64().unwrap() as f32,
                r[3].as_f64().unwrap() as f32,
            );
            let contents = format!("RS02-{kind}");
            let res: Result<(), PdfiumError> = (|| {
                let annots = page.annotations_mut();
                match kind {
                    "highlight" => {
                        let mut a = annots.create_highlight_annotation()?;
                        a.set_bounds(rect)?;
                        a.attachment_points_mut().create_attachment_point_at_end(PdfQuadPoints::from_rect(&rect))?;
                        a.set_stroke_color(color)?;
                        a.set_contents(&contents)?;
                    }
                    "underline" => {
                        let mut a = annots.create_underline_annotation()?;
                        a.set_bounds(rect)?;
                        a.attachment_points_mut().create_attachment_point_at_end(PdfQuadPoints::from_rect(&rect))?;
                        a.set_stroke_color(color)?;
                        a.set_contents(&contents)?;
                    }
                    "strikeout" => {
                        let mut a = annots.create_strikeout_annotation()?;
                        a.set_bounds(rect)?;
                        a.attachment_points_mut().create_attachment_point_at_end(PdfQuadPoints::from_rect(&rect))?;
                        a.set_stroke_color(color)?;
                        a.set_contents(&contents)?;
                    }
                    _ => {
                        let mut a = annots.create_squiggly_annotation()?;
                        a.set_bounds(rect)?;
                        a.attachment_points_mut().create_attachment_point_at_end(PdfQuadPoints::from_rect(&rect))?;
                        a.set_stroke_color(color)?;
                        a.set_contents(&contents)?;
                    }
                }
                Ok(())
            })();
            match res {
                Ok(()) => created.push(json!({"page": 1, "kind": kind, "via": "pdfium-render high-level", "rect": rect_json(&rect), "contents": contents})),
                Err(e) => errors.push(json!({"page": 1, "kind": kind, "error": format!("{e:?}")})),
            }
        }
    }

    // Page index 0: note, free text, square, stamp (wrapper) + circle and ink (raw FFI).
    {
        let mut page = doc.pages().get(0)?;
        let wrapper_items: [(&str, PdfRect, PdfColor); 4] = [
            ("text", pdf_rect(60.0, 700.0, 84.0, 724.0), PdfColor::new(255, 200, 0, 255)),
            ("freetext", pdf_rect(120.0, 690.0, 320.0, 730.0), PdfColor::new(0, 0, 0, 255)),
            ("square", pdf_rect(60.0, 560.0, 200.0, 660.0), PdfColor::new(200, 0, 200, 255)),
            ("stamp", pdf_rect(380.0, 560.0, 540.0, 640.0), PdfColor::new(0, 128, 128, 255)),
        ];
        for (kind, rect, color) in wrapper_items {
            let contents = format!("RS02-{kind}");
            let res: Result<(), PdfiumError> = (|| {
                let annots = page.annotations_mut();
                match kind {
                    "text" => {
                        let mut a = annots.create_text_annotation(&contents)?;
                        a.set_bounds(rect)?;
                        a.set_stroke_color(color)?;
                    }
                    "freetext" => {
                        let mut a = annots.create_free_text_annotation(&contents)?;
                        a.set_bounds(rect)?;
                        a.set_stroke_color(color)?;
                    }
                    "square" => {
                        let mut a = annots.create_square_annotation()?;
                        a.set_bounds(rect)?;
                        a.set_stroke_color(color)?;
                        a.set_contents(&contents)?;
                    }
                    _ => {
                        let mut a = annots.create_stamp_annotation()?;
                        a.set_bounds(rect)?;
                        a.set_stroke_color(color)?;
                        a.set_contents(&contents)?;
                    }
                }
                Ok(())
            })();
            match res {
                Ok(()) => created.push(json!({"page": 0, "kind": kind, "via": "pdfium-render high-level", "rect": rect_json(&rect), "contents": contents})),
                Err(e) => errors.push(json!({"page": 0, "kind": kind, "error": format!("{e:?}")})),
            }
        }

        // Raw FFI: circle (not wrapped by pdfium-render 0.9.4) and ink with an InkList stroke.
        let page_handle = raw.get_handle_from_page(&page);
        for (kind, subtype, l, b, r, t, rgb) in [
            ("circle", 6i32, 240.0f32, 560.0f32, 360.0f32, 660.0f32, (0u32, 90u32, 200u32)),
            ("ink", 15i32, 60.0, 420.0, 300.0, 520.0, (200, 60, 0)),
        ] {
            let contents = format!("RS02-{kind}");
            unsafe {
                let annot = raw.FPDFPage_CreateAnnot(page_handle, subtype);
                if annot.is_null() {
                    errors.push(json!({"page": 0, "kind": kind, "error": "FPDFPage_CreateAnnot returned NULL"}));
                    continue;
                }
                let rect = FS_RECTF { left: l, top: t, right: r, bottom: b };
                let ok_rect = raw.FPDFAnnot_SetRect(annot, &rect);
                // 0 = FPDFANNOT_COLORTYPE_Color (fpdf_annot.h); the named constant is not re-exported by pdfium-render.
                let ok_color = raw.FPDFAnnot_SetColor(annot, 0, rgb.0, rgb.1, rgb.2, 255);
                let mut ink_index = -2;
                if kind == "ink" {
                    let pts: Vec<FS_POINTF> = (0..12)
                        .map(|k| FS_POINTF { x: l + 20.0 * k as f32, y: b + 30.0 + if k % 2 == 0 { 0.0 } else { 40.0 } })
                        .collect();
                    ink_index = raw.FPDFAnnot_AddInkStroke(annot, pts.as_ptr(), pts.len());
                }
                let ok_contents = raw.FPDFAnnot_SetStringValue_str(annot, "Contents", &contents);
                raw.FPDFPage_CloseAnnot(annot);
                created.push(json!({
                    "page": 0, "kind": kind, "via": "raw FFI FPDFPage_CreateAnnot",
                    "rect": [l, b, r, t], "contents": contents,
                    "set_rect_ok": ok_rect != 0, "set_color_ok": ok_color != 0,
                    "set_contents_ok": ok_contents != 0, "ink_stroke_index": ink_index,
                }));
            }
        }
    }

    let out_pdf = out.join("annotated.pdf");
    doc.save_to_file(&out_pdf)?;
    drop(doc);

    // Reopen with PDFium.
    let re = pdfium.load_pdf_from_file(&out_pdf, None)?;
    let mut reopened = vec![];
    for (pi, page) in re.pages().iter().enumerate() {
        for a in page.annotations().iter() {
            reopened.push(json!({
                "page": pi,
                "type": format!("{:?}", a.annotation_type()),
                "bounds": a.bounds().map(|r| rect_json(&r)).unwrap_or(json!(null)),
                "contents": a.contents(),
                "stroke_color": color_json(a.stroke_color()),
                "attachment_points": a.attachment_points().len(),
            }));
        }
        for (suffix, with_annots) in [("annots", true), ("noannots", false)] {
            let img = page
                .render_with_config(&PdfRenderConfig::new().scale_page_by_factor(2.0).render_annotations(with_annots))?
                .as_image()?;
            img.save(out.join(format!("annotated_p{pi}_{suffix}_x2.png")))?;
        }
    }
    let result = json!({
        "spike": "RS-02 (PDFium part)",
        "input": src.file_name().unwrap().to_string_lossy(),
        "output": "annotated.pdf",
        "created": created,
        "creation_errors": errors,
        "reopened_by_pdfium": reopened,
        "wrapper_notes": [
            "pdfium-render 0.9.4 exposes create_* for: free_text, highlight, ink, link, popup, square, squiggly, stamp, strikeout, text, underline",
            "circle is creatable upstream but not wrapped -> raw FFI used",
            "ink: wrapper has no InkList stroke API -> raw FPDFAnnot_AddInkStroke used",
            "raw bindings obtained by calling Pdfium::bind_to_library twice before Pdfium::new (accessor trait is pub(crate) in 0.9.4)"
        ],
    });
    write_json(&out.join("result_pdfium.json"), &result)?;
    Ok(result)
}

// ---------- RS-03 (PDFium part) ----------
fn rs03(pdfium: &Pdfium, ctx: &Ctx) -> Res<Value> {
    let out = ctx.out_dir("rs03")?;
    let src = ctx.fixture(ctx.manifest["fixtures"]["rs03_form"]["file"].as_str().unwrap());
    let doc = pdfium.load_pdf_from_file(&src, None)?;
    let mut actions = vec![];
    let mut fields_before = vec![];
    {
        let page = doc.pages().get(0)?;
        let mut radio_seen = 0;
        for mut annot in page.annotations().iter() {
            if let PdfPageAnnotation::Widget(ref mut w) = annot {
                if let Some(field) = w.form_field_mut() {
                    let name = field.name();
                    let ftype = format!("{:?}", field.field_type());
                    fields_before.push(json!({"name": name, "type": ftype}));
                    if let Some(t) = field.as_text_field_mut() {
                        let r = t.set_value("Diisi PDFium RS03");
                        actions.push(json!({"field": name, "action": "text.set_value", "ok": r.is_ok(), "err": r.err().map(|e| format!("{e:?}"))}));
                    } else if let Some(c) = field.as_checkbox_field_mut() {
                        let r = c.set_checked(true);
                        actions.push(json!({"field": name, "action": "checkbox.set_checked(true)", "ok": r.is_ok(), "err": r.err().map(|e| format!("{e:?}"))}));
                    } else if let Some(rb) = field.as_radio_button_field_mut() {
                        radio_seen += 1;
                        if radio_seen == 2 {
                            let r = rb.set_checked();
                            actions.push(json!({"field": name, "action": "radio#2.set_checked()", "ok": r.is_ok(), "err": r.err().map(|e| format!("{e:?}"))}));
                        }
                    } else {
                        actions.push(json!({"field": name, "action": "none", "reason": format!("no setter exposed by pdfium-render 0.9.4 for {ftype}")}));
                    }
                }
            }
        }
    }
    let out_pdf = out.join("filled.pdf");
    doc.save_to_file(&out_pdf)?;
    drop(doc);

    let re = pdfium.load_pdf_from_file(&out_pdf, None)?;
    let mut fields_after = vec![];
    {
        let page = re.pages().get(0)?;
        for annot in page.annotations().iter() {
            if let Some(field) = annot.as_form_field() {
                fields_after.push(field_json(field));
            }
        }
        let img = page
            .render_with_config(&PdfRenderConfig::new().scale_page_by_factor(2.0).render_form_data(true))?
            .as_image()?;
        img.save(out.join("filled_p0_x2.png"))?;
    }
    let result = json!({
        "spike": "RS-03 (PDFium part)",
        "input": src.file_name().unwrap().to_string_lossy(),
        "output": "filled.pdf",
        "fields_before": fields_before,
        "actions": actions,
        "reopened_by_pdfium": fields_after,
    });
    write_json(&out.join("result_pdfium.json"), &result)?;
    Ok(result)
}

// ---------- RS-05 (PDFium part) ----------
fn rs05(pdfium: &Pdfium, raw: &dyn PdfiumLibraryBindings, ctx: &Ctx) -> Res<Value> {
    let out = ctx.out_dir("rs05")?;
    let fx = &ctx.manifest["fixtures"]["rs05_structure"];
    let src = ctx.fixture(fx["file"].as_str().unwrap());
    let merge_src = ctx.fixture(fx["merge_source"].as_str().unwrap());
    let mut ops = vec![];

    let mut record = |name: &str, op_ms: f64, path: &Path, err: Option<String>| -> Res<()> {
        let mut v = json!({"op": name, "op_and_save_ms": op_ms, "output": path.file_name().unwrap().to_string_lossy(), "error": err});
        if path.exists() {
            let d = pdfium.load_pdf_from_file(path, None)?;
            v["reopened_by_pdfium"] = describe_document(&d)?;
        }
        ops.push(v);
        Ok(())
    };

    // rotate page 2 (index 1) by 90 degrees
    {
        let t = Instant::now();
        let doc = pdfium.load_pdf_from_file(&src, None)?;
        let mut p = doc.pages().get(1)?;
        p.set_rotation(PdfPageRenderRotation::Degrees90);
        drop(p);
        let path = out.join("rotate.pdf");
        doc.save_to_file(&path)?;
        let e = ms(t.elapsed());
        drop(doc);
        record("rotate p2 90deg", e, &path, None)?;
    }
    // delete page 5 (index 4)
    {
        let t = Instant::now();
        let doc = pdfium.load_pdf_from_file(&src, None)?;
        let r = doc.pages().get(4)?.delete();
        let path = out.join("delete.pdf");
        doc.save_to_file(&path)?;
        let e = ms(t.elapsed());
        drop(doc);
        record("delete p5", e, &path, r.err().map(|e| format!("{e:?}")))?;
    }
    // reorder: move page 6 (index 5) to front via raw FPDF_MovePages
    {
        let t = Instant::now();
        let doc = pdfium.load_pdf_from_file(&src, None)?;
        let idx = [5i32];
        let ok = unsafe { raw.FPDF_MovePages(raw.get_handle_from_document(&doc), idx.as_ptr(), 1, 0) };
        let path = out.join("reorder.pdf");
        doc.save_to_file(&path)?;
        let e = ms(t.elapsed());
        drop(doc);
        record("reorder p6 -> front (FPDF_MovePages)", e, &path, if ok == 0 { Some("FPDF_MovePages returned false".into()) } else { None })?;
    }
    // insert blank A4 page at index 2
    {
        let t = Instant::now();
        let mut doc = pdfium.load_pdf_from_file(&src, None)?;
        let r = doc.pages_mut().create_page_at_index(PdfPagePaperSize::a4(), 2).map(|_| ());
        let path = out.join("insert_blank.pdf");
        doc.save_to_file(&path)?;
        let e = ms(t.elapsed());
        drop(doc);
        record("insert blank A4 at index 2", e, &path, r.err().map(|e| format!("{e:?}")))?;
    }
    // merge (append into loaded source document)
    {
        let t = Instant::now();
        let mut doc = pdfium.load_pdf_from_file(&src, None)?;
        let other = pdfium.load_pdf_from_file(&merge_src, None)?;
        let r = doc.pages_mut().append(&other);
        let path = out.join("merge_append.pdf");
        doc.save_to_file(&path)?;
        let e = ms(t.elapsed());
        drop(other);
        drop(doc);
        record("merge: append merge_source into loaded structure doc", e, &path, r.err().map(|e| format!("{e:?}")))?;
    }
    // merge into a brand-new document
    {
        let t = Instant::now();
        let mut doc = pdfium.create_new_pdf()?;
        let a = pdfium.load_pdf_from_file(&src, None)?;
        let b = pdfium.load_pdf_from_file(&merge_src, None)?;
        let r1 = doc.pages_mut().append(&a);
        let r2 = doc.pages_mut().append(&b);
        let path = out.join("merge_new.pdf");
        doc.save_to_file(&path)?;
        let e = ms(t.elapsed());
        drop(a);
        drop(b);
        drop(doc);
        let err = match (r1, r2) {
            (Ok(_), Ok(_)) => None,
            (x, y) => Some(format!("{:?} {:?}", x.err(), y.err())),
        };
        record("merge: new document <- structure + merge_source", e, &path, err)?;
    }
    // extract pages 2-4 (index 1..=3) into new document
    {
        let t = Instant::now();
        let mut doc = pdfium.create_new_pdf()?;
        let a = pdfium.load_pdf_from_file(&src, None)?;
        let r = doc.pages_mut().copy_page_range_from_document(&a, 1..=3, 0);
        let path = out.join("extract_p2-4.pdf");
        doc.save_to_file(&path)?;
        let e = ms(t.elapsed());
        drop(a);
        drop(doc);
        record("extract p2-4 into new document", e, &path, r.err().map(|e| format!("{e:?}")))?;
    }
    // split into p1-3 and p4-6
    for (label, range) in [("split_a_p1-3", 0..=2), ("split_b_p4-6", 3..=5)] {
        let t = Instant::now();
        let mut doc = pdfium.create_new_pdf()?;
        let a = pdfium.load_pdf_from_file(&src, None)?;
        let r = doc.pages_mut().copy_page_range_from_document(&a, range, 0);
        let path = out.join(format!("{label}.pdf"));
        doc.save_to_file(&path)?;
        let e = ms(t.elapsed());
        drop(a);
        drop(doc);
        record(label, e, &path, r.err().map(|e| format!("{e:?}")))?;
    }

    let result = json!({
        "spike": "RS-05 (PDFium part)",
        "input": src.file_name().unwrap().to_string_lossy(),
        "merge_source": merge_src.file_name().unwrap().to_string_lossy(),
        "operations": ops,
    });
    write_json(&out.join("result_pdfium.json"), &result)?;
    Ok(result)
}

// ---------- describe: PDFium as an independent reader for outputs of other engines ----------
fn field_json(field: &PdfFormField) -> Value {
    let mut v = json!({"name": field.name(), "type": format!("{:?}", field.field_type())});
    if let Some(t) = field.as_text_field() {
        v["value"] = json!(t.value());
    } else if let Some(c) = field.as_checkbox_field() {
        v["checked"] = json!(c.is_checked().ok());
    } else if let Some(r) = field.as_radio_button_field() {
        v["checked"] = json!(r.is_checked().ok());
    } else if let Some(c) = field.as_combo_box_field() {
        v["value"] = json!(c.value());
    }
    v
}

fn describe(pdfium: &Pdfium, input: &Path, out_json: &Path, render_dir: Option<&Path>) -> Res<Value> {
    let doc = match pdfium.load_pdf_from_file(input, None) {
        Ok(d) => d,
        Err(e) => {
            let v = json!({"input": input.to_string_lossy(), "load_error": format!("{e:?}")});
            write_json(out_json, &v)?;
            return Ok(v);
        }
    };
    let stem = input.file_stem().unwrap().to_string_lossy().to_string();
    let mut pages = vec![];
    for (i, page) in doc.pages().iter().enumerate() {
        let mut annots = vec![];
        let mut fields = vec![];
        let trace = std::env::var("SPIKE_TRACE").is_ok();
        for (ai, a) in page.annotations().iter().enumerate() {
            if trace { eprintln!("p{i} a{ai} type"); }
            let atype = format!("{:?}", a.annotation_type());
            if trace { eprintln!("p{i} a{ai} {atype} form_field"); }
            if let Some(f) = a.as_form_field() {
                fields.push(field_json(f));
            }
            if trace { eprintln!("p{i} a{ai} {atype} bounds"); }
            let bounds = a.bounds().map(|r| rect_json(&r)).unwrap_or(json!(null));
            if trace { eprintln!("p{i} a{ai} {atype} contents"); }
            let contents = a.contents();
            // stroke_color() TIDAK dipanggil: pada pdfium-render 0.9.4 + PDFium 7881 panggilan ini
            // menyebabkan access violation untuk anotasi Text yang sudah memiliki /AP (temuan spike).
            annots.push(json!({"type": atype, "bounds": bounds, "contents": contents}));
        }
        if trace { eprintln!("p{i} links"); }
        let mut links = vec![];
        for l in page.links().iter() {
            links.push(json!({
                "dest_page_index": l.destination().and_then(|d| d.page_index().ok()),
                "has_action": l.action().is_some(),
            }));
        }
        if let Some(dir) = render_dir {
            fs::create_dir_all(dir)?;
            for (suffix, with) in [("annots", true), ("noannots", false)] {
                let img = page
                    .render_with_config(
                        &PdfRenderConfig::new().scale_page_by_factor(2.0).render_annotations(with).render_form_data(with),
                    )?
                    .as_image()?;
                img.save(dir.join(format!("{stem}_p{i}_{suffix}.png")))?;
            }
        }
        pages.push(json!({
            "index": i,
            "width": page.width().value,
            "height": page.height().value,
            "rotation": rotation_deg(&page),
            "text": page.text().map(|t| t.all()).unwrap_or_default(),
            "annotations": annots,
            "form_fields": fields,
            "links": links,
        }));
    }
    let bookmarks: Vec<Value> = doc
        .bookmarks()
        .iter()
        .map(|b| json!({"title": b.title(), "dest_page_index": b.destination().and_then(|d| d.page_index().ok())}))
        .collect();
    let signatures: Vec<Value> = doc
        .signatures()
        .iter()
        .map(|s| json!({"contents_bytes": s.bytes().len(), "reason": s.reason(), "signing_date": s.signing_date()}))
        .collect();
    let v = json!({
        "input": input.file_name().unwrap().to_string_lossy(),
        "reader": "PDFium chromium/7881 via pdfium-render 0.9.4",
        "page_count": doc.pages().len(),
        "has_form": doc.form().is_some(),
        "bookmarks": bookmarks,
        "signatures": signatures,
        "pages": pages,
    });
    write_json(out_json, &v)?;
    Ok(v)
}

fn main() -> Res<()> {
    let args: Vec<String> = std::env::args().collect();
    let cmd = args.get(1).map(|s| s.as_str()).unwrap_or("all");
    if cmd == "describe" {
        let input = PathBuf::from(args.get(2).ok_or("usage: describe <in.pdf> <out.json> [render_dir]")?);
        let out = PathBuf::from(args.get(3).ok_or("usage: describe <in.pdf> <out.json> [render_dir]")?);
        let render = args.get(4).map(PathBuf::from);
        let exe_dir = std::env::current_exe()?.parent().unwrap().to_path_buf();
        let lib_dir = std::env::var("PDFIUM_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|_| exe_dir.join("..").join("..").join("..").join("deps").join("pdfium").join("chromium-7881").join("bin"));
        let pdfium = Pdfium::new(Pdfium::bind_to_library(Pdfium::pdfium_platform_library_name_at_path(&lib_dir))?);
        describe(&pdfium, &input, &out, render.as_deref())?;
        return Ok(());
    }
    let root = std::env::current_dir()?;
    let manifest_path = root.join("fixtures").join("generated").join("manifest.json");
    let manifest: Value = serde_json::from_str(&fs::read_to_string(&manifest_path)?)?;
    let ctx = Ctx { root: root.clone(), manifest };

    let lib_dir = root.join("deps").join("pdfium").join("chromium-7881").join("bin");
    let lib = Pdfium::pdfium_platform_library_name_at_path(&lib_dir);
    let t_init = Instant::now();
    // Two bindings to the same DLL: one owned by Pdfium (high-level API), one kept for raw FFI.
    let raw = Pdfium::bind_to_library(&lib)?;
    let pdfium = Pdfium::new(Pdfium::bind_to_library(&lib)?);
    let init_ms = ms(t_init.elapsed());

    let mut summary = json!({"command": cmd, "pdfium_dll": lib.to_string_lossy()});
    if cmd == "rs01" || cmd == "all" {
        let r = rs01(&pdfium, &ctx, init_ms)?;
        summary["rs01_text_mismatch_fixtures"] = json!(r["fixtures"].as_array().map(|a| a.iter().filter(|f| !f["text_mismatches"].as_array().map(|m| m.is_empty()).unwrap_or(true)).count()));
    }
    if cmd == "rs02" || cmd == "all" {
        let r = rs02(&pdfium, raw.as_ref(), &ctx)?;
        summary["rs02_created"] = json!(r["created"].as_array().map(|a| a.len()));
        summary["rs02_errors"] = r["creation_errors"].clone();
    }
    if cmd == "rs03" || cmd == "all" {
        let r = rs03(&pdfium, &ctx)?;
        summary["rs03_actions"] = r["actions"].clone();
    }
    if cmd == "rs05" || cmd == "all" {
        let r = rs05(&pdfium, raw.as_ref(), &ctx)?;
        summary["rs05_ops"] = json!(r["operations"].as_array().map(|a| a.len()));
    }
    println!("{}", serde_json::to_string_pretty(&summary)?);
    Ok(())
}
