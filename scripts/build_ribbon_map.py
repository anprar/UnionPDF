"""Rekonstruksi hierarki kontrol ribbon v14 dari identifier `AVRibbon:...`.

Konvensi identifier (terverifikasi dari 783 kontrol):
    AVRibbon:<Tipe>:<Tab>[:<Grup>][:<Nama>]

Contoh:
    AVRibbon:Category:Review            -> tab kategori "Review"
    AVRibbon:Panel:Review:Markup        -> panel "Markup" di tab Review
    AVRibbon:Element:Erase:Whiteout     -> elemen "Whiteout" di tab Erase
    AVRibbon:Btn:Forms:CheckBox:Btn     -> tombol CheckBox di tab Forms
    AVRibbon:Categories:CropToolsCRC    -> sub-kategori
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "research" / "ribbon_controls_v14.json"
OUT = ROOT / "docs" / "research" / "V14_RIBBON_STRUCTURE.md"

# Segmen pertama adalah "tipe kontrol", bukan tab.
SCOPES = {
    "Category", "Categories", "Panel", "Element", "SubElement", "Separator",
    "Btn", "Group", "Label", "CheckBox", "Combo", "Edit", "Gallery", "Menu",
    "Radio", "Toggle", "Popup", "DropDown", "Spin", "Slider", "List",
}


def parse(ident: str) -> tuple[str, list[str]]:
    parts = ident.split(":")
    if parts and parts[0] == "AVRibbon":
        parts = parts[1:]
    if not parts:
        return "", []
    scope = parts[0]
    rest = parts[1:]
    if scope not in SCOPES:
        # Tanpa scope eksplisit -> anggap segmen pertama sebagai tab.
        scope = "Control"
        rest = parts
    return scope, [p for p in rest if p]


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))

    # Tab otoritatif diambil dari entri "AVRibbon:Category:<Tab>".
    tabs: set[str] = set()
    for idents in data.values():
        for ident in idents:
            parts = ident.split(":")
            if len(parts) >= 3 and parts[0] == "AVRibbon" and parts[1] == "Category" and parts[2]:
                tabs.add(parts[2])
    if "Home" not in tabs:
        tabs.add("Home")

    # tab -> grup -> set(item)
    tree: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    owner: dict[str, set[str]] = defaultdict(set)
    scopes: dict[str, int] = defaultdict(int)

    for module, idents in data.items():
        for ident in idents:
            scope, parts = parse(ident)
            scopes[scope] += 1
            if not parts:
                continue
            if parts[0] in tabs:
                tab = parts[0]
                rest = parts[1:]
            else:
                # Toolbar kontekstual (mis. Btn:Zoom100) -> bukan tab ribbon.
                tab = "(kontekstual)"
                rest = parts
            group = rest[0] if rest else "(langsung)"
            item = " › ".join(rest[1:]) if len(rest) > 1 else ""
            tree[tab][group].add(item)
            owner[f"{tab}/{group}"].add(module)

    lines: list[str] = []
    lines.append("# Struktur Ribbon Nitro PDF Pro 14.41.0.15")
    lines.append("")
    lines.append("**Status:** DRAFT v1")
    lines.append("**Sumber:** identifier kontrol `AVRibbon:*` yang diekstraksi read-only")
    lines.append("dari 30 modul engine (bukti `E-401`).")
    lines.append("**Ekstraksi:** `scripts/extract_native_strings.py` →")
    lines.append("`scripts/build_ribbon_map.py`")
    lines.append("")
    lines.append("> Rekonstruksi ini **menggantikan** pengamatan UI langsung yang tidak")
    lines.append("> mungkin dilakukan pada instalasi ini. Nama kontrol berasal dari")
    lines.append("> binary build **v14.41.0.15** yang terpasang, jadi berbeda dari")
    lines.append("> dokumentasi versi lain.")
    lines.append("")
    total = sum(len(v) for v in data.values())
    lines.append(f"**{total} kontrol** · **{len(tree)} tab** · "
                 f"**{sum(len(g) for t in tree.values() for g in t.values())} grup**")
    lines.append("")
    lines.append("## Tipe kontrol")
    lines.append("")
    lines.append("| Scope | Jumlah |")
    lines.append("|---|---:|")
    for scope, count in sorted(scopes.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{scope}` | {count} |")
    lines.append("")

    for tab in sorted(tree, key=lambda t: (-sum(len(v) for v in tree[t].values()), t)):
        groups = tree[tab]
        if not groups:
            continue
        lines.append(f"## Tab `{tab}`")
        lines.append("")
        for group in sorted(groups):
            mods = ", ".join(sorted(owner.get(f"{tab}/{group}", [])))
            subs = sorted(x for x in groups[group] if x)
            lines.append(f"### Grup `{group}`")
            lines.append("")
            lines.append(f"- *Modul:* {mods}")
            if subs:
                lines.append("")
                for sub in subs:
                    lines.append(f"  - {sub}")
            lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Tertulis: {OUT}")
    print(f"\nTab yang teridentifikasi ({len(tree)}):")
    for tab in sorted(tree, key=lambda t: (-sum(len(v) for v in tree[t].values()), t)):
        n = sum(len(v) for v in tree[tab].values())
        print(f"  {tab:16} kontrol={n:4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
