"""Spike 04 - Jalur OCR lokal (tanpa layanan berbayar, tanpa cloud).

Menguji kandidat OCR yang bisa dipakai UnionPDF:
  A) Tesseract (biner eksternal)   -> butuh instalasi sistem
  B) Windows.Media.Ocr (WinRT)     -> bawaan Windows, offline
  C) rapidocr-onnxruntime         -> pip-only, model ikut paket
  D) PyMuPDF page.get_textpage_ocr -> butuh Tesseract

Output: spikes/out/spike_04_ocr.json
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pymupdf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = Path(__file__).parent / "out"
FIX = Path(__file__).parent / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)
FIX.mkdir(parents=True, exist_ok=True)

results: dict = {"spike": "04_ocr"}

EXPECTED_LINES = [
    "INVOICE NUMBER 2026-0042",
    "Customer: PT Union PDF Nusantara",
    "Total Amount: Rp 1.250.000",
    "Due Date: 30 November 2026",
]


def make_scan_fixture(path: Path) -> Path:
    """Buat PDF 'scan' sintetik: gambar grayscale berisi teks, tanpa text layer."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("L", (1240, 1754), 255)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 44)
    except OSError:
        font = ImageFont.load_default()
    y = 200
    for line in EXPECTED_LINES:
        draw.text((150, y), line, fill=0, font=font)
        y += 140

    png = OUT / "scan_source.png"
    img.save(png)

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, filename=str(png))
    doc.save(path)
    doc.close()
    return path


def _render_page_png(fixture: Path, name: str) -> Path:
    doc = pymupdf.open(fixture)
    png_path = OUT / name
    doc[0].get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(png_path)
    doc.close()
    return png_path


def _score(text: str) -> dict:
    """Hitung berapa baris yang dikenali tepat (substring case-insensitive)."""
    low = (text or "").lower()
    hits = [line for line in EXPECTED_LINES if line.lower() in low]
    return {"lines_expected": len(EXPECTED_LINES), "lines_matched": len(hits), "matched": hits}


def probe_tesseract() -> dict:
    exe = shutil.which("tesseract")
    info = {"on_path": bool(exe), "path": exe, "tessdata_env": os.environ.get("TESSDATA_PREFIX")}
    if exe:
        try:
            r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20)
            info["version"] = r.stdout.strip().splitlines()[0] if r.stdout else r.stderr.strip()[:120]
            r2 = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, timeout=20)
            info["langs"] = [x for x in r2.stdout.split() if x and x != "List"]
        except Exception as exc:  # noqa: BLE001
            info["error"] = str(exc)
    return info


def probe_windows_ocr(fixture: Path) -> dict:
    out = {"api": "Windows.Media.Ocr (WinRT)"}
    try:
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.storage import FileAccessMode, StorageFile

        out["binding"] = "winrt-* 3.2.x"
        access = FileAccessMode.READ
    except Exception as exc:  # noqa: BLE001
        out["winrt_error"] = str(exc)[:200]
        try:
            from winsdk.windows.graphics.imaging import BitmapDecoder
            from winsdk.windows.media.ocr import OcrEngine
            from winsdk.windows.storage import FileAccessMode, StorageFile

            out["binding"] = "winsdk 1.0.0b10 (beta, fallback)"
            access = FileAccessMode.READ
        except Exception as exc2:  # noqa: BLE001
            out["ok"] = False
            out["error"] = f"tidak ada binding WinRT yang bisa dipakai: {exc2}"
            out["install_hint"] = (
                "pip install winrt-Windows.Media.Ocr winrt-Windows.Graphics.Imaging "
                "winrt-Windows.Storage winrt-Windows.Globalization winrt-Windows.Foundation"
            )
            return out

    try:
        try:
            engines = list(OcrEngine.get_available_recognizer_languages())
        except Exception:  # noqa: BLE001
            engines = []
        out["available_languages"] = [str(x) for x in engines]
        out["exposes_available_languages"] = hasattr(OcrEngine, "get_available_recognizer_languages")

        png_path = _render_page_png(fixture, "ocr_probe.png")

        engine = None
        if engines:
            engine = OcrEngine.try_create_from_language(engines[0])
        if engine is None:
            engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            # Coba bahasa eksplisit (mis. en-US) sebagai upaya terakhir.
            try:
                from winrt.windows.globalization import Language

                engine = OcrEngine.try_create_from_language(Language("en-US"))
            except Exception:  # noqa: BLE001
                engine = None
        if engine is None:
            out["ok"] = False
            out["error"] = "OcrEngine tidak bisa dibuat (tidak ada bahasa OCR terdaftar)"
            return out

        t0 = time.perf_counter()
        file = StorageFile.get_file_from_path_async(str(png_path)).get()
        stream = file.open_read_async().get()
        decoder = BitmapDecoder.create_async(stream).get()
        bitmap = decoder.get_software_bitmap_async().get()
        result = engine.recognize_async(bitmap).get()
        out["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        out["text"] = result.text
        out["ok"] = bool(result.text.strip())
        out["engine_language"] = str(engine.recognizer_language)
        out["accuracy"] = _score(result.text)
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["error"] = str(exc)[:400]
    return out


def probe_rapidocr(fixture: Path) -> dict:
    out = {"api": "rapidocr-onnxruntime"}
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["error"] = f"tidak terpasang: {exc}"
        out["install_hint"] = "pip install rapidocr-onnxruntime  (model ONNX ikut paket, ~80-150 MB)"
        return out
    try:
        png_path = _render_page_png(fixture, "ocr_probe2.png")
        engine = RapidOCR()
        t0 = time.perf_counter()
        result, _ = engine(str(png_path))
        out["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        lines = [r[1] for r in (result or [])]
        text = " | ".join(lines)
        out["text"] = text
        out["ok"] = bool(lines)
        out["accuracy"] = _score(text)
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["error"] = str(exc)[:400]
    return out


def probe_pymupdf_ocr(fixture: Path) -> dict:
    out = {"api": "Page.get_textpage_ocr"}
    doc = pymupdf.open(fixture)
    page = doc[0]
    try:
        tp = page.get_textpage_ocr(language="eng", dpi=300, full=True)
        text = tp.extractText()
        out["text"] = text
        out["ok"] = True
        out["accuracy"] = _score(text)
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["error"] = str(exc)[:300]
    doc.close()
    return out


def main() -> int:
    fixture = FIX / "scan_source.pdf"
    if not fixture.exists():
        make_scan_fixture(fixture)
    results["A_tesseract"] = probe_tesseract()
    results["B_windows_ocr"] = probe_windows_ocr(fixture)
    results["C_rapidocr"] = probe_rapidocr(fixture)
    results["D_pymupdf_ocr"] = probe_pymupdf_ocr(fixture)
    (OUT / "spike_04_ocr.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
