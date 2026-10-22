"""Spike pembandingan MuPDF (via PyMuPDF yang sudah ada di .venv) — BUKAN kode produksi.

Menjalankan operasi yang sama dengan spike PDFium/PDFBox pada fixture yang sama:
RS-02 anotasi, RS-03 isi form, RS-04 buat field, RS-05 merge/extract, RS-07 redaksi,
RS-08 penelusuran API signing (tanpa implementasi kriptografi).

Jalankan dari experiments/restart:
    ..\\..\\.venv\\Scripts\\python.exe mupdf-spike\\run_mupdf.py
Output: raw/compare/mupdf/*.pdf + raw/compare/mupdf/result.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pymupdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "fixtures" / "generated"
OUT = ROOT / "raw" / "compare" / "mupdf"
ENGINE = "MuPDF"


def mu_rect(page: pymupdf.Page, pdf_rect: list[float]) -> pymupdf.Rect:
    l, b, r, t = pdf_rect
    h = page.rect.height
    return pymupdf.Rect(l, h - t, r, h - b)


def rs02(manifest: dict) -> dict:
    fx = manifest["fixtures"]["rs02_annot_base"]
    doc = pymupdf.open(GEN / fx["file"])
    created, errors = [], []

    def note(page_no: int, kind: str, pdf_rect: list[float], fn):
        try:
            annot = fn()
            annot.set_info(content=f"RS02-{kind}")
            annot.update()
            created.append({"page": page_no, "kind": kind, "via": "PyMuPDF", "rect": pdf_rect, "contents": f"RS02-{kind}"})
        except Exception as e:  # noqa: BLE001
            errors.append({"page": page_no, "kind": kind, "error": f"{type(e).__name__}: {e}"})

    p1 = doc[1]
    colors = {"highlight": (1, 0.9, 0), "underline": (0, 0.47, 1), "strikeout": (0.86, 0, 0), "squiggly": (0, 0.63, 0.24)}
    adders = {"highlight": p1.add_highlight_annot, "underline": p1.add_underline_annot,
              "strikeout": p1.add_strikeout_annot, "squiggly": p1.add_squiggly_annot}
    for kind, rect in fx["markup_targets_pdf_rect"].items():
        def mk(kind=kind, rect=rect):
            a = adders[kind](mu_rect(p1, rect))
            a.set_colors(stroke=colors[kind])
            return a
        note(1, kind, rect, mk)

    p0 = doc[0]
    items = {
        "text": ([60, 700, 84, 724], lambda r: p0.add_text_annot(r.tl, "RS02-text")),
        "freetext": ([120, 690, 320, 730], lambda r: p0.add_freetext_annot(r, "RS02-freetext", fontsize=10)),
        "square": ([60, 560, 200, 660], lambda r: p0.add_rect_annot(r)),
        "circle": ([240, 560, 360, 660], lambda r: p0.add_circle_annot(r)),
        "stamp": ([380, 560, 540, 640], lambda r: p0.add_stamp_annot(r, stamp=0)),
        "ink": ([60, 420, 300, 520], lambda r: p0.add_ink_annot(
            [[(r.x0 + 20 * k, r.y1 - 30 - (0 if k % 2 == 0 else 40)) for k in range(12)]])),
        # CR-08 (tidak dapat dibuat PDFium)
        "line": ([320, 420, 540, 470], lambda r: p0.add_line_annot(r.tl, r.br)),
        "polygon": ([60, 300, 200, 400], lambda r: p0.add_polygon_annot([r.tl, r.tr, (r.x1, r.y1), (r.x0 + 30, r.y1)])),
        "polyline": ([240, 300, 380, 400], lambda r: p0.add_polyline_annot([r.tl, (r.x0 + 70, r.y1), r.tr])),
        "caret": ([420, 330, 440, 350], lambda r: p0.add_caret_annot(r.tl)),
    }
    for kind, (rect, fn) in items.items():
        note(0, kind, rect, lambda rect=rect, fn=fn: fn(mu_rect(p0, rect)))
    out = OUT / "rs02_annotated.pdf"
    doc.save(out, garbage=3, deflate=True)
    doc.close()
    return {"output": out.name, "created": created, "errors": errors}


def rs03(manifest: dict) -> dict:
    doc = pymupdf.open(GEN / manifest["fixtures"]["rs03_form"]["file"])
    actions = []
    for w in doc[0].widgets():
        try:
            if w.field_name == "nama":
                w.field_value = f"Diisi {ENGINE} RS03"
            elif w.field_name == "setuju":
                w.field_value = w.on_state()
            elif w.field_name == "pilihan":
                w.field_value = w.on_state() if w.on_state() == "B" else "Off"
            elif w.field_name == "kota":
                w.field_value = "Surabaya"
            w.update()
            actions.append({"field": w.field_name, "on_state": w.on_state() if w.field_type in (2, 5) else None, "ok": True})
        except Exception as e:  # noqa: BLE001
            actions.append({"field": w.field_name, "ok": False, "error": f"{type(e).__name__}: {e}"})
    out = OUT / "rs03_filled.pdf"
    doc.save(out, garbage=3, deflate=True)
    doc.close()
    return {"output": out.name, "actions": actions}


def rs04() -> dict:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 60), "RS04 field authoring", fontname="helv", fontsize=12)
    errors = []
    try:
        w = pymupdf.Widget()
        w.field_type, w.field_name, w.rect, w.field_value = pymupdf.PDF_WIDGET_TYPE_TEXT, "rs04_text", pymupdf.Rect(50, 100, 300, 124), "awal"
        page.add_widget(w)
        w = pymupdf.Widget()
        w.field_type, w.field_name, w.rect, w.field_value = pymupdf.PDF_WIDGET_TYPE_CHECKBOX, "rs04_check", pymupdf.Rect(50, 140, 66, 156), False
        page.add_widget(w)
    except Exception as e:  # noqa: BLE001
        errors.append(f"{type(e).__name__}: {e}")
    out = OUT / "rs04_fields.pdf"
    doc.save(out, garbage=3, deflate=True)
    doc.close()
    return {"output": out.name, "errors": errors}


def rs05(manifest: dict) -> dict:
    fx = manifest["fixtures"]["rs05_structure"]
    src_path, extra_path = GEN / fx["file"], GEN / fx["merge_source"]
    res = []
    # merge in-place (dokumen sumber dibuka, lalu ditambah)
    t = time.perf_counter()
    doc = pymupdf.open(src_path)
    doc.insert_pdf(pymupdf.open(extra_path))
    out = OUT / "rs05_merge.pdf"
    doc.save(out, garbage=3, deflate=True)
    doc.close()
    res.append({"op": "merge (open structure + insert_pdf merge_source)", "output": out.name, "ms": round((time.perf_counter() - t) * 1000, 2)})
    # extract p2-4 ke dokumen baru, outline dipetakan ulang lewat set_toc
    t = time.perf_counter()
    src = pymupdf.open(src_path)
    new = pymupdf.open()
    new.insert_pdf(src, from_page=1, to_page=3)
    toc = [[lvl, title, p - 1] for lvl, title, p in src.get_toc(simple=True) if 2 <= p <= 4]
    if toc and toc[0][0] != 1:
        toc = [[1, e[1], e[2]] if i == 0 else e for i, e in enumerate(toc)]
    try:
        new.set_toc(toc)
        toc_note = "set_toc dengan pemetaan ulang (API)"
    except Exception as e:  # noqa: BLE001
        toc_note = f"set_toc gagal: {e}"
    out = OUT / "rs05_extract_p2-4.pdf"
    new.save(out, garbage=3, deflate=True)
    new.close()
    res.append({"op": "extract p2-4 (insert_pdf ke dokumen baru + set_toc)", "output": out.name, "toc_note": toc_note,
                "ms": round((time.perf_counter() - t) * 1000, 2)})
    return {"operations": res}


def rs07(manifest: dict) -> dict:
    fx = manifest["fixtures"]["rs07_redact"]
    out_files = {}
    for variant in ("apply_only", "apply_plus_scrub"):
        doc = pymupdf.open(GEN / fx["file"])
        page = doc[0]
        for rect in fx["areas_mupdf"].values():
            page.add_redact_annot(pymupdf.Rect(rect), fill=(0, 0, 0))
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_PIXELS,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)
        if variant == "apply_plus_scrub":
            # kanal di luar content stream: anotasi di area, nilai field, metadata
            for a in list(page.annots()):
                if any(a.rect.intersects(pymupdf.Rect(r)) for r in fx["areas_mupdf"].values()):
                    page.delete_annot(a)
            doc.scrub(metadata=True, xml_metadata=True, reset_fields=True, hidden_text=True,
                      javascript=True, attached_files=True, embedded_files=True, thumbnails=True)
        out = OUT / f"rs07_redacted_{variant}.pdf"
        doc.save(out, garbage=4, deflate=True, clean=True)
        doc.close()
        out_files[variant] = out.name
    return {"outputs": out_files,
            "notes": ["apply_redactions menghapus konten halaman di area (teks, gambar piksel, vektor)",
                      "anotasi non-redaksi, nilai field, dan metadata TIDAK disentuh apply_redactions; varian kedua memakai delete_annot + scrub()"]}


def rs08_review() -> dict:
    m = pymupdf.mupdf
    names = [n for n in dir(m) if "sign" in n.lower() and ("pkcs7" in n.lower() or n.startswith("pdf_sign") or "signer" in n.lower())]
    doc_api = [n for n in dir(pymupdf.Document) if "sig" in n.lower()]
    return {"pymupdf_document_api_with_sig": doc_api, "low_level_mupdf_symbols_sample": sorted(names)[:40],
            "note": "Penelusuran saja; tidak ada implementasi signing dalam spike ini."}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((GEN / "manifest.json").read_text(encoding="utf-8"))
    result = {"engine": f"{ENGINE} via PyMuPDF {pymupdf.VersionBind}",
              "rs02": rs02(manifest), "rs03": rs03(manifest), "rs04": rs04(),
              "rs05": rs05(manifest), "rs07": rs07(manifest), "rs08_review": rs08_review()}
    (OUT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: (v if k in ("engine",) else "ok") for k, v in result.items()}, ensure_ascii=False))
    print("rs02 errors:", result["rs02"]["errors"])
    print("rs03 actions:", result["rs03"]["actions"])
    print("rs04 errors:", result["rs04"]["errors"])
    print("rs08 review:", result["rs08_review"]["pymupdf_document_api_with_sig"], result["rs08_review"]["low_level_mupdf_symbols_sample"][:15])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
