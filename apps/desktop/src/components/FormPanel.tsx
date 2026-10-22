import { useEffect, useMemo, useState } from "react";
import type { FormField } from "../types";

type Value = string | boolean;

interface Props {
  fields: FormField[] | null;
  loading: boolean;
  busy: boolean;
  onApply: (values: Record<string, Value>) => void;
  onGoToPage: (index: number) => void;
}

function initial(f: FormField): Value {
  if (f.type === "checkbox") return f.value !== "" && f.value !== "Off";
  return f.value === "Off" ? "" : f.value;
}

const SUPPORTED = new Set(["text", "checkbox", "radio", "combo", "list"]);

/** Side panel listing AcroForm fields (read via PDFBox) with editors; applies only changed values. */
export function FormPanel({ fields, loading, busy, onApply, onGoToPage }: Props) {
  const [edits, setEdits] = useState<Record<string, Value>>({});
  useEffect(() => setEdits({}), [fields]);

  const changed = useMemo(() => {
    const out: Record<string, Value> = {};
    for (const f of fields ?? []) {
      if (f.name in edits && edits[f.name] !== initial(f)) out[f.name] = f.type === "radio" && edits[f.name] === "" ? "Off" : edits[f.name];
    }
    return out;
  }, [edits, fields]);

  const set = (name: string, v: Value) => setEdits((e) => ({ ...e, [name]: v }));

  return (
    <aside className="form-panel" aria-label="Panel form">
      <h2>Form</h2>
      {loading && <p className="muted">Membaca field…</p>}
      {fields && fields.length === 0 && <p className="muted">Dokumen tidak memiliki field yang dapat diisi.</p>}
      {fields?.map((f) => {
        const v = f.name in edits ? edits[f.name] : initial(f);
        const disabled = busy || f.read_only || !SUPPORTED.has(f.type);
        const label = (
          <span className="field-name">
            {f.name}
            {f.pages.length > 0 && (
              <button className="link" onClick={() => onGoToPage(f.pages[0])} aria-label={`Ke halaman field ${f.name}`}>
                h.{f.pages[0] + 1}
              </button>
            )}
          </span>
        );
        if (!SUPPORTED.has(f.type)) {
          return (
            <div className="field" key={f.name}>
              {label}
              <span className="muted small">Jenis field “{f.type}” belum didukung</span>
            </div>
          );
        }
        if (f.type === "checkbox") {
          return (
            <label className="field inline" key={f.name}>
              <input type="checkbox" checked={v === true} disabled={disabled} onChange={(e) => set(f.name, e.target.checked)} aria-label={f.name} />
              {label}
            </label>
          );
        }
        if (f.type === "radio") {
          return (
            <fieldset className="field" key={f.name} disabled={disabled}>
              <legend>{label}</legend>
              {(f.options ?? []).map((o) => (
                <label key={o} className="inline">
                  <input type="radio" name={`radio-${f.name}`} checked={v === o} onChange={() => set(f.name, o)} aria-label={`${f.name}: ${o}`} />
                  {o}
                </label>
              ))}
              <label className="inline">
                <input type="radio" name={`radio-${f.name}`} checked={v === ""} onChange={() => set(f.name, "")} aria-label={`${f.name}: kosong`} />
                <span className="muted">(kosong)</span>
              </label>
            </fieldset>
          );
        }
        if (f.type === "combo" || f.type === "list") {
          return (
            <label className="field" key={f.name}>
              {label}
              <select value={String(v)} disabled={disabled} onChange={(e) => set(f.name, e.target.value)} aria-label={f.name}>
                {!(f.options ?? []).includes(String(v)) && <option value={String(v)}>{String(v) || "(kosong)"}</option>}
                {(f.options ?? []).map((o, i) => (
                  <option key={o} value={o}>{f.option_labels?.[i] ?? o}</option>
                ))}
              </select>
            </label>
          );
        }
        return (
          <label className="field" key={f.name}>
            {label}
            <input value={String(v)} disabled={disabled} onChange={(e) => set(f.name, e.target.value)} aria-label={f.name} />
          </label>
        );
      })}
      {fields && fields.length > 0 && (
        <div className="actions">
          <span className="muted small">{Object.keys(changed).length} perubahan</span>
          <button className="primary" disabled={busy || Object.keys(changed).length === 0} onClick={() => onApply(changed)}>
            Terapkan
          </button>
        </div>
      )}
      <p className="muted small">Nilai diterapkan ke dokumen di memori; simpan dengan Simpan Sebagai.</p>
    </aside>
  );
}
