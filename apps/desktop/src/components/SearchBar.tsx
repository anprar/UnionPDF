import { useEffect, useRef, useState } from "react";
import { IconChevronDown, IconSearch } from "./icons";

export interface SearchHit {
  page: number;
  text: string;
  left: number;
  top: number;
  width: number;
  height: number;
}

interface Props {
  open: boolean;
  query: string;
  hits: SearchHit[];
  activeIndex: number;
  searching: boolean;
  caseSensitive: boolean;
  onQuery: (q: string) => void;
  onNext: () => void;
  onPrevious: () => void;
  onClose: () => void;
  onToggleCase: () => void;
  onCancel: () => void;
}

/** Search bar: query, hit counter, next/previous, case sensitivity, cancel and close. */
export function SearchBar(p: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [focused, setFocused] = useState(true);

  useEffect(() => {
    if (p.open) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [p.open]);

  if (!p.open) return null;
  const total = p.hits.length;
  const position = total > 0 ? `${p.activeIndex + 1} dari ${total}` : total === 0 && p.query ? "Tidak ada hasil" : "";

  return (
    <div className="searchbar" role="search" aria-label="Cari teks dalam dokumen">
      <IconSearch />
      <input
        ref={inputRef}
        className="search-input"
        value={p.query}
        placeholder="Cari teks…"
        aria-label="Kata kunci pencarian"
        onChange={(e) => p.onQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            if (e.shiftKey) p.onPrevious();
            else p.onNext();
          } else if (e.key === "Escape") {
            e.preventDefault();
            p.onClose();
          }
        }}
        onFocus={() => setFocused(true)}
      />
      <span className="search-count" aria-live="polite">
        {p.searching ? "Mencari…" : position}
      </span>
      <button className="icon-btn" onClick={p.onPrevious} disabled={total === 0} title="Hasil sebelumnya (Shift+Enter)" aria-label="Hasil sebelumnya">
        <IconChevronDown className="flip" />
      </button>
      <button className="icon-btn" onClick={p.onNext} disabled={total === 0} title="Hasil berikutnya (Enter)" aria-label="Hasil berikutnya">
        <IconChevronDown />
      </button>
      <button
        className={`cmd-btn ${p.caseSensitive ? "active" : ""}`}
        aria-pressed={p.caseSensitive}
        onClick={p.onToggleCase}
        title="PCocokkan huruf besar/kecil"
        aria-label="PCocokkan huruf besar kecil"
      >
        <span>Aa</span>
      </button>
      {p.searching && (
        <button className="cmd-btn" onClick={p.onCancel} title="Batalkan pencarian">
          <span>Batalkan</span>
        </button>
      )}
      <button className="icon-btn" onClick={p.onClose} title="Tutup pencarian (Esc)" aria-label="Tutup pencarian">
        ×
      </button>
      {focused && <span className="visually-hidden">Pencarian aktif</span>}
    </div>
  );
}
