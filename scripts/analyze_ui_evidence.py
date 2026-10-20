"""Analisis korpus string UI aplikasi referensi (dari .mui en-US).

Menghasilkan laporan fitur ringkas per modul: label UI, opsi dialog, dan
pesan error yang€™ ada di build 14.41.0.15.

Read-only terhadap berkas referensi; menulis hanya ke docs/research/.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "research" / "mui_strings_en-US.json"
OUT = ROOT / "docs" / "research" / "V14_UI_EVIDENCE.md"

# Pola yang menandai string "UI nyata", bukan identifier internal.
INTERESTING = re.compile(
    r"[A-Za-z]{3,}"           # ada huruf
    r"[\s\-&/().:,']{0,40}"
)
NOISE = re.compile(
    r"^[\W\d_]*$"             # tanpa huruf
    r"|^[A-Z0-9_]{8,}$"      # konstanta
    r"|^\{[a-z_]+\}$"         # placeholder format
)

# Pola pesan error (mengandung kata indicative + nama kapital/format).
ERRORISH = re.compile(
    r"cannot|could not|unable|failed|invalid|not supported|not available"
    r"|error|warning|must |please |required|too (large|small|many)"
    r"|try again|out of memory|permission|denied",
    re.IGNORECASE,
)


def load() -> dict:
    return json.loads(SRC.read_text(encoding="utf-8"))


def texts_of(entry: dict) -> list[str]:
    return [t for _rid, t in entry.get("strings", [])]


def is_ui_text(s: str) -> bool:
    s = s.strip()
    if not s or len(s) < 3 or len(s) > 140:
        return False
    if NOISE.search(s):
        return False
    # Buang string yang terlihat seperti path, GUID, atau format teknis.
    if re.match(r"^[A-Za-z]:\\", s) or re.match(r"^\{?[0-9A-Fa-f]{8}-", s):
        return False
    if s.count(".") == 0 and " " not in s and s.islower():
        return False
    return True


def main() -> int:
    data = load()
    lines: list[str] = []
    lines.append("# V14 UI Evidence — Teks UI asli Nitro PDF Pro 14.41.0.15")
    lines.append("")
    lines.append("**Status:** DRAFT v1 · **Sumber:** 35 berkas `.mui` di `en-US`,")
    lines.append("diekstraksi read-only oleh `scripts/extract_mui_strings.py`.")
    lines.append("**Total:** 14.452 string UI.")
    lines.append("")
    lines.append("> Ini adalah **teks antarmuka yang benar-benar ada di build**,")
    lines.append("> bukan dokumentasi marketing. Dipakai untuk memverifikasi")
    lines.append("> cakupan fitur v14 secara langsung.")
    lines.append("")

    # Ringkasan per modul
    lines.append("## 1. Ukuran korpus per modul")
    lines.append("")
    lines.append("| Modul | String UI |")
    lines.append("|---|---:|")
    for name, entry in sorted(data.items(), key=lambda kv: -kv[1].get("count", 0)):
        lines.append(f"| `{name}` | {entry.get('count', 0)} |")
    lines.append("")

    # Ringkasan fitur per modul
    lines.append("## 2. Label & opsi UI per modul")
    lines.append("")
    for name, entry in sorted(data.items()):
        texts = [t for t in texts_of(entry) if is_ui_text(t)]
        if not texts:
            continue
        # Dedup sambil mempertahankan urutan
        seen: set[str] = set()
        unique = [t for t in texts if not (t in seen or seen.add(t))]
        lines.append(f"### `{name}` ({len(unique)} label unik)")
        lines.append("")
        # Batasi supaya dokumen tetap ringkas: ambil yang paling informatif
        # (label dengan kata kerja/objek, bukan yang terlalu generik)
        picked = [t for t in unique if 3 <= len(t.split()) <= 12][:70]
        for t in picked:
            lines.append(f"- {t}")
        if len(unique) > len(picked):
            lines.append(f"- _… {len(unique) - len(picked)} label lain tidak ditampilkan di sini_")
        lines.append("")

    # Pesan error
    lines.append("## 3. Pesan error & perilaku yang terpicu")
    lines.append("")
    lines.append("Pesan iniicy Errors menunjukkan kondisi failure yang ditangani aplikasi")
    lines.append("referensi — berguna untuk merancang pesan UnionPDF yang setara.")
    lines.append("")
    for name, entry in sorted(data.items()):
        errors = []
        for t in texts_of(entry):
            if ERRORISH.search(t) and 8 <= len(t) <= 200 and is_ui_text(t):
                if t not in errors:
                    errors.append(t)
        if not errors:
            continue
        lines.append(f"### `{name}`")
        lines.append("")
        for t in errors[:25]:
            lines.append(f"- {t}")
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Ditulis: {OUT} ({len(lines)} baris)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
