"""Linter workspace UnionPDF.

Memeriksa:
  1. Mojibake / karakter non-Latin yang tersisip (bug yang pernah terjadi).
  2. Tautan markdown relatif ke file lokal yang tidak ada.
  3. Placeholder yang tertinggal ("lorem ipsum", "TBD!", "FIXME").

Jalankan: .venv\\Scripts\\python.exe scripts\\lint.py
Keluar dengan kode 1 bila ada temuan.
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP_DIRS = {".venv", "node_modules", ".git", "spikes", "out", "__pycache__"}

# Dependency/vendor/cache pihak ketiga dan output build — path eksplisit (relatif ke ROOT).
# Sengaja TIDAK memakai "semua file gitignored": source proyek yang penting tetap dipindai.
VENDOR_PREFIXES = (
    "experiments/restart/.cargo-home/",
    "experiments/restart/deps/pdfium/",
    "experiments/restart/deps/download/",
    "experiments/restart/deps/pdfbox/",
    "experiments/restart/pdfium-spike/target/",
    "experiments/restart/pdfbox-spike/build/",
    "experiments/restart/raw/",
    "experiments/restart/fixtures/generated/",
    "apps/desktop/src-tauri/target/",
    "apps/desktop/src-tauri/pdfium/",
    "apps/desktop/src-tauri/worker/",
    "apps/desktop/dist-package/",
    "apps/desktop/.toolchain/",
    "apps/desktop/dist/",
    "apps/desktop/.cargo-home/",
    "apps/desktop/src-tauri/gen/",
    "apps/desktop/src-tauri/icons/",
    ".cargo-home/",
)

HANGUL_CJK = re.compile(r"[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7af\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
LINK_MD = re.compile(r"\[[^\]]*\]\((?!https?://|mailto:)([^)#]+)(?:#[^)]*)?\)")
PLACEHOLDERS = re.compile(r"\blorem ipsum\b|\bTBD!|\bFIXME\b", re.IGNORECASE)
PLACEHOLDER_UPPER = re.compile(r"\bXXX\b")

# Berkas yang boleh memuat karakter non-Latin secara wajar (data sintetis).
ALLOW_FILES = {"scripts/repair_docs.py", "scripts/lint.py"}


def iter_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = [ROOT / "AGENTS.md", ROOT / "README.md"]
    for pattern in ("*.md", "*.py", "*.ps1", "*.txt", "*.toml", "*.ini"):
        files += sorted(ROOT.rglob(pattern))
    out = []
    for f in files:
        if not f.exists():
            continue
        if SKIP_DIRS & set(f.relative_to(ROOT).parts):
            continue
        if f.relative_to(ROOT).as_posix().startswith(VENDOR_PREFIXES):
            continue
        out.append(f)
    return out


def main() -> int:
    findings = 0
    for path in iter_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOW_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"[encoding] {rel}: bukan UTF-8")
            findings += 1
            continue

        for n, line in enumerate(text.splitlines(), 1):
            if HANGUL_CJK.search(line):
                print(f"[mojibake] {rel}:{n}: {line.strip()[:90]}")
                findings += 1
            if PLACEHOLDERS.search(line):
                print(f"[placeholder] {rel}:{n}: {line.strip()[:90]}")
                findings += 1
            if PLACEHOLDER_UPPER.search(line):
                print(f"[placeholder] {rel}:{n}: {line.strip()[:90]}")
                findings += 1

        if path.suffix == ".md":
            for m in LINK_MD.finditer(text):
                target = m.group(1).strip()
                if not target:
                    continue
                if not (path.parent / target).resolve().exists():
                    if not (ROOT / target).resolve().exists():
                        print(f"[link-mati] {rel}: -> {target}")
                        findings += 1

    print(f"\nlint: {findings} temuan")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
