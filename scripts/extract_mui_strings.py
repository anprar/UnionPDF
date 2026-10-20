"""Ekstraksi string sumber daya RT_STRING dari berkas .mui (read-only).

Berguna untuk memetakan teks UI **sebenarnya** dari aplikasi referensi
versi 14.41.0.15, termasuk label dialog, opsi, dan pesan error.

Read-only: berkas hanya dibaca, tidak pernah ditulis.

Jalankan: .venv\\Scripts\\python.exe scripts\\extract_mui_strings.py
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REF = Path(r"C:\Program Files\Nitro\PDF Pro\14")
MUI_DIR = REF / "en-US"
OUT = Path(__file__).resolve().parents[1] / "docs" / "research" / "mui_strings_en-US.json"

RT_STRING = 6


class PEError(RuntimeError):
    pass


def read_u16(data: bytes, off: int) -> int:
    return struct.unpack_from("<H", data, off)[0]


def read_u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def rva_to_offset(sections: list[tuple[int, int, int, int]], rva: int) -> int:
    for va, vsize, raw_ptr, raw_size in sections:
        if va <= rva < va + max(vsize, raw_size):
            return raw_ptr + (rva - va)
    raise PEError(f"RVA 0x{rva:x} tidak berada di section manapun")


def parse_sections(data: bytes) -> tuple[list[tuple[int, int, int, int]], int]:
    e_lfanew = read_u32(data, 0x3C)
    if data[e_lfanew : e_lfanew + 4] != b"PE\x00\x00":
        raise PEError("bukan berkas PE")
    coff = e_lfanew + 4
    num_sections = read_u16(data, coff + 2)
    opt_size = read_u16(data, coff + 16)
    opt = coff + 20
    magic = read_u16(data, opt)
    if magic == 0x20B:  # PE32+
        dd_offset = opt + 112
    elif magic == 0x10B:  # PE32
        dd_offset = opt + 96
    else:
        raise PEError(f"optional header magic tidak dikenal: 0x{magic:x}")
    res_rva = read_u32(data, dd_offset + 2 * 8)
    res_size = read_u32(data, dd_offset + 2 * 8 + 4)

    sections = []
    sec_table = opt + opt_size
    for i in range(num_sections):
        off = sec_table + i * 40
        vsize = read_u32(data, off + 8)
        va = read_u32(data, off + 12)
        raw_size = read_u32(data, off + 16)
        raw_ptr = read_u32(data, off + 20)
        sections.append((va, vsize, raw_ptr, raw_size))
    return sections, res_rva


def walk_resource_dir(
    data: bytes,
    sections: list[tuple[int, int, int, int]],
    root_offset: int,
    dir_offset: int,
    level: int,
    type_id: int | None,
    name_id: int | None,
    out: list[tuple[int, int, int]],
) -> None:
    """Kumpulkan (type_id, name_id, data_entry_offset) untuk semua daun.

    Offset subdirektori pada PE relatif terhadap **root** resource directory,
    bukan terhadap direktori saat ini.
    """
    number_of_named = read_u16(data, dir_offset + 12)
    number_of_id = read_u16(data, dir_offset + 14)
    total = number_of_named + number_of_id

    for i in range(total):
        entry = dir_offset + 16 + i * 8
        name = read_u32(data, entry)
        offset = read_u32(data, entry + 4)

        current_type = name if level == 0 else type_id
        current_name = name if level == 1 else name_id

        if offset & 0x80000000:
            sub = offset & 0x7FFFFFFF
            walk_resource_dir(
                data,
                sections,
                root_offset,
                root_offset + sub,
                level + 1,
                current_type,
                current_name,
                out,
            )
        else:
            out.append((current_type, current_name, root_offset + offset))


def extract_rt_string(data: bytes, payload: bytes) -> list[str]:
    """Payload RT_STRING berisi 16 string UTF-16 panjang-berhitung."""
    strings: list[str] = []
    pos = 0
    for _ in range(16):
        if pos + 2 > len(payload):
            break
        length = read_u16(payload, pos)
        pos += 2
        if length:
            chunk = payload[pos : pos + length * 2]
            pos += length * 2
            try:
                strings.append(chunk.decode("utf-16-le"))
            except UnicodeDecodeError:
                strings.append(chunk.decode("utf-16-le", errors="replace"))
        else:
            strings.append("")
    return strings


def extract_from_mui(path: Path) -> dict:
    data = path.read_bytes()
    sections, res_rva = parse_sections(data)
    if not res_rva:
        return {"file": path.name, "error": "tidak ada resource table", "strings": []}

    root_off = rva_to_offset(sections, res_rva)
    leaves: list[tuple[int, int, int]] = []
    walk_resource_dir(data, sections, root_off, root_off, 0, None, None, leaves)

    strings: list[tuple[str, str]] = []  # (resource_id, text)
    for type_id, name_id, data_entry in leaves:
        if type_id != RT_STRING:
            continue
        payload_rva = read_u32(data, data_entry)
        payload_size = read_u32(data, data_entry + 4)
        try:
            payload_off = rva_to_offset(sections, payload_rva)
        except PEError:
            continue
        payload = data[payload_off : payload_off + payload_size]
        block = (name_id - 1) // 16
        base = (name_id - 1) % 16
        for idx, text in enumerate(extract_rt_string(data, payload)):
            if text.strip():
                strings.append((f"{block}:{base + idx}", text))
    return {"file": path.name, "count": len(strings), "strings": strings}


def main() -> int:
    if not MUI_DIR.is_dir():
        print(f"Folder tidak ditemukan: {MUI_DIR}")
        return 1

    result: dict[str, dict] = {}
    total = 0
    for mui in sorted(MUI_DIR.glob("*.mui")):
        info = extract_from_mui(mui)
        result[mui.name] = info
        total += info.get("count", 0)
        print(f"{mui.name:42} {info.get('count', 0):6} string")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nTotal: {total} string UI -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
