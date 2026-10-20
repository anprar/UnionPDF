"""Ekstraksi string dari DLL/EXE aplikasi referensi (read-only) + rekonstruksi
struktur ribbon v14.

Tujuan:
  1. Menemukan identifier kontrol ribbon (`AVRibbon:...`) untuk memetakan
     struktur UI v14.41.0.15 secara presisi.
  2. Mengumpulkan string fitur (perintah, profiler, event) per modul.

Read-only terhadap folder referensi. Menulis hanya ke docs/research/.

Jalankan: .venv\\Scripts\\python.exe scripts\\extract_native_strings.py
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

ASCII_RE = re.compile(rb"[\x20-\x7e]{6,}")
UTF16_RE = re.compile(rb"(?:[\x20-\x7e]\x00){5,}")

RIBBON_RE = re.compile(r"^AVRibbon:")
CMD_RE = re.compile(r"^AVCmd|^AVPlugin|^Pro[A-Z]|^On[A-Z]")
PLUGIN_RE = re.compile(r"^[a-z_]+::[a-z_]+$")


def extract_strings(data: bytes) -> list[str]:
    found: list[str] = []
    for m in ASCII_RE.finditer(data):
        try:
            found.append(m.group().decode("ascii"))
        except UnicodeDecodeError:
            pass
    for m in UTF16_RE.finditer(data):
        try:
            found.append(m.group().decode("utf-16-le"))
        except UnicodeDecodeError:
            pass
    return found


def main() -> int:
    targets = sorted(REF.glob("np_*.dll")) + [REF / "NitroPDF.exe"]
    ribbon: dict[str, list[str]] = {}
    features: dict[str, list[str]] = {}

    for target in targets:
        if not target.exists():
            continue
        try:
            data = target.read_bytes()
        except OSError:
            continue
        strings = extract_strings(data)

        ribs = sorted({s for s in strings if RIBBON_RE.match(s)})
        if ribs:
            ribbon[target.name] = ribs

        feats = sorted(
            {
                s
                for s in strings
                if len(s) < 120 and (CMD_RE.match(s) or PLUGIN_RE.match(s))
            }
        )
        if feats:
            features[target.name] = feats

        print(f"{target.name:34} ribbon={len(ribs):4}  fitur={len(feats):4}")

    (OUT_DIR / "ribbon_controls_v14.json").write_text(
        json.dumps(ribbon, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "native_feature_ids_v14.json").write_text(
        json.dumps(features, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nTotal kontrol ribbon : {sum(len(v) for v in ribbon.values())}")
    print(f"Total identifier fitur: {sum(len(v) for v in features.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
