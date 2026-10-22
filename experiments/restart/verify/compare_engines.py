"""Verifier lintas engine (PDFium, MuPDF, PDFBox) pada fixture & operasi yang sama.

Pembaca: PDFium (`pdfium-spike describe`), PyMuPDF (API + objek mentah), Pillow (piksel).
Untuk output engine X, pembaca yang bukan X dianggap independen.

Jalankan dari experiments/restart:
    ..\\..\\.venv\\Scripts\\python.exe verify\\compare_engines.py
Output: raw/compare/compare.json + ringkasan di stdout.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

import pymupdf
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_independent import (raw_annots, region_diff_fraction, pdf_rect_to_box, render_pymupdf,  # noqa: E402
                                warnings_and_repair, page_label, norm, ANNOT_VISIBLE_MIN)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "fixtures" / "generated"
CMP = ROOT / "raw" / "compare"
SPIKE = ROOT / "pdfium-spike" / "target" / "release" / "pdfium-spike.exe"
ENGINES = ["pdfium", "mupdf", "pdfbox"]


def stage_pdfium_outputs() -> None:
    """Salin output spike PDFium (raw/rs0x) ke raw/compare/pdfium dengan nama seragam."""
    d = CMP / "pdfium"
    d.mkdir(parents=True, exist_ok=True)
    pairs = {"rs02/annotated.pdf": "rs02_annotated.pdf", "rs03/filled.pdf": "rs03_filled.pdf",
             "rs05/merge_append.pdf": "rs05_merge.pdf", "rs05/extract_p2-4.pdf": "rs05_extract_p2-4.pdf"}
    for src, dst in pairs.items():
        if (ROOT / "raw" / src).exists():
            shutil.copy2(ROOT / "raw" / src, d / dst)


def pdfium_describe(pdf: Path) -> dict:
    out = pdf.with_suffix(".pdfium.json")
    rdir = pdf.parent / "render"
    proc = subprocess.run([str(SPIKE), "describe", str(pdf), str(out), str(rdir)], capture_output=True, text=True)
    if proc.returncode != 0 or not out.exists():
        return {"describe_error": proc.stderr.strip()[:300] or f"exit {proc.returncode}"}
    return json.loads(out.read_text(encoding="utf-8"))


def mu_open(pdf: Path) -> tuple[pymupdf.Document | None, str | None]:
    pymupdf.TOOLS.mupdf_warnings()
    try:
        return pymupdf.open(pdf), None
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


def mu_page_ok(doc: pymupdf.Document) -> str | None:
    try:
        for p in doc:
            list(p.widgets())
        return None
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {e}"


# ------------------------------------------------------------------ RS-02
def check_rs02(engine: str) -> dict | None:
    pdf = CMP / engine / "rs02_annotated.pdf"
    result_file = CMP / engine / "result.json" if engine != "pdfium" else ROOT / "raw" / "rs02" / "result_pdfium.json"
    if not pdf.exists() or not result_file.exists():
        return None
    res = json.loads(result_file.read_text(encoding="utf-8"))
    created = res["created"] if engine == "pdfium" else res["rs02"]["created"]
    pd = pdfium_describe(pdf)
    doc, err = mu_open(pdf)
    rows = []
    for c in created:
        page = doc[c["page"]]
        raw = next((a for a in raw_annots(doc, page) if a["contents"] == c["contents"]), None)
        pdfium_seen = any(a.get("contents") == c["contents"] for a in pd["pages"][c["page"]]["annotations"]) if "pages" in pd else False
        loadable = None
        if raw:
            loadable = any((page.load_annot(x) is not None) for x, *_ in page.annot_xrefs() if x) and raw["indirect_object"]
        box = pdf_rect_to_box(c["rect"], page.rect.height, 2.0)
        stem = pdf.stem
        rdir = pdf.parent / "render"
        try:
            vp = region_diff_fraction(Image.open(rdir / f"{stem}_p{c['page']}_annots.png").convert("RGB"),
                                      Image.open(rdir / f"{stem}_p{c['page']}_noannots.png").convert("RGB"), box)
        except Exception:  # noqa: BLE001
            vp = None
        vm = region_diff_fraction(render_pymupdf(page, 2.0, True), render_pymupdf(page, 2.0, False), box)
        rows.append({"kind": c["kind"], "in_file": raw is not None, "subtype": raw["subtype"] if raw else None,
                     "has_AP": raw["has_AP"] if raw else None, "indirect": raw["indirect_object"] if raw else None,
                     "pymupdf_api_loadable": loadable, "pdfium_reads": pdfium_seen,
                     "visible_pdfium": vp, "visible_pymupdf": vm,
                     "visible_both": (vp or 0) >= ANNOT_VISIBLE_MIN and vm >= ANNOT_VISIBLE_MIN})
    state = warnings_and_repair(doc)
    doc.close()
    return {"output": pdf.name, "structure_pymupdf": state, "annotations": rows}


# ------------------------------------------------------------------ RS-03
def check_rs03(engine: str) -> dict | None:
    pdf = CMP / engine / "rs03_filled.pdf"
    if not pdf.exists():
        return None
    expected_text = {"pdfium": "Diisi PDFium RS03", "mupdf": "Diisi MuPDF RS03", "pdfbox": "Diisi PDFBox RS03"}[engine]
    doc, err = mu_open(pdf)
    raw = []
    for x in re.findall(r"(\d+) 0 R", doc.xref_get_key(doc.page_xref(0), "Annots")[1]):
        x = int(x)
        t = doc.xref_get_key(x, "T")[1]
        par = doc.xref_get_key(x, "Parent")
        name = t if t != "null" else (doc.xref_get_key(int(par[1].split()[0]), "T")[1] if par[0] == "xref" else None)
        entry = {"name": name, "AS": list(doc.xref_get_key(x, "AS")), "V": list(doc.xref_get_key(x, "V"))}
        if par[0] == "xref":
            entry["parent_V"] = list(doc.xref_get_key(int(par[1].split()[0]), "V"))
        n = doc.xref_get_key(x, "AP/N")
        if n[0] == "xref":
            stream = doc.xref_stream(int(n[1].split()[0])) or b""
            entry["AP_N_contains_value"] = expected_text.encode() in stream or b"Surabaya" in stream
        raw.append(entry)
    page_err = mu_page_ok(doc)
    mu_widgets = None if page_err else [{"name": w.field_name, "value": w.field_value} for w in doc[0].widgets()]
    doc.close()
    pd = pdfium_describe(pdf)
    pd_fields = pd["pages"][0]["form_fields"] if "pages" in pd else pd
    by = {e["name"]: e for e in raw if e["name"] not in ("pilihan",)}
    radios = [e for e in raw if e["name"] == "pilihan"]
    checks = {
        "text_value": by.get("nama", {}).get("V", [None, None])[1] == expected_text,
        "text_appearance_updated": bool(by.get("nama", {}).get("AP_N_contains_value")),
        "checkbox_AS_is_name_Yes": by.get("setuju", {}).get("AS") == ["name", "/Yes"],
        "radio_B_selected_only": sorted(r["AS"][1] for r in radios) == ["/B", "/Off"],
        "combo_value": by.get("kota", {}).get("V", [None, None])[1] == "Surabaya",
        "combo_appearance_updated": bool(by.get("kota", {}).get("AP_N_contains_value")),
        "pymupdf_can_load_page": page_err is None,
    }
    return {"output": pdf.name, "checks": checks, "raw_widgets": raw, "pymupdf_widgets": mu_widgets,
            "pymupdf_page_error": page_err, "pdfium_fields": pd_fields}


# ------------------------------------------------------------------ RS-04
def check_rs04(engine: str) -> dict | None:
    pdf = CMP / engine / "rs04_fields.pdf"
    if not pdf.exists():
        return None
    pd = pdfium_describe(pdf)
    pd_fields = pd["pages"][0]["form_fields"] if "pages" in pd else []
    doc, err = mu_open(pdf)
    widgets = [{"name": w.field_name, "type": w.field_type_string, "value": w.field_value} for w in doc[0].widgets()]
    ap = {}
    for w in doc[0].widgets():
        ap[w.field_name] = doc.xref_get_key(w.xref, "AP")[0] != "null"
    acro = doc.xref_get_key(doc.pdf_catalog(), "AcroForm")[0] != "null"
    # isi oleh pembaca independen (PyMuPDF), simpan, baca ulang dengan PDFium
    for w in doc[0].widgets():
        if w.field_name == "rs04_text":
            w.field_value = "diisi pembaca lain"
        elif w.field_name == "rs04_check":
            w.field_value = w.on_state()
        w.update()
    filled = pdf.with_name("rs04_fields_refilled_by_pymupdf.pdf")
    doc.save(filled)
    doc.close()
    pd2 = pdfium_describe(filled)
    pd2_fields = pd2["pages"][0]["form_fields"] if "pages" in pd2 else []
    names_pd = sorted(f.get("name") or "" for f in pd_fields)
    return {"output": pdf.name, "acroform_present": acro, "pymupdf_widgets": widgets, "widget_has_AP": ap,
            "pdfium_fields": pd_fields, "pdfium_fields_after_refill": pd2_fields,
            "checks": {"both_fields_recognised_by_pdfium": names_pd == ["rs04_check", "rs04_text"],
                       "both_fields_recognised_by_pymupdf": sorted(w["name"] for w in widgets) == ["rs04_check", "rs04_text"],
                       "refill_visible_to_pdfium": any(f.get("value") == "diisi pembaca lain" for f in pd2_fields)
                       and any(f.get("checked") is True for f in pd2_fields)}}


# ------------------------------------------------------------------ RS-05
EXPECT_RS05 = {"rs05_merge.pdf": [1, 2, 3, 4, 5, 6, "m1", "m2"], "rs05_extract_p2-4.pdf": [2, 3, 4],
               "rs05_extract_pageextractor.pdf": [2, 3, 4], "rs05_extract_inplace.pdf": [2, 3, 4]}


def check_rs05(engine: str) -> list[dict]:
    rows = []
    for name, expected in EXPECT_RS05.items():
        pdf = CMP / engine / name
        if not pdf.exists():
            continue
        doc, err = mu_open(pdf)
        state = warnings_and_repair(doc)
        labels = [page_label(p.get_text("text")) for p in doc]
        idx = {lab: i + 1 for i, lab in enumerate(labels) if lab is not None}
        toc = doc.get_toc(simple=True)
        orig_toc = [[1, "Bab 1", 1], [1, "Bab 3", 3], [2, "Sub 3.1 ke hal 4", 4], [1, "Bab 6", 6]]
        toc_ok = []
        for lvl, title, p in orig_toc:
            if p not in idx:
                continue
            got = [e for e in toc if e[1] == title]
            toc_ok.append(bool(got) and got[0][2] == idx[p])
        links = [(labels[i], labels[ln["page"]] if 0 <= ln.get("page", -1) < len(labels) else None)
                 for i, p in enumerate(doc) for ln in p.get_links() if ln.get("kind") == pymupdf.LINK_GOTO]
        link_ok = (1 not in idx) or ((1, 4) in links if 4 in idx else True)
        acro_fields = doc.xref_get_key(doc.pdf_catalog(), "AcroForm/Fields")
        field_ok = (3 not in idx) or (acro_fields[0] == "array" and any(w.field_name == "rs05_field" for w in doc[idx[3] - 1].widgets()))
        annot_ok = (2 not in idx) or any(a["subtype"] == "Text" for a in raw_annots(doc, doc[idx[2] - 1]))
        doc.close()
        pd = pdfium_describe(pdf)
        rows.append({"output": name, "labels": labels,
                     "checks": {"order": labels == expected,
                                "no_repair_no_warning": (not state["is_repaired"]) and not state["mupdf_warnings"],
                                "bookmarks_in_scope_preserved": all(toc_ok) if toc_ok else None,
                                "internal_link_preserved": link_ok,
                                "form_field_preserved_as_field": field_ok,
                                "text_annotation_preserved": annot_ok,
                                "pdfium_bookmarks": len(pd.get("bookmarks", []))}})
    return rows


# ------------------------------------------------------------------ RS-07 (MuPDF)
def scan_raw(doc: pymupdf.Document, secret: str) -> bool:
    b = secret.encode()
    for x in range(1, doc.xref_length()):
        try:
            if doc.xref_is_stream(x) and b in (doc.xref_stream(x) or b""):
                return True
            if secret in doc.xref_object(x, compressed=True):
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


def check_rs07() -> list[dict]:
    manifest = json.loads((GEN / "manifest.json").read_text(encoding="utf-8"))
    fx = manifest["fixtures"]["rs07_redact"]
    rows = []
    for name in ("rs07_redacted_apply_only.pdf", "rs07_redacted_apply_plus_scrub.pdf"):
        pdf = CMP / "mupdf" / name
        if not pdf.exists():
            continue
        doc, err = mu_open(pdf)
        mu_text = doc[0].get_text("text")
        meta = json.dumps(doc.metadata, ensure_ascii=False) + (doc.get_xml_metadata() or "")
        pd = pdfium_describe(pdf)
        pd_text = pd["pages"][0]["text"] if "pages" in pd else ""
        channels = {}
        for ch, secret in fx["secrets"].items():
            channels[ch] = {"in_text_pdfium": secret in pd_text, "in_text_pymupdf": secret in mu_text,
                            "in_raw_objects_or_streams": scan_raw(doc, secret),
                            "in_metadata": secret in meta}
            channels[ch]["leaked"] = any(channels[ch].values())
        # piksel: area gambar & vektor harus tertutup (tidak lagi berwarna asli)
        render = Image.open(pdf.parent / "render" / f"{pdf.stem}_p0_annots.png").convert("RGB")
        def frac_dark(box):
            crop = render.crop(tuple(int(v * 2) for v in box)).convert("L")
            h = crop.histogram()
            return round(sum(h[:40]) / max(1, crop.size[0] * crop.size[1]), 4)
        public_ok = all(p in norm(pd_text) for p in fx["public_text"])
        state = warnings_and_repair(doc)
        doc.close()
        rows.append({"output": name, "channels": channels,
                     "image_area_dark_fraction": frac_dark(fx["areas_mupdf"]["R4_image"]),
                     "vector_area_dark_fraction": frac_dark(fx["areas_mupdf"]["R5_vector"]),
                     "public_text_preserved_pdfium": public_ok, "structure_pymupdf": state})
    return rows


# ------------------------------------------------------------------ RS-08 (PDFBox)
def check_rs08() -> dict | None:
    pdf = CMP / "pdfbox" / "rs08_signed.pdf"
    if not pdf.exists():
        return None
    res = json.loads((CMP / "pdfbox" / "result.json").read_text(encoding="utf-8"))["rs08"]
    pd = pdfium_describe(pdf)
    doc, err = mu_open(pdf)
    flags = doc.get_sigflags()
    doc.close()
    tampered = pdfium_describe(CMP / "pdfbox" / "rs08_signed_tampered.pdf")
    return {"bc_verify_original": res["verify_original_by_bouncycastle"], "bc_verify_tampered": res["verify_tampered_by_bouncycastle"],
            "pdfium_signature_count": len(pd.get("signatures", [])), "pdfium_signatures": pd.get("signatures"),
            "pymupdf_sigflags": flags, "pdfium_loads_tampered": "pages" in tampered,
            "limits": "self-signed test cert; integritas diverifikasi BC (library yang sama); rantai kepercayaan tidak dinilai"}


def main() -> int:
    stage_pdfium_outputs()
    report = {"rs02": {}, "rs03": {}, "rs04": {}, "rs05": {}}
    for e in ENGINES:
        report["rs02"][e] = check_rs02(e)
        report["rs03"][e] = check_rs03(e)
        report["rs04"][e] = check_rs04(e)
        report["rs05"][e] = check_rs05(e)
    report["rs07_mupdf"] = check_rs07()
    report["rs08_pdfbox"] = check_rs08()
    (CMP / "compare.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print("== RS-02 anotasi: kind | AP | indirect | API PyMuPDF | PDFium baca | visible both")
    for e in ENGINES:
        r = report["rs02"][e]
        if not r:
            print(f"  {e}: -")
            continue
        ok = sum(1 for a in r["annotations"] if a["has_AP"] and a["visible_both"])
        print(f"  {e}: {len(r['annotations'])} dibuat; AP+terlihat di kedua engine: {ok}; repair={r['structure_pymupdf']}")
        for a in r["annotations"]:
            print(f"     {a['kind']:9} AP={a['has_AP']!s:5} ind={a['indirect']!s:5} api={a['pymupdf_api_loadable']!s:5} "
                  f"pdfium={a['pdfium_reads']!s:5} vis_pdfium={a['visible_pdfium']} vis_mu={a['visible_pymupdf']} both={a['visible_both']}")
    print("== RS-03 isi form")
    for e in ENGINES:
        r = report["rs03"][e]
        print(f"  {e}: {r['checks'] if r else '-'}")
    print("== RS-04 buat field")
    for e in ENGINES:
        r = report["rs04"][e]
        print(f"  {e}: {r['checks'] if r else 'NOT_RUN (tidak ada API / ditunda)'}")
    print("== RS-05 merge/extract")
    for e in ENGINES:
        for r in report["rs05"][e]:
            print(f"  {e:6} {r['output']:32} {r['labels']} {r['checks']}")
    print("== RS-07 redaksi (MuPDF)")
    for r in report["rs07_mupdf"]:
        leaked = [k for k, v in r["channels"].items() if v["leaked"]]
        print(f"  {r['output']}: bocor={leaked} image_dark={r['image_area_dark_fraction']} vector_dark={r['vector_area_dark_fraction']} "
              f"public_ok={r['public_text_preserved_pdfium']} repair={r['structure_pymupdf']}")
    print("== RS-08 signature (PDFBox)")
    print(" ", json.dumps(report["rs08_pdfbox"], ensure_ascii=False)[:700])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
