"""Spike 01 - Inti PDF: render, text layer, operasi halaman, round-trip.

Semua angka yang dilaporkan di STACK_EVALUATION.md harus berasal dari file ini.
Output: spikes/out/spike_01_core.json
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import pymupdf

OUT = Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)
FIX = Path(__file__).parent / "fixtures"
FIX.mkdir(parents=True, exist_ok=True)

results: dict = {"spike": "01_core", "pymupdf": pymupdf.__version__, "muPDF": pymupdf.pymupdf_version}


def timed(fn):
    t0 = time.perf_counter()
    value = fn()
    return value, (time.perf_counter() - t0) * 1000.0


def make_fixture(path: Path, pages: int = 12) -> Path:
    """Buat PDF sintetis multi-halaman dengan text layer, ukuran halaman campuran."""
    doc = pymupdf.open()
    sizes = [(595, 842), (842, 595), (612, 792), (420, 595)]
    for i in range(pages):
        w, h = sizes[i % len(sizes)]
        page = doc.new_page(width=w, height=h)
        page.insert_text((72, 90), f"UnionPDF fixture page {i + 1}", fontsize=18, fontname="helv")
        page.insert_text((72, 130), "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                         fontsize=11, fontname="helv")
        page.draw_rect(pymupdf.Rect(50, 150, 200, 250), color=(0.2, 0.4, 0.9), fill=(0.9, 0.95, 1.0))
        page.insert_text((72, 300), "REDOACTME-0001", fontsize=12, fontname="helv")
    doc.save(path)
    doc.close()
    return path


def build_large(path: Path, pages: int = 500) -> Path:
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 90), f"Page {i + 1}", fontsize=12, fontname="helv")
    doc.save(path, deflate=True)
    doc.close()
    return path


def s1_render_text(fixture: Path) -> None:
    doc = pymupdf.open(fixture)
    times, bytes_out = [], []
    for page in doc:
        t, ms = timed(lambda p=page: p.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).tobytes("png"))
        times.append(ms)
        bytes_out.append(len(t))
    text = doc[0].get_text().strip()
    words = doc[0].get_text("words")
    doc.close()
    results["s1_render_text"] = {
        "pages": len(times),
        "zoom": 2.0,
        "render_ms_min": round(min(times), 2),
        "render_ms_median": round(statistics.median(times), 2),
        "render_ms_max": round(max(times), 2),
        "png_bytes_median": int(statistics.median(bytes_out)),
        "text_extracted": text,
        "text_len": len(text),
        "word_count": len(words),
        "has_text_layer": len(words) > 0,
    }


def s2_page_ops(fixture: Path) -> None:
    src = pymupdf.open(fixture)
    total = src.page_count

    # merge
    other = pymupdf.open()
    other.insert_pdf(src, from_page=0, to_page=1)
    merged = pymupdf.open()
    merged.insert_pdf(src)
    merged.insert_pdf(other)
    merged.save(OUT / "s2_merged.pdf", deflate=True)
    merged_pages = merged.page_count
    merged.close()

    # split: ambil halaman 3..6
    split = pymupdf.open()
    split.insert_pdf(src, from_page=2, to_page=5)
    split.save(OUT / "s2_split.pdf", deflate=True)
    split_pages = split.page_count
    split.close()

    # rotate + delete + reorder
    for p in src:
        p.set_rotation(90)
    src.delete_page(0)
    src.save(OUT / "s2_rotated.pdf", deflate=True)
    src.close()

    # verifikasi reopen + isi
    def reopen_check(path: Path) -> dict:
        d = pymupdf.open(path)
        txt = d[0].get_text().strip() if d.page_count else ""
        info = {
            "pages": d.page_count,
            "rotation_page0": d[0].rotation if d.page_count else None,
            "first_page_text_head": txt.splitlines()[0] if txt else "",
        }
        d.close()
        return info

    results["s2_page_ops"] = {
        "source_pages": total,
        "merge_pages": merged_pages,
        "merge_expected": total + 2,
        "merge_ok": merged_pages == total + 2,
        "split_pages": split_pages,
        "split_expected": 4,
        "split_ok": split_pages == 4,
        "rotated_reopen": reopen_check(OUT / "s2_rotated.pdf"),
        "merged_reopen": reopen_check(OUT / "s2_merged.pdf"),
    }


def s3_large_doc() -> None:
    big = FIX / "large_500p.pdf"
    if not big.exists():
        build_large(big)
    size_mb = big.stat().st_size / 1024 / 1024

    t_open, ms_open = timed(lambda: pymupdf.open(big))
    doc = t_open
    t_count, ms_count = timed(lambda: doc.page_count)
    page = doc[0]
    t_render, ms_render = timed(lambda: page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).tobytes("png"))
    t_text, ms_text = timed(lambda: page.get_text("words"))
    t_save, ms_save = timed(lambda: doc.save(OUT / "s3_large_saved.pdf", deflate=True))
    doc.close()

    results["s3_large_doc"] = {
        "pages": ms_count and 500,
        "file_mb": round(size_mb, 2),
        "open_ms": round(ms_open, 2),
        "page_count_ms": round(ms_count, 2),
        "render_page0_ms": round(ms_render, 2),
        "extract_words_ms": round(ms_text, 2),
        "save_all_ms": round(ms_save, 2),
        "saved_mb": round((OUT / "s3_large_saved.pdf").stat().st_size / 1024 / 1024, 2),
    }


def s4_search_find() -> None:
    fixture = FIX / "fixture_12p.pdf"
    doc = pymupdf.open(fixture)
    hits = doc[0].search_for("REDOACTME-0001")
    n_hits = sum(len(doc[i].search_for("UnionPDF fixture")) for i in range(doc.page_count))
    doc.close()
    results["s4_search"] = {
        "search_rects_on_page0": len(hits),
        "search_hit_total": n_hits,
        "search_api": "Page.search_for -> Rect list",
    }


def s5_fonts_and_encrypt() -> None:
    """Cek dukungan font bawaan, font eksternal, dan enkripsi AES."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    fonts_ok = True
    try:
        page.insert_text((72, 100), "Helvetica built-in", fontsize=14, fontname="helv")
        page.insert_text((72, 130), "Times built-in", fontsize=14, fontname="tiro")
        page.insert_text((72, 160), "Courier built-in", fontsize=14, fontname="cour")
    except Exception as exc:  # noqa: BLE001
        fonts_ok = False
        results["font_error"] = str(exc)
    # font dari file sistem
    ext_ok = True
    try:
        page.insert_font(fontname="PF", fontfile=r"C:\Windows\Fonts\arial.ttf")
    except Exception:  # noqa: BLE001
        ext_ok = False
    plain = OUT / "s5_plain.pdf"
    doc.save(plain)
    doc.close()

    # enkripsi
    enc_ok, enc_err = False, None
    try:
        d = pymupdf.open(plain)
        d.save(OUT / "s5_encrypted.pdf", encryption=pymupdf.PDF_ENCRYPT_AES_256,
               owner_pw="owner", user_pw="user")
        d.close()
        enc_ok = True
    except Exception as exc:  # noqa: BLE001
        enc_err = str(exc)

    # reopen terenkripsi
    reopen_ok, reopen_err = False, None
    if enc_ok:
        try:
            d = pymupdf.open(OUT / "s5_encrypted.pdf")
            needs_pass_before = d.needs_pass
            auth_ok = bool(d.authenticate("user"))
            pages = d.page_count
            txt = d[0].get_text().strip() if pages else ""
            d.close()
            reopen_ok = auth_ok and pages == 1 and bool(txt)
            results["s5_encrypt_detail"] = {
                "needs_pass_before_auth": needs_pass_before,
                "authenticate_ok": auth_ok,
                "pages_after_auth": pages,
                "text_after_auth": txt[:60],
            }
        except Exception as exc:  # noqa: BLE001
            reopen_err = str(exc)

    results["s5_fonts_encrypt"] = {
        "builtin_fonts_ok": fonts_ok,
        "external_ttf_embed_ok": ext_ok,
        "aes256_encrypt_ok": enc_ok,
        "encrypt_error": enc_err,
        "encrypted_reopen_auth_ok": reopen_ok,
        "reopen_error": reopen_err,
    }


def main() -> int:
    fixture = FIX / "fixture_12p.pdf"
    if not fixture.exists():
        make_fixture(fixture)
    s1_render_text(fixture)
    s2_page_ops(fixture)
    s3_large_doc()
    s4_search_find()
    s5_fonts_and_encrypt()
    (OUT / "spike_01_core.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
