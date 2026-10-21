"""Verifikasi angka yang dikutip di `docs/ANALYSIS_STIRLING_PDF.md`.

Menghitung ulang angka kunci langsung dari artefak Stirling-PDF, lalu
mencocokkannya dengan nilai yang tertulis di dokumen.

Artefak yang dibutuhkan (hasil ekstraksi MSI, read-only):
  - fat JAR  : libs/stirling-pdf-3.2.0.jar
  - shell EXE : Stirling-PDF.exe   (opsional, untuk hitungan string)

Jalankan:
  .venv\\Scripts\\python.exe scripts\\verify_stirling_artifact.py <path-jar> [path-exe]

Exit code 0 = semua angka cocok, 1 = ada yang meleset.
"""

from __future__ import annotations

import re
import struct
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Nilai yang dikutip di docs/ANALYSIS_STIRLING_PDF.md
EXPECTED = {
    "entri_zip_jar": 1136,
    "dependency_jar": 248,
    "class_aplikasi": 476,
    "class_controller": 177,
    "class_model": 153,
    "class_service": 88,
    "class_config": 36,
    "entri_modul_common": 470,
    "jalur_api_literal": 47,
}

ASCII_RE = re.compile(rb"[\x20-\x7e]{5,}")
UTF16_RE = re.compile(rb"(?:[\x20-\x7e]\x00){5,}")
SIZES = {3: 4, 4: 4, 5: 8, 6: 8, 7: 2, 8: 2, 9: 4, 10: 4, 11: 4, 12: 4,
         15: 3, 16: 2, 17: 4, 18: 4, 19: 2, 20: 2}


def utf8_constants(data: bytes) -> list[str]:
    """Ambil seluruh CONSTANT_Utf8 dari satu class file Java."""
    if len(data) < 10 or data[:4] != b"\xca\xfe\xba\xbe":
        return []
    count = struct.unpack_from(">H", data, 8)[0]
    pos, out, i = 10, [], 1
    while i < count:
        tag = data[pos]
        pos += 1
        if tag == 1:
            ln = struct.unpack_from(">H", data, pos)[0]
            pos += 2
            out.append(data[pos:pos + ln].decode("utf-8", "replace"))
            pos += ln
        else:
            size = SIZES.get(tag)
            if size is None:
                return out
            pos += size
        i += 2 if tag in (5, 6) else 1
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    jar = Path(sys.argv[1])
    if not jar.is_file():
        print(f"Berkas tidak ditemukan: {jar}")
        return 2

    with zipfile.ZipFile(jar) as z:
        entries = z.namelist()
        dep = [e for e in entries if e.startswith("BOOT-INF/lib/") and e.endswith(".jar")]
        classes: dict[str, list[str]] = {}
        for name in entries:
            if name.startswith("BOOT-INF/classes/") and name.endswith(".class"):
                with z.open(name) as fh:
                    classes[name[len("BOOT-INF/classes/"):-6].replace("/", ".")] = utf8_constants(fh.read())
        common = [e for e in entries if e == "BOOT-INF/lib/common-3.2.0-plain.jar"]
        common_entries = 0
        if common:
            with z.open(common[0]) as fh:
                data = fh.read()
            import io

            with zipfile.ZipFile(io.BytesIO(data)) as cz:
                common_entries = len(cz.namelist())

    paths = {c for consts in classes.values() for c in consts
             if c.startswith("/api/v") or "api/v1/" in c}

    aktual = {
        "entri_zip_jar": len(entries),
        "dependency_jar": len(dep),
        "class_aplikasi": len(classes),
        "class_controller": sum(1 for k in classes if ".controller." in k),
        "class_model": sum(1 for k in classes if ".model." in k),
        "class_service": sum(1 for k in classes if ".service." in k),
        "class_config": sum(1 for k in classes if ".config." in k),
        "entri_modul_common": common_entries,
        "jalur_api_literal": len(paths),
    }

    gagal = 0
    for kunci, diharapkan in EXPECTED.items():
        nilai = aktual.get(kunci)
        ok = nilai == diharapkan
        gagal += 0 if ok else 1
        print(f"  [{'OK ' if ok else 'GAGAL'}] {kunci:22} diharapkan={diharapkan:<8} aktual={nilai}")

    if len(sys.argv) > 2:
        exe = Path(sys.argv[2])
        if exe.is_file():
            data = exe.read_bytes()
            n = len(ASCII_RE.findall(data)) + len(UTF16_RE.findall(data))
            print(f"  [{'OK ' if n == 344413 else 'PERIKSA'}] kemunculan_string_exe "
                  f"diharapkan=344413  aktual={n}")
        else:
            print(f"  [PERIKSA] shell EXE tidak ditemukan: {exe}")

    if gagal:
        print(f"\n{gagal} angka tidak cocok.")
        return 1
    print("\nSeluruh angka pada docs/ANALYSIS_STIRLING_PDF.md cocok dengan artefak.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
