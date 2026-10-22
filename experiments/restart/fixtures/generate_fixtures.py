"""Generator fixture sintetis untuk spike restart (RS-01, RS-02, RS-03, RS-05).

Fixture dibuat dengan PyMuPDF (engine yang BUKAN sedang diuji, yaitu PDFium) agar
tidak bias satu engine. Semua isi sintetis; tidak memakai dokumen pribadi.

Jalankan dari experiments/restart:
    ..\\..\\.venv\\Scripts\\python.exe fixtures\\generate_fixtures.py

Output: fixtures/generated/*.pdf + fixtures/generated/manifest.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pymupdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
OUT = HERE / "generated"
FIXED_DATE = "D:20261021000000+07'00'"
# Font TrueType sistem untuk fixture Unicode/Arab. Fixture hasilnya tidak di-commit.
ARABIC_FONT = Path(r"C:\Windows\Fonts\arial.ttf")

A4 = (595.0, 842.0)
A4_LANDSCAPE = (842.0, 595.0)
LETTER = (612.0, 792.0)
A5 = (420.0, 595.0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finish(doc: pymupdf.Document, name: str) -> Path:
    doc.set_metadata({
        "title": f"UnionPDF synthetic fixture {name}",
        "author": "UnionPDF spike generator",
        "creator": "generate_fixtures.py",
        "producer": f"PyMuPDF {pymupdf.VersionBind}",
        "creationDate": FIXED_DATE,
        "modDate": FIXED_DATE,
    })
    path = OUT / name
    doc.save(path, garbage=3, deflate=True, no_new_id=True)
    doc.close()
    return path


def to_pdf_rect(page: pymupdf.Page, r: pymupdf.Rect) -> list[float]:
    """Rect PyMuPDF (origin kiri-atas) -> user space PDF [left, bottom, right, top]."""
    h = page.rect.height
    return [round(r.x0, 2), round(h - r.y1, 2), round(r.x1, 2), round(h - r.y0, 2)]


def page_info(doc_path: Path) -> list[dict]:
    doc = pymupdf.open(doc_path)
    pages = []
    for p in doc:
        pages.append({
            "index": p.number,
            "width": round(p.rect.width, 2),
            "height": round(p.rect.height, 2),
            "rotation": p.rotation,
            "text": p.get_text("text"),
        })
    doc.close()
    return pages


def make_mixed_sizes() -> dict:
    doc = pymupdf.open()
    sizes = [("A4", A4), ("A4-landscape", A4_LANDSCAPE), ("Letter", LETTER), ("A5", A5)]
    lines = []
    for i, (label, (w, h)) in enumerate(sizes, start=1):
        page = doc.new_page(width=w, height=h)
        line = f"UnionPDF RS01 mixed page {i} size {label}"
        page.insert_text((50, 80), line, fontname="helv", fontsize=14)
        lines.append([line])
    path = finish(doc, "rs01_mixed_sizes.pdf")
    return {"file": path.name, "expected_lines": lines}


def make_latin() -> dict:
    doc = pymupdf.open()
    content = [
        ["The quick brown fox jumps over the lazy dog 0123456789.",
         "Cafe naive cooperation resume - plain ASCII line.",
         "Accented Latin: Café naïve façade Ångström Œuvre Straße."],
        ["Second page for search: UNIONPDF-SEARCH-TOKEN appears once.",
         "Punctuation check: (brackets) [square] {curly} 'quote' \"dq\"."],
    ]
    for lines in content:
        page = doc.new_page(width=A4[0], height=A4[1])
        y = 90
        for line in lines:
            # v2 (2026-10-21): baris beraksen memakai font TrueType agar Œ (U+0152) ter-encode
            # benar; font base-14 'helv' menulisnya sebagai '·' (cacat fixture v1).
            if any(ord(c) > 127 for c in line) and ARABIC_FONT.is_file():
                page.insert_text((50, y), line, fontfile=str(ARABIC_FONT), fontname="F1", fontsize=12)
            else:
                page.insert_text((50, y), line, fontname="helv", fontsize=12)
            y += 24
    path = finish(doc, "rs01_latin.pdf")
    return {"file": path.name, "expected_lines": content,
            "search_token": "UNIONPDF-SEARCH-TOKEN", "search_token_page": 1}


def make_unicode_arabic() -> dict:
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    # v2 (2026-10-21): layout HTML MuPDF (HarfBuzz) agar teks Arab ber-shaping dengan arah RTL.
    lines = [
        "Bahasa Indonesia: dokumen uji sintetis.",
        "مرحبا بالعالم",
        "Greek & symbols: αβγ Ω € ™ ±",
    ]
    font_ok = ARABIC_FONT.is_file()
    if font_ok:
        css = ("@font-face {font-family: uarial; src: url(arial.ttf);} "
               "* {font-family: uarial; font-size: 13pt;}")
        html = (f"<p>{lines[0]}</p><p dir=\"rtl\">{lines[1]}</p>"
                f"<p>{lines[2].replace('&', '&amp;')}</p>")
        page.insert_htmlbox(pymupdf.Rect(50, 60, 545, 400), html, css=css,
                            archive=pymupdf.Archive(str(ARABIC_FONT.parent)))
    else:
        y = 90
        for line in lines:
            page.insert_text((50, y), line, fontname="helv", fontsize=13)
            y += 26
    path = finish(doc, "rs01_unicode_arabic.pdf")
    return {"file": path.name, "expected_lines": [lines],
            "font": str(ARABIC_FONT) if font_ok else "helv (fallback)",
            "note": "v2: insert_htmlbox (shaping HarfBuzz, dir=rtl). Ekstraksi dibandingkan setelah NFKC."}


def make_images() -> dict:
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    # Gambar sintetis: gradien 240x160 dibuat piksel demi piksel (tanpa file eksternal).
    w, h = 240, 160
    samples = bytearray()
    for y in range(h):
        for x in range(w):
            samples += bytes((x * 255 // (w - 1), y * 255 // (h - 1), 128))
    pix = pymupdf.Pixmap(pymupdf.csRGB, w, h, bytes(samples), False)
    page.insert_image(pymupdf.Rect(60, 120, 60 + w * 1.5, 120 + h * 1.5), pixmap=pix)
    line = "UnionPDF RS01 image page"
    page.insert_text((60, 90), line, fontname="helv", fontsize=14)
    path = finish(doc, "rs01_images.pdf")
    return {"file": path.name, "expected_lines": [[line]]}


def make_large() -> dict:
    doc = pymupdf.open()
    lines = []
    for i in range(1, 501):
        page = doc.new_page(width=A4[0], height=A4[1])
        line = f"UnionPDF RS01 large page {i}"
        page.insert_text((50, 80), line, fontname="helv", fontsize=12)
        lines.append([line])
    path = finish(doc, "rs01_large_500p.pdf")
    return {"file": path.name, "expected_lines": lines}


def make_annot_base() -> dict:
    doc = pymupdf.open()
    p0 = doc.new_page(width=A4[0], height=A4[1])
    p0.insert_text((50, 60), "RS02 page 1: area for shapes, notes, ink, stamp.", fontname="helv", fontsize=12)
    p1 = doc.new_page(width=A4[0], height=A4[1])
    targets = {}
    y = 120
    for key in ("highlight", "underline", "strikeout", "squiggly"):
        text = f"RS02 markup target line for {key}."
        p1.insert_text((60, y), text, fontname="helv", fontsize=14)
        y += 40
    path = finish(doc, "rs02_annot_base.pdf")
    # ukur rect target setelah disimpan
    d = pymupdf.open(path)
    pg = d[1]
    for key in ("highlight", "underline", "strikeout", "squiggly"):
        hits = pg.search_for(f"RS02 markup target line for {key}.")
        targets[key] = to_pdf_rect(pg, hits[0])
    d.close()
    return {"file": path.name, "markup_targets_page_index": 1, "markup_targets_pdf_rect": targets}


def make_form() -> dict:
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    page.insert_text((50, 60), "RS03 form fixture (AcroForm)", fontname="helv", fontsize=14)

    def add(widget: pymupdf.Widget) -> None:
        page.add_widget(widget)

    w = pymupdf.Widget()
    w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    w.field_name = "nama"
    w.rect = pymupdf.Rect(50, 100, 300, 125)
    w.field_value = ""
    w.text_fontsize = 11
    add(w)

    w = pymupdf.Widget()
    w.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
    w.field_name = "setuju"
    w.rect = pymupdf.Rect(50, 145, 66, 161)
    w.field_value = False
    add(w)

    for idx, rect in enumerate((pymupdf.Rect(50, 185, 66, 201), pymupdf.Rect(90, 185, 106, 201))):
        w = pymupdf.Widget()
        w.field_type = pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON
        w.field_name = "pilihan"
        w.rect = rect
        w.field_value = False
        w.button_caption = None
        add(w)

    w = pymupdf.Widget()
    w.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
    w.field_name = "kota"
    w.rect = pymupdf.Rect(50, 225, 250, 245)
    w.choice_values = ["Jakarta", "Bandung", "Surabaya"]
    w.field_value = "Jakarta"
    add(w)

    path = finish(doc, "rs03_form.pdf")
    group_radios(path)
    return {"file": path.name,
            "fields": {"nama": "text", "setuju": "checkbox", "pilihan": "radio group (A, B)", "kota": "combobox"}}


def group_radios(path: Path) -> None:
    """v2 (2026-10-21): jadikan dua widget radio 'pilihan' satu field grup dengan /Parent + /Kids
    dan export value berbeda (A, B). Fixture v1 berisi dua field terpisah bernama sama."""
    import re
    doc = pymupdf.open(path)
    page_xref = doc.page_xref(0)
    annots = re.findall(r"(\d+) 0 R", doc.xref_get_key(page_xref, "Annots")[1])
    kids = [int(x) for x in annots if doc.xref_get_key(int(x), "T")[1] == "pilihan"]
    assert len(kids) == 2, kids
    parent = doc.get_new_xref()
    doc.update_object(parent, "<</FT/Btn/Ff 49152/T(pilihan)/V/Off/Kids[%d 0 R %d 0 R]>>" % tuple(kids))
    for kid, state in zip(kids, ("A", "B")):
        for key in ("AP/N", "AP/D"):
            t, v = doc.xref_get_key(kid, key)
            if t == "dict":
                doc.xref_set_key(kid, key, v.replace("/Yes", "/" + state))
        doc.xref_set_key(kid, "AS", "/Off")
        doc.xref_set_key(kid, "Parent", f"{parent} 0 R")
        for key in ("T", "FT", "Ff", "V"):
            doc.xref_set_key(kid, key, "null")
    cat = doc.pdf_catalog()
    fields = doc.xref_get_key(cat, "AcroForm/Fields")[1]
    for kid in kids:
        fields = fields.replace(f"{kid} 0 R", "")
    fields = fields.rstrip("]").rstrip() + f" {parent} 0 R]"
    doc.xref_set_key(cat, "AcroForm/Fields", fields)
    tmp = path.with_suffix(".tmp.pdf")
    doc.save(tmp, garbage=3, deflate=True, no_new_id=True)
    doc.close()
    tmp.replace(path)


def make_structure() -> dict:
    doc = pymupdf.open()
    sizes = [A4, A4, LETTER, A4_LANDSCAPE, A5, A4]
    for i, (w, h) in enumerate(sizes, start=1):
        page = doc.new_page(width=w, height=h)
        page.insert_text((50, 70), f"RS05 structure page {i}", fontname="helv", fontsize=14)
    # bookmark (outline) ke halaman 1, 3, 4, 6
    doc.set_toc([[1, "Bab 1", 1], [1, "Bab 3", 3], [2, "Sub 3.1 ke hal 4", 4], [1, "Bab 6", 6]])
    # link internal: hal 1 -> hal 4
    p1 = doc[0]
    p1.insert_text((50, 110), "Link ke halaman 4", fontname="helv", fontsize=12)
    p1.insert_link({"kind": pymupdf.LINK_GOTO, "from": pymupdf.Rect(48, 96, 170, 114), "page": 3})
    # anotasi teks pada hal 2
    doc[1].add_text_annot((60, 120), "RS05 note on page 2")
    # field form pada hal 3
    w = pymupdf.Widget()
    w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    w.field_name = "rs05_field"
    w.rect = pymupdf.Rect(50, 110, 250, 132)
    w.field_value = "nilai awal"
    doc[2].add_widget(w)
    path = finish(doc, "rs05_structure.pdf")

    src = pymupdf.open()
    for i in (1, 2):
        page = src.new_page(width=A4[0], height=A4[1])
        page.insert_text((50, 70), f"RS05 merge source page {i}", fontname="helv", fontsize=14)
    src_path = finish(src, "rs05_merge_source.pdf")
    return {"file": path.name, "merge_source": src_path.name,
            "toc": [[1, "Bab 1", 1], [1, "Bab 3", 3], [2, "Sub 3.1 ke hal 4", 4], [1, "Bab 6", 6]],
            "links": [{"from_page": 1, "to_page": 4}],
            "annots": {"2": "Text"}, "widgets": {"3": "rs05_field"}}


def make_redact() -> dict:
    """RS-07: rahasia di 8 kanal. Area redaksi R1..R5 (koordinat PyMuPDF, origin kiri-atas)."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    page.insert_text((50, 80), "Data publik: laporan triwulan.", fontname="helv", fontsize=12)
    page.insert_text((50, 150), "RAHASIA-7781 nomor rekening", fontname="helv", fontsize=12)
    page.insert_text((50, 300), "RAHASIA-HIDDEN-9931", fontname="helv", fontsize=12, render_mode=3)
    page.insert_text((50, 500), "Teks publik bawah tetap ada.", fontname="helv", fontsize=12)
    # Form XObject berisi rahasia (halaman sumber disisipkan sebagai XObject)
    src = pymupdf.open()
    sp = src.new_page(width=360, height=60)
    sp.insert_text((10, 35), "RAHASIA-XOBJ-5520", fontname="helv", fontsize=14)
    page.show_pdf_page(pymupdf.Rect(40, 200, 400, 260), src, 0)
    # gambar & vektor
    w, h = 140, 100
    samples = bytes(v for y in range(h) for x in range(w) for v in (200, 30 + x, 30 + y))
    page.insert_image(pymupdf.Rect(420, 130, 560, 230), pixmap=pymupdf.Pixmap(pymupdf.csRGB, w, h, samples, False))
    page.draw_rect(pymupdf.Rect(420, 260, 560, 320), color=(0.8, 0, 0), fill=(0.8, 0, 0))
    # anotasi & field & metadata (kanal di luar content stream)
    page.add_freetext_annot(pymupdf.Rect(300, 136, 400, 160), "RAHASIA-ANNOT-1200", fontsize=8)
    wd = pymupdf.Widget()
    wd.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    wd.field_name = "rs07_field"
    wd.rect = pymupdf.Rect(50, 400, 300, 422)
    wd.field_value = "RAHASIA-FIELD-3300"
    page.add_widget(wd)
    path = finish(doc, "rs07_redact.pdf")
    d = pymupdf.open(path)
    d.set_metadata({**d.metadata, "subject": "RAHASIA-META-4400"})
    tmp = path.with_suffix(".tmp.pdf")
    d.save(tmp, garbage=3, deflate=True, no_new_id=True)
    d.close()
    tmp.replace(path)
    areas = {"R1_text": [40, 130, 410, 165], "R2_xobject": [40, 200, 400, 260], "R3_hidden": [40, 280, 400, 320],
             "R4_image": [420, 130, 560, 230], "R5_vector": [420, 260, 560, 320]}
    return {"file": path.name, "page_height": A4[1], "areas_mupdf": areas,
            "secrets": {"content_text": "RAHASIA-7781", "xobject_text": "RAHASIA-XOBJ-5520",
                        "hidden_text": "RAHASIA-HIDDEN-9931", "annotation": "RAHASIA-ANNOT-1200",
                        "form_field": "RAHASIA-FIELD-3300", "metadata": "RAHASIA-META-4400"},
            "public_text": ["Data publik: laporan triwulan.", "Teks publik bawah tetap ada."]}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "rs01_mixed_sizes": make_mixed_sizes(),
        "rs01_latin": make_latin(),
        "rs01_unicode_arabic": make_unicode_arabic(),
        "rs01_images": make_images(),
        "rs01_large_500p": make_large(),
        "rs02_annot_base": make_annot_base(),
        "rs03_form": make_form(),
        "rs05_structure": make_structure(),
        "rs07_redact": make_redact(),
    }
    files = sorted(p.name for p in OUT.glob("*.pdf"))
    manifest = {
        "generator": "experiments/restart/fixtures/generate_fixtures.py",
        "pymupdf_version": pymupdf.VersionBind,
        "fixtures": fixtures,
        "files": {name: {"sha256": sha256(OUT / name), "bytes": (OUT / name).stat().st_size,
                         "pages": page_info(OUT / name)} for name in files},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    for name in files:
        info = manifest["files"][name]
        print(f"{name:28} {info['bytes']:>9} byte  {len(info['pages']):>3} hlm  sha256={info['sha256'][:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
