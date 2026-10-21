"""Verifikasi angka yang dikutip di `docs/ANALYSIS_NITRO14.md`.

Membaca korporas hasil ekstraksi read-only di `docs/research/` lalu
memastikan angka kunci pada dokumen analisis tetap cocok dengan data.

Jalankan: .venv\\Scripts\\python.exe scripts\\verify_analysis_corpus.py

Exit code 0 = semua angka cocok, 1 = ada yang meleset.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs" / "research"

# Angka yang dikutip di docs/ANALYSIS_NITRO14.md -> nilai yang diharapkan
EXPECTED = {
    "jumlah_berkas_mui": 36,
    "total_string_ui": 14452,
    "total_kontrol_ribbon": 783,
    # 13 tab bernama. Angka 14 pada dokumen lama menghitung bucket
    # "(kontekstual)" sebagai tab; itu bukan tab ribbon.
    "total_tab_ribbon": 13,
    "total_identifier_fitur": 10284,
    "bahasa_ocr_model": 20,
    "grup_kontekstual": 228,
    "placeholder_dummy": 12,
}


def main() -> int:
    mui = json.loads((RESEARCH / "mui_strings_en-US.json").read_text(encoding="utf-8"))
    ribbon = json.loads((RESEARCH / "ribbon_controls_v14.json").read_text(encoding="utf-8"))
    feat = json.loads((RESEARCH / "native_feature_ids_v14.json").read_text(encoding="utf-8"))
    ocr = json.loads(
        (RESEARCH / "ocr_languages_and_shortcuts_v14.json").read_text(encoding="utf-8")
    )

    tabs = set()
    for idents in ribbon.values():
        for ident in idents:
            parts = ident.split(":")
            if len(parts) >= 3 and parts[1] == "Category" and parts[2]:
                tabs.add(parts[2])

    konteks = set()
    for idents in ribbon.values():
        for ident in idents:
            bagian = ident.split(":")[1:]
            if not bagian:
                continue
            scope = bagian[0]
            sisa = [p for p in bagian[1:] if p]
            if not sisa:
                continue
            if sisa[0] not in tabs:
                konteks.add(sisa[0])

    # Model bahasa nyata: kunci .ocr/.ilex dikurangi autolang + nop (no-op).
    lang_keys = {
        item["key"]
        for item in ocr.get("ocr_languages", [])
        if item["file"].lower().endswith((".ocr", ".ilex"))
    }
    model_bahasa = len(lang_keys - {"autolang", "nop"})

    aktual = {
        "jumlah_berkas_mui": len(mui),
        "total_string_ui": sum(len(e.get("strings", [])) for e in mui.values()),
        "total_kontrol_ribbon": sum(len(v) for v in ribbon.values()),
        "total_tab_ribbon": len(tabs),
        "total_identifier_fitur": sum(len(v) for v in feat.values()),
        "bahasa_ocr_model": model_bahasa,
        "grup_kontekstual": len(konteks),
        "placeholder_dummy": sum(1 for g in konteks if g.startswith("Dummy")),
    }

    gagal = 0
    for kunci, diharapkan in EXPECTED.items():
        nilai = aktual.get(kunci)
        ok = nilai == diharapkan
        gagal += 0 if ok else 1
        print(f"  [{'OK ' if ok else 'GAGAL'}] {kunci:26} diharapkan={diharapkan:<8} aktual={nilai}")

    if gagal:
        print(f"\n{gagal} angka tidak cocok.")
        return 1
    print("\nSeluruh angka pada docs/ANALYSIS_NITRO14.md cocok dengan korporas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
