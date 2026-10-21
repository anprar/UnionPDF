"""Verifikasi angka yang dikutip di `docs/ANALYSIS_PDFGEAR.md`.

Menghitung ulang angka kunci langsung dari instalasi PDFgear, lalu
mencocokkannya dengan nilai yang tertulis di dokumen.

Jalankan:
  .venv\\Scripts\\python.exe scripts\\verify_pdfgear_artifact.py [path-install] [path-installer]

Exit code 0 = semua angka cocok, 1 = ada yang meleset.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXPECTED = {
    "jumlah_berkas_instalasi": 349,
    "ukuran_pdfgear_exe": 8_681_096,
    "sha256_pdfgear_exe": "6b74060a120115405ca685761ec955f54315dfd6883097dd79d219966aacd891",
    "sha256_installer": "633a1a1ff3aef27541e8bd8a472066b8ffc10442ee83729388958604496db69a",
    "jumlah_pustaka_pdf": 4,
    "jumlah_engine_ocr": 2,
    "jumlah_traineddata": 16,
    "jumlah_berkas_tessdata": 63,
    "jumlah_berkas_nsocr": 54,
    "jumlah_direktori_locale": 10,
    "jumlah_paket_oss": 15,
    "jumlah_aksi_copilot": 27,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_copilot_actions(exe: Path) -> int:
    """Hitung aksi pada resource tertanam pdfeditor.Utils.Copilot.actions.json."""
    data = exe.read_bytes()
    dec = json.JSONDecoder()
    best = 0
    for m in re.finditer(rb'\{\s*"actions"\s*:', data):
        txt = data[m.start():m.start() + 1_100_000].decode("utf-8", "ignore")
        try:
            obj, _ = dec.raw_decode(txt)
        except Exception:
            continue
        acts = obj.get("actions")
        if isinstance(acts, list):
            best = max(best, len(acts))
    return best


def main() -> int:
    install = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Program Files\PDFgear")
    if not install.is_dir():
        print(f"Direktori instalasi tidak ditemukan: {install}")
        return 2
    exe = install / "PDFgear.exe"
    if not exe.is_file():
        print(f"PDFgear.exe tidak ditemukan di {install}")
        return 2

    files = [p for p in install.rglob("*") if p.is_file()]
    pdf_libs = [p for p in files if p.suffix.lower() == ".dll"
                and re.search(r"(pdfium|Patagames\.Pdf|PdfFocus|Syncfusion\.Pdf)", p.name, re.I)]
    # Engine OCR dihitung per engine, bukan per berkas:
    # Tesseract.dll (C# wrapper) + x64/tesseract41.dll (native) = 1 engine;
    # NsOCR/Bin_64/NSOCR.dll = engine kedua.
    ocr_engines: set[str] = set()
    for p in files:
        if re.search(r"(?i)tesseract.*\.dll$", p.name):
            ocr_engines.add("tesseract")
        if re.search(r"(?i)^nsocr\.dll$", p.name):
            ocr_engines.add("nsocr")
    tessdata = install / "tessdata"
    nsocr = install / "NsOCR"
    locales = [p for p in install.iterdir() if p.is_dir() and re.fullmatch(
        r"(de|es|fr|it|ja|ko|nl|pt|ru|zh-CN|en)", p.name)]
    lic = install / "OpensourceLicense" / "LICENSE.txt"
    oss = 0
    if lic.is_file():
        oss = len(re.findall(r"^[A-Za-z0-9._-]+\(https?://", lic.read_text(encoding="utf-8", errors="replace"),
                             flags=re.MULTILINE))

    aktual = {
        "jumlah_berkas_instalasi": len(files),
        "ukuran_pdfgear_exe": exe.stat().st_size,
        "sha256_pdfgear_exe": sha256(exe),
        "jumlah_pustaka_pdf": len(pdf_libs),
        "jumlah_engine_ocr": len(ocr_engines),        "jumlah_traineddata": len(list(tessdata.glob("*.traineddata"))) if tessdata.is_dir() else 0,
        "jumlah_berkas_tessdata": len([p for p in tessdata.rglob("*") if p.is_file()]) if tessdata.is_dir() else 0,
        "jumlah_berkas_nsocr": len([p for p in nsocr.rglob("*") if p.is_file()]) if nsocr.is_dir() else 0,
        "jumlah_direktori_locale": len(locales),
        "jumlah_paket_oss": oss,
        "jumlah_aksi_copilot": extract_copilot_actions(exe),
    }
    if len(sys.argv) > 2:
        inst = Path(sys.argv[2])
        if inst.is_file():
            aktual["sha256_installer"] = sha256(inst)

    gagal = 0
    for kunci, diharapkan in EXPECTED.items():
        nilai = aktual.get(kunci)
        ok = nilai == diharapkan
        gagal += 0 if ok else 1
        shown = nilai if not isinstance(nilai, str) else nilai[:16] + "…"
        print(f"  [{'OK ' if ok else 'GAGAL'}] {kunci:26} diharapkan={str(diharapkan)[:18]:<18} aktual={shown}")

    if gagal:
        print(f"\n{gagal} angka tidak cocok.")
        return 1
    print("\nSeluruh angka pada docs/ANALYSIS_PDFGEAR.md cocok dengan instalasi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
