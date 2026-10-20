"""Spike 02 - Anotasi, form, redaction, tanda tangan gambar, watermark.

Output: spikes/out/spike_02_annotate.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pymupdf

OUT = Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)
FIX = Path(__file__).parent / "fixtures"
FIX.mkdir(parents=True, exist_ok=True)

results: dict = {"spike": "02_annotate", "pymupdf": pymupdf.__version__}


def make_source(path: Path) -> Path:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 100), "CONFIDENTIAL PAYLOAD 9999", fontsize=16, fontname="helv")
    page.insert_text((72, 140), "Public body text that must survive redaction.", fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()
    return path


def s1_annotations(src: Path) -> None:
    doc = pymupdf.open(src)
    page = doc[0]
    hits = page.search_for("CONFIDENTIAL PAYLOAD 9999")
    added = {}
    try:
        page.add_highlight_annot(hits[0])
        added["highlight"] = True
    except Exception as exc:  # noqa: BLE001
        added["highlight"] = f"ERROR: {exc}"
    try:
        page.add_text_annot((100, 200), "Catatan UniPDF", icon="Note")
        added["text_note"] = True
    except Exception as exc:  # noqa: BLE001
        added["text_note"] = f"ERROR: {exc}"
    try:
        page.add_freetext_annot(pymupdf.Rect(72, 240, 400, 280), "Overlay text", fontsize=14)
        added["freetext"] = True
    except Exception as exc:  # noqa: BLE001
        added["freetext"] = f"ERROR: {exc}"
    try:
        page.draw_rect(pymupdf.Rect(300, 300, 420, 380), color=(1, 0, 0), width=2)
        page.draw_circle((480, 340), 40, color=(0, 0.6, 0), width=2)
        added["vector_shapes"] = True
    except Exception as exc:  # noqa: BLE001
        added["vector_shapes"] = f"ERROR: {exc}"
    doc.save(OUT / "s1_annotated.pdf")
    doc.close()

    # verifikasi reopen
    d = pymupdf.open(OUT / "s1_annotated.pdf")
    types = sorted({a.type[1] for a in d[0].annots()}) if d[0].first_annot else []
    count = sum(1 for _ in d[0].annots()) if d[0].first_annot else 0
    d.close()
    results["s1_annotations"] = {
        "added": added,
        "annot_count_after_reopen": count,
        "annot_types": types,
        "annot_type_names": {"8": "Highlight", "6": "Text(Note)", "1": "FreeText"},
    }


def s2_forms(src: Path) -> None:
    doc = pymupdf.open(src)
    page = doc[0]
    errors = []
    try:
        w = pymupdf.Widget()
        w.field_name = "nama_lengkap"
        w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        w.field_value = "Awal"
        w.rect = pymupdf.Rect(72, 320, 320, 350)
        w.text_font = "Helv"
        try:
            w.text_fontsize = 12
        except Exception:  # noqa: BLE001
            pass
        page.add_widget(w)

        cb = pymupdf.Widget()
        cb.field_name = "setuju"
        cb.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
        cb.rect = pymupdf.Rect(72, 360, 92, 380)
        cb.field_value = False
        page.add_widget(cb)
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))

    doc.save(OUT / "s2_form_created.pdf")
    doc.close()

    # isi ulang lalu simpan
    d = pymupdf.open(OUT / "s2_form_created.pdf")
    filled = {}
    for w in d[0].widgets():
        if w.field_name == "nama_lengkap":
            w.field_value = "Diisi Uji"
            w.update()
            filled["nama_lengkap"] = w.field_value
        if w.field_name == "setuju":
            w.field_value = True
            w.update()
            filled["setuju"] = w.field_value
    d.save(OUT / "s2_form_filled.pdf")
    d.close()

    d2 = pymupdf.open(OUT / "s2_form_filled.pdf")
    reread = {w.field_name: str(w.field_value) for w in d2[0].widgets()}
    d2.close()

    # Checkbox pada state "on" diekspor sebagai label on-state (default "Yes"),
    # bukan boolean Python -> normalisasi saat pembanding.
    def _checkbox_on(value: str) -> bool:
        return value.strip().lower() in {"yes", "true", "1", "on"}

    results["s2_forms"] = {
        "create_errors": errors,
        "filled": filled,
        "reread_after_reopen": reread,
        "text_field_ok": reread.get("nama_lengkap") == "Diisi Uji",
        "checkbox_ok": _checkbox_on(reread.get("setuju", "")),
        "roundtrip_ok": reread.get("nama_lengkap") == "Diisi Uji" and _checkbox_on(reread.get("setuju", "")),
    }


def s3_redaction(src: Path) -> None:
    doc = pymupdf.open(src)
    page = doc[0]
    hits = page.search_for("CONFIDENTIAL PAYLOAD 9999")
    n_hits = len(hits)
    for r in hits:
        page.add_redact_annot(r, fill=(0, 0, 0))
    apply_args = dict(images=pymupdf.PDF_REDACT_IMAGE_PIXELS, graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED)
    try:
        page.apply_redactions(**apply_args)
        apply_ok = True
        apply_err = None
    except Exception as exc:  # noqa: BLE001
        apply_ok = False
        apply_err = str(exc)
    doc.save(OUT / "s3_redacted.pdf")
    doc.close()

    d = pymupdf.open(OUT / "s3_redacted.pdf")
    text_after = d[0].get_text()
    d.close()
    leaked = "CONFIDENTIAL PAYLOAD 9999" in text_after
    results["s3_redaction"] = {
        "search_hits": n_hits,
        "apply_ok": apply_ok,
        "apply_error": apply_err,
        "secret_still_extractable": leaked,
        "body_text_preserved": "Public body text" in text_after,
        "text_after_len": len(text_after),
    }


def s4_image_and_stamp(src: Path) -> None:
    # siapkan gambar PNG
    from PIL import Image

    img_path = OUT / "s4_logo.png"
    Image.new("RGB", (240, 80), (12, 90, 200)).save(img_path)

    doc = pymupdf.open(src)
    page = doc[0]
    errors = []
    try:
        page.insert_image(pymupdf.Rect(300, 320, 480, 380), filename=str(img_path))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"image: {exc}")
    try:
        page.insert_text((400, 250), "WATERMARK", fontsize=28, fontname="helv",
                         color=(0.85, 0.85, 0.85), rotate=0)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"watermark: {exc}")
    # header/footer + page number
    try:
        page.insert_text((72, 810), "Footer teks - hal. 1", fontsize=9, fontname="helv")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"footer: {exc}")
    doc.save(OUT / "s4_stamped.pdf")
    doc.close()

    d = pymupdf.open(OUT / "s4_stamped.pdf")
    imgs = d[0].get_images(full=True)
    txt = d[0].get_text()
    d.close()
    results["s4_image_stamp"] = {
        "errors": errors,
        "image_count": len(imgs),
        "watermark_text_present": "WATERMARK" in txt,
        "footer_present": "Footer teks" in txt,
    }


def s5_page_range_and_export() -> None:
    """Ekspor halaman ke PNG (mirip fitur 'PDF ke gambar')."""
    doc = pymupdf.open(FIX / "fixture_12p.pdf")
    times = []
    for i in range(min(6, doc.page_count)):
        t0 = time.perf_counter()
        pix = doc[i].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
        pix.save(OUT / f"s5_page{i + 1}.png")
        times.append((time.perf_counter() - t0) * 1000)
    doc.close()
    results["s5_export_png"] = {
        "pages_exported": len(times),
        "ms_per_page_max": round(max(times), 2) if times else None,
        "ms_per_page_median": round(sorted(times)[len(times) // 2], 2) if times else None,
    }


def main() -> int:
    src = FIX / "annotate_source.pdf"
    if not src.exists():
        make_source(src)
    s1_annotations(src)
    s2_forms(src)
    s3_redaction(src)
    s4_image_and_stamp(src)
    s5_page_range_and_export()
    (OUT / "spike_02_annotate.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
