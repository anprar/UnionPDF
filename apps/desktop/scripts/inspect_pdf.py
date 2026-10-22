"""Pembaca independen (PyMuPDF) untuk verifikasi output E2E. Mencetak JSON ringkas.

    python inspect_pdf.py <file.pdf>
"""

import json
import sys

import pymupdf


def main(path: str) -> int:
    try:
        doc = pymupdf.open(path)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"open_error": f"{type(e).__name__}: {e}"}))
        return 0
    fields = []
    annots = []
    for i, page in enumerate(doc):
        for w in page.widgets():
            ap = doc.xref_get_key(w.xref, "AP/N")
            ap_text = ""
            if ap[0] == "xref":
                ap_text = (doc.xref_stream(int(ap[1].split()[0])) or b"").decode("latin-1")
            fields.append({"name": w.field_name, "type": w.field_type_string, "value": w.field_value,
                           "page": i, "ap_contains_value": bool(w.field_value) and str(w.field_value) in ap_text})
        for a in page.annots():
            annots.append({"page": i, "type": a.type[1], "has_ap": doc.xref_get_key(a.xref, "AP")[0] != "null"})
    out = {
        "page_count": doc.page_count,
        "text": "\n".join(p.get_text("text") for p in doc),
        "rotations": [p.rotation for p in doc],
        "toc": doc.get_toc(simple=True),
        "links": [{"page": i, "to": ln.get("page")} for i, p in enumerate(doc) for ln in p.get_links()
                  if ln.get("kind") == pymupdf.LINK_GOTO],
        "fields": fields,
        "annotations": annots,
        "is_repaired": doc.is_repaired,
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
