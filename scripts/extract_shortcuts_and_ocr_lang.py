"""Inventaris bahasa OCR & pintasan keyboard aplikasi referensi (read-only).

Dua hal yang belum tertutup di v1/v2:
  U-07 — pintasan keyboard (dari string shortcut di modul & resource)
  U-10 — daftar bahasa OCR yang benar-benar tersedia (dari IRIS_OCR/resources)

Jalankan: .venv\\Scripts\\python.exe scripts\\extract_shortcuts_and_ocr_lang.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REF = Path(r"C:\Program Files\Nitro\PDF Pro\14")
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "research"

ASCII_RE = re.compile(rb"[\x20-\x7e]{4,}")
UTF16_RE = re.compile(rb"(?:[\x20-\x7e]\x00){4,}")

# Pola shortcut Windows: "Ctrl+Shift+N", "Ctrl+Alt+Del", "F5", "Alt+F4", ...
SHORTCUT_RE = re.compile(
    r"\b(?:Ctrl|Control|Shift|Alt|Ctrl\+Shift|Ctrl\+Alt|Alt\+Shift|"
    r"Ctrl\+Shift\+Alt)\s*\+?\s*"
    r"(?:[A-Z0-9]{1,3}|F(?:[1-9]|1[0-9]|2[0-4])|Del|Ins|Home|End|PgUp|PgDn|"
    r"Space|Backspace|Tab|Enter|Escape|Left|Right|Up|Down)\b",
    re.IGNORECASE,
)

# Kode bahasa ISO 639-1 yang relevan + nama skrip.
LANG_NAMES = {
    "autolang": "Deteksi otomatis",
    "brt": "Breton",
    "brz": "Portugis Brasil",
    "cyrillic": "Cyrillic",
    "dan": "Danska",
    "dut": "Belanda",
    "eng": "Inggris",
    "fin": "Finlandia",
    "frn": "Prancis",
    "greek": "Yunani",
    "grm": "Jerman",
    "handpr": "Tulisan tangan",
    "hebrew": "Ibrani",
    "itl": "Italia",
    "latin": "Latin (huruf latin umum)",
    "nop": "Tanpa operasi (no-op)",
    "nrw": "Norwegia",
    "ocra1": "OCR-A (mesin ketik)",
    "ocrb1": "OCR-B (mesin ketik)",
    "prt": "Portugis",
    "spn": "Spanyol",
    "swd": "Swedia",
}


def extract_strings(data: bytes) -> list[str]:
    found: list[str] = []
    for m in ASCII_RE.finditer(data):
        found.append(m.group().decode("ascii", errors="ignore"))
    for m in UTF16_RE.finditer(data):
        found.append(m.group().decode("utf-16-le", errors="ignore"))
    return found


def main() -> int:
    # ---------------------------------------------------- U-10: bahasa OCR
    ocr_dir = REF / "IRIS_OCR" / "resources"
    ocr_langs: list[dict] = []
    if ocr_dir.is_dir():
        for path in sorted(ocr_dir.iterdir()):
            if path.suffix.lower() not in {".ocr", ".ilex", ".bin"}:
                continue
            stem = path.stem.lower()
            ocr_langs.append(
                {
                    "file": path.name,
                    "key": stem,
                    "nama": LANG_NAMES.get(stem, "(tidak dipetakan)"),
                    "bytes": path.stat().st_size,
                }
            )

    # ------------------------------------------- U-07: pintasan keyboard
    shortcuts: dict[str, list[str]] = {}
    targets = sorted(REF.glob("np_*.dll")) + [REF / "NitroPDF.exe"]
    for target in targets:
        if not target.exists():
            continue
        data = target.read_bytes()
        found: set[str] = set()
        for s in extract_strings(data):
            for m in SHORTCUT_RE.finditer(s):
                found.add(m.group(0).strip())
        if found:
            shortcuts[target.name] = sorted(found, key=str.lower)

    total_shortcuts = sum(len(v) for v in shortcuts.values())
    unique_shortcuts = sorted(
        {s for values in shortcuts.values() for s in values}, key=str.lower
    )

    payload = {
        "ocr_languages": ocr_langs,
        "ocr_language_count": len(ocr_langs),
        "shortcuts_per_module": shortcuts,
        "unique_shortcuts": unique_shortcuts,
        "unique_shortcut_count": len(unique_shortcuts),
        "total_shortcut_occurrences": total_shortcuts,
    }
    (OUT_DIR / "ocr_languages_and_shortcuts_v14.json").write_text(
        json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Bahasa OCR (IRIS_OCR/resources): {len(ocr_langs)}")
    for item in ocr_langs:
        print(f"  {item['file']:20} {item['nama']:22} {item['bytes'] / 1024:9.1f} KB")
    print(f"\nPintasan unik: {len(unique_shortcuts)} (total kemunculan {total_shortcuts})")
    print(", ".join(unique_shortcuts[:60]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
