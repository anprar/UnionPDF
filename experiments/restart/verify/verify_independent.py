"""Verifikasi independen output spike PDFium memakai PyMuPDF (pembaca kedua) + Pillow.

Jalankan dari experiments/restart:
    ..\\..\\.venv\\Scripts\\python.exe verify\\verify_independent.py

Menulis raw/<rs>/verify_independent.json dan mencetak ringkasan PASS/FAIL per kriteria.
Kriteria & ambang ditetapkan di README.md sebelum skrip ini dijalankan.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageChops, ImageStat

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "fixtures" / "generated"
RAW = ROOT / "raw"
MAD_MAX = 10.0
ANNOT_VISIBLE_MIN = 0.01
DIFF_PIXEL = 16


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def warnings_and_repair(doc: pymupdf.Document) -> dict:
    return {"is_repaired": bool(doc.is_repaired), "mupdf_warnings": pymupdf.TOOLS.mupdf_warnings()}


def render_pymupdf(page: pymupdf.Page, scale: float, annots: bool = True) -> Image.Image:
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), annots=annots, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def gray(img: Image.Image) -> Image.Image:
    return img.convert("L")


def mad(a: Image.Image, b: Image.Image) -> tuple[float, float]:
    if a.size != b.size:
        b = b.resize(a.size)
    d = ImageChops.difference(gray(a), gray(b))
    mean = ImageStat.Stat(d).mean[0]
    hist = d.histogram()
    over = sum(hist[65:]) / (a.size[0] * a.size[1])
    return round(mean, 3), round(over * 100, 3)


def region_diff_fraction(a: Image.Image, b: Image.Image, box: tuple[int, int, int, int]) -> float:
    ca, cb = gray(a).crop(box), gray(b).crop(box)
    d = ImageChops.difference(ca, cb)
    hist = d.histogram()
    total = max(1, ca.size[0] * ca.size[1])
    return round(sum(hist[DIFF_PIXEL + 1:]) / total, 4)


def pdf_rect_to_box(rect: list[float], page_h: float, scale: float, pad: float = 2.0) -> tuple[int, int, int, int]:
    l, b, r, t = rect
    return (int((l - pad) * scale), int((page_h - t - pad) * scale), int((r + pad) * scale), int((page_h - b + pad) * scale))


def norm(s: str) -> str:
    return " ".join(s.split())


def _split_top_level(array_src: str) -> list[str]:
    """Pisahkan isi array PDF menjadi elemen top-level: kamus '<<...>>' atau referensi 'N G R'."""
    items, i, n = [], 0, len(array_src)
    s = array_src.strip()
    if s.startswith("["):
        s = s[1:]
    if s.endswith("]"):
        s = s[:-1]
    n = len(s)
    while i < n:
        if s.startswith("<<", i):
            depth, j = 0, i
            while j < n:
                if s.startswith("<<", j):
                    depth += 1
                    j += 2
                elif s.startswith(">>", j):
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            items.append(s[i:j])
            i = j
        elif s[i].isdigit():
            j = i
            while j < n and s[j] != "R":
                j += 1
            items.append(s[i:j + 1].strip())
            i = j + 1
        else:
            i += 1
    return items


def raw_annots(doc: pymupdf.Document, page: pymupdf.Page) -> list[dict]:
    """Baca /Annots apa adanya, termasuk kamus langsung (yang tidak bisa dimuat API anotasi PyMuPDF)."""
    import re
    t, v = doc.xref_get_key(page.xref, "Annots")
    if t == "xref":
        v = doc.xref_object(int(v.split()[0]), compressed=True)
    elif t != "array":
        return []
    out = []
    for item in _split_top_level(v):
        indirect = item.endswith("R") and not item.startswith("<<")
        src = doc.xref_object(int(item.split()[0]), compressed=True) if indirect else item
        sub = re.search(r"/Subtype\s*/(\w+)", src)
        cont = re.search(r"/Contents\s*\(([^)]*)\)", src)
        rect = re.search(r"/Rect\s*\[([^\]]*)\]", src)
        out.append({"indirect_object": indirect, "subtype": sub.group(1) if sub else None,
                    "contents": cont.group(1) if cont else None,
                    "rect": [float(x) for x in rect.group(1).split()] if rect else None,
                    "has_AP": "/AP" in src, "has_InkList": "/InkList" in src,
                    "has_QuadPoints": "/QuadPoints" in src})
    return out


# ---------------------------------------------------------------- inputs
def check_inputs(manifest: dict) -> dict:
    out = {}
    for name, info in manifest["files"].items():
        out[name] = {"sha256_manifest": info["sha256"], "sha256_now": sha256(GEN / name)}
        out[name]["unchanged"] = out[name]["sha256_manifest"] == out[name]["sha256_now"]
    return out


# ---------------------------------------------------------------- RS-01
def verify_rs01(manifest: dict) -> dict:
    res = json.loads((RAW / "rs01" / "result_pdfium.json").read_text(encoding="utf-8"))
    pages_out = []
    for f in res["fixtures"]:
        doc = pymupdf.open(GEN / f["fixture"])
        for pd in f["pages_detail"]:
            i = pd["page"]
            pdfium_png = Image.open(RAW / "rs01" / pd["png_x2"]).convert("RGB")
            mu = render_pymupdf(doc[i], 2.0)
            m, over = mad(pdfium_png, mu)
            pages_out.append({"fixture": f["fixture"], "page": i, "size_pdfium": list(pdfium_png.size),
                              "size_pymupdf": list(mu.size), "gray_mad": m, "pct_pixels_diff_gt_64": over,
                              "match": m <= MAD_MAX})
        doc.close()
    # klasifikasi mismatch teks: bandingkan dengan ekstraksi PyMuPDF
    text_class = []
    for f in res["fixtures"]:
        for mm in f["text_mismatches"]:
            doc = pymupdf.open(GEN / f["fixture"])
            mu_text = doc[mm["page"]].get_text("text")
            doc.close()
            for miss in mm["missing"]:
                import unicodedata
                nf = lambda s: unicodedata.normalize("NFKC", norm(s))  # noqa: E731
                mu_has = nf(miss) in nf(mu_text)
                text_class.append({
                    "fixture": f["fixture"], "page": mm["page"], "expected": miss,
                    "pdfium_matches_after_nfkc": nf(miss) in nf(mm["extracted"]),
                    "pymupdf_extracts_expected": mu_has,
                    "pymupdf_line": next((l for l in mu_text.splitlines() if l.split(":")[0] == miss.split(":")[0]), None),
                    "pdfium_line": next((l for l in mm["extracted"].splitlines() if l.split(":")[0] == miss.split(":")[0]), None),
                })
    return {"render_compare": pages_out,
            "render_all_match": all(p["match"] for p in pages_out),
            "text_mismatch_classification": text_class}


# ---------------------------------------------------------------- RS-02
def verify_rs02(manifest: dict) -> dict:
    res = json.loads((RAW / "rs02" / "result_pdfium.json").read_text(encoding="utf-8"))
    out_pdf = RAW / "rs02" / "annotated.pdf"
    pymupdf.TOOLS.mupdf_warnings()  # reset
    doc = pymupdf.open(out_pdf)
    state = warnings_and_repair(doc)
    annots = []
    api_load = []
    for page in doc:
        for a in raw_annots(doc, page):
            a["page"] = page.number
            annots.append(a)
        # Bisakah API anotasi PyMuPDF memuat tiap entri?
        for xref, atype, _ in page.annot_xrefs():
            try:
                loaded = page.load_annot(xref) is not None if xref else False
            except Exception:
                loaded = False
            api_load.append({"page": page.number, "xref": xref, "type_code": atype, "loadable_by_pymupdf_annot_api": loaded})
    # visibilitas: PDFium (render dg/tanpa anotasi) dan PyMuPDF (annots True/False)
    vis = []
    for c in res["created"]:
        pg = doc[c["page"]]
        h = pg.rect.height
        box = pdf_rect_to_box(c["rect"], h, 2.0)
        p_with = Image.open(RAW / "rs02" / f"annotated_p{c['page']}_annots_x2.png").convert("RGB")
        p_without = Image.open(RAW / "rs02" / f"annotated_p{c['page']}_noannots_x2.png").convert("RGB")
        m_with, m_without = render_pymupdf(pg, 2.0, True), render_pymupdf(pg, 2.0, False)
        fp, fm = region_diff_fraction(p_with, p_without, box), region_diff_fraction(m_with, m_without, box)
        found = next((a for a in annots if a["contents"] == c["contents"]), None)
        vis.append({"kind": c["kind"], "via": c["via"], "page": c["page"],
                    "visible_pdfium": fp, "visible_pymupdf": fm,
                    "visible_both": fp >= ANNOT_VISIBLE_MIN and fm >= ANNOT_VISIBLE_MIN,
                    "present_in_file": found is not None,
                    "subtype_in_file": found["subtype"] if found else None,
                    "indirect_object": found["indirect_object"] if found else None,
                    "has_AP_in_file": found["has_AP"] if found else None,
                    "has_InkList": found["has_InkList"] if found else None})
    doc.close()
    return {"structure": state, "annotations_raw": annots, "pymupdf_annot_api_load": api_load, "visibility": vis}


# ---------------------------------------------------------------- RS-03
def verify_rs03(manifest: dict) -> dict:
    import re
    pymupdf.TOOLS.mupdf_warnings()
    doc = pymupdf.open(RAW / "rs03" / "filled.pdf")
    state = warnings_and_repair(doc)
    # Pemeriksaan objek mentah (tidak butuh load_page).
    raw = []
    t, v = doc.xref_get_key(doc.page_xref(0), "Annots")
    for r in re.findall(r"(\d+) 0 R", v):
        x = int(r)
        entry = {"xref": x, "T": doc.xref_get_key(x, "T")[1], "FT": doc.xref_get_key(x, "FT")[1],
                 "AS": list(doc.xref_get_key(x, "AS")), "V": list(doc.xref_get_key(x, "V"))}
        if entry["FT"] == "/Tx":
            n = doc.xref_get_key(x, "AP/N")
            if n[0] == "xref":
                entry["text_AP_contains_new_value"] = b"Diisi PDFium RS03" in (doc.xref_stream(int(n[1].split()[0])) or b"")
        entry["AS_is_name"] = entry["AS"][0] in ("name", "null")
        raw.append(entry)
    acroform = doc.xref_get_key(doc.pdf_catalog(), "AcroForm")
    try:
        page_widgets = [{"name": w.field_name, "value": w.field_value} for w in doc[0].widgets()]
        page_load_error = None
    except Exception as e:  # pembaca independen gagal memuat halaman
        page_widgets, page_load_error = None, f"{type(e).__name__}: {e}"
    doc.close()
    return {"structure": state, "raw_widgets": raw, "acroform": list(acroform),
            "pymupdf_page_load_error": page_load_error, "pymupdf_widgets": page_widgets}


def _unused_verify_rs03_page_api(doc):  # dipertahankan sebagai referensi, tidak dipanggil
    widgets = []
    for w in doc[0].widgets():
        ap_has_value = None
        if w.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:
            n = doc.xref_get_key(w.xref, "AP/N")
            if n[0] == "xref":
                stream = doc.xref_stream(int(n[1].split()[0])) or b""
                ap_has_value = b"Diisi PDFium RS03" in stream
        widgets.append({"name": w.field_name, "type": w.field_type_string, "value": w.field_value,
                        "on_state": w.on_state() if w.field_type in (pymupdf.PDF_WIDGET_TYPE_CHECKBOX, pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON) else None,
                        "AS": doc.xref_get_key(w.xref, "AS")[1],
                        "text_AP_contains_new_value": ap_has_value})
    doc.close()
    return {"structure": state, "widgets_pymupdf": widgets}


# ---------------------------------------------------------------- RS-05
EXPECTED_ORDER = {
    "rotate.pdf": [1, 2, 3, 4, 5, 6],
    "delete.pdf": [1, 2, 3, 4, 6],
    "reorder.pdf": [6, 1, 2, 3, 4, 5],
    "insert_blank.pdf": [1, 2, None, 3, 4, 5, 6],
    "merge_append.pdf": [1, 2, 3, 4, 5, 6, "m1", "m2"],
    "merge_new.pdf": [1, 2, 3, 4, 5, 6, "m1", "m2"],
    "extract_p2-4.pdf": [2, 3, 4],
    "split_a_p1-3.pdf": [1, 2, 3],
    "split_b_p4-6.pdf": [4, 5, 6],
}
IN_PLACE = {"rotate.pdf", "delete.pdf", "reorder.pdf", "insert_blank.pdf", "merge_append.pdf"}


def page_label(text: str):
    t = norm(text)
    if "RS05 structure page" in t:
        return int(t.split("RS05 structure page")[1].split()[0])
    if "RS05 merge source page" in t:
        return "m" + t.split("RS05 merge source page")[1].split()[0]
    return None if not t else "?"


def verify_rs05(manifest: dict) -> dict:
    results = []
    for name, expected in EXPECTED_ORDER.items():
        path = RAW / "rs05" / name
        pymupdf.TOOLS.mupdf_warnings()
        doc = pymupdf.open(path)
        state = warnings_and_repair(doc)
        labels = [page_label(p.get_text("text")) for p in doc]
        rotations = [p.rotation for p in doc]
        label_to_index = {lab: i for i, lab in enumerate(labels) if lab is not None}
        toc = doc.get_toc(simple=True)
        toc_check = []
        for lvl, title, pno in [tuple(x) for x in manifest["fixtures"]["rs05_structure"]["toc"]]:
            survivors = [e for e in toc if e[1] == title]
            target_exists = pno in label_to_index
            ok = None
            if survivors:
                got = survivors[0][2]
                ok = target_exists and got == label_to_index[pno] + 1
            toc_check.append({"title": title, "orig_page": pno, "present": bool(survivors),
                              "target_page_present": target_exists, "points_to_correct_page": ok})
        links = []
        for i, p in enumerate(doc):
            for ln in p.get_links():
                if ln.get("kind") == pymupdf.LINK_GOTO:
                    links.append({"from_label": labels[i], "to_label": labels[ln["page"]] if 0 <= ln.get("page", -1) < len(labels) else None})
        annots = [{"label": labels[i], "type": a["subtype"], "indirect_object": a["indirect_object"]}
                  for i, p in enumerate(doc) for a in raw_annots(doc, p) if a["subtype"] != "Widget" and a["subtype"] != "Link"]
        widgets = [{"label": labels[i], "name": w.field_name, "value": w.field_value} for i, p in enumerate(doc) for w in p.widgets()]
        doc.close()

        expected_rot = [90 if (name == "rotate.pdf" and lab == 2) else 0 for lab in labels]
        mandatory = {
            "page_count": len(labels) == len(expected),
            "order": labels == expected,
            "rotation": rotations == expected_rot,
            "no_repair_no_warning": (not state["is_repaired"]) and not state["mupdf_warnings"],
        }
        in_scope = None
        if name in IN_PLACE:
            link_ok = all(l["to_label"] == 4 for l in links if l["from_label"] == 1) and (any(l["from_label"] == 1 for l in links) or 1 not in labels)
            annot_ok = any(a["label"] == 2 and a["type"] == "Text" for a in annots) or 2 not in labels
            widget_ok = any(w["label"] == 3 and w["name"] == "rs05_field" for w in widgets) or 3 not in labels
            toc_ok = all((t["points_to_correct_page"] is True) for t in toc_check if t["target_page_present"])
            in_scope = {"bookmarks": toc_ok, "internal_link": link_ok, "annotation": annot_ok, "form_field": widget_ok}
        results.append({"output": name, "labels": labels, "rotations": rotations, "mandatory": mandatory,
                        "in_scope_structure": in_scope, "toc": toc_check, "links": links,
                        "annotations": annots, "widgets": widgets, "structure_state": state})
    return {"operations": results}


def main() -> int:
    manifest = json.loads((GEN / "manifest.json").read_text(encoding="utf-8"))
    report = {
        "reader": f"PyMuPDF {pymupdf.VersionBind}",
        "inputs": check_inputs(manifest),
        "rs01": verify_rs01(manifest),
        "rs02": verify_rs02(manifest),
        "rs03": verify_rs03(manifest),
        "rs05": verify_rs05(manifest),
    }
    (RAW / "verify_independent.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    print("Input tidak berubah:", all(v["unchanged"] for v in report["inputs"].values()))
    print("\nRS-01 render vs PyMuPDF (MAD<=10):")
    for p in report["rs01"]["render_compare"]:
        print(f"  {p['fixture']:26} p{p['page']}  MAD={p['gray_mad']:6.3f}  >64={p['pct_pixels_diff_gt_64']:6.3f}%  {'OK' if p['match'] else 'FAIL'}")
    print("RS-01 klasifikasi mismatch teks:")
    for t in report["rs01"]["text_mismatch_classification"]:
        print(f"  {t['fixture']} p{t['page']}: PDFium cocok setelah NFKC = {t['pdfium_matches_after_nfkc']}; "
              f"PyMuPDF cocok (NFKC) = {t['pymupdf_extracts_expected']}")
        print(f"     PyMuPDF: {t['pymupdf_line']}")
        print(f"     PDFium : {t['pdfium_line']}")
    print("\nRS-02 anotasi (visible>=1% di kedua engine):")
    print("  struktur:", report["rs02"]["structure"])
    print("  dapat dimuat API anotasi PyMuPDF:", sum(1 for x in report["rs02"]["pymupdf_annot_api_load"] if x["loadable_by_pymupdf_annot_api"]),
          "dari", len(report["rs02"]["pymupdf_annot_api_load"]))
    for v in report["rs02"]["visibility"]:
        print(f"  {v['kind']:9} {v['via'][:22]:22} pdfium={v['visible_pdfium']:.4f} pymupdf={v['visible_pymupdf']:.4f} "
              f"both={v['visible_both']} inFile={v['present_in_file']} subtype={v['subtype_in_file']} "
              f"indirect={v['indirect_object']} AP={v['has_AP_in_file']} InkList={v['has_InkList']}")
    print("\nRS-03 widget (objek mentah + PyMuPDF):")
    print("  struktur:", report["rs03"]["structure"], "| AcroForm:", report["rs03"]["acroform"])
    print("  PyMuPDF load_page error:", report["rs03"]["pymupdf_page_load_error"])
    for w in report["rs03"]["raw_widgets"]:
        print(f"  {w}")
    print("\nRS-05 operasi:")
    for o in report["rs05"]["operations"]:
        print(f"  {o['output']:18} labels={o['labels']} rot={o['rotations']}")
        print(f"     wajib={o['mandatory']}")
        print(f"     scope={o['in_scope_structure']}  toc_present={[t['present'] for t in o['toc']]} links={o['links']} annots={len(o['annotations'])} widgets={len(o['widgets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
