import { useEffect, useRef, useState } from "react";
import { cancelJob, searchDocument } from "../api";
import type { SearchHit } from "./SearchBar";

interface Props {
  hits: SearchHit[];
  activeIndex: number;
  cssScale: number;
}

/** Highlight overlay for the search hits of the visible page(s). */
export function SearchHighlights({ hits, activeIndex, cssScale }: Props) {
  return (
    <>
      {hits.map((h, i) => (
        <div
          key={`${h.page}-${i}-${h.left}`}
          className={`search-hit ${i === activeIndex ? "active" : ""}`}
          style={{
            left: h.left * cssScale,
            top: h.top * cssScale,
            width: h.width * cssScale,
            height: h.height * cssScale,
          }}
        />
      ))}
    </>
  );
}

/** Debounced search over the whole document; a running search is cancelled when the query changes. */
export function useSearch(docId: number | null, revision: number) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [searching, setSearching] = useState(false);
  const [caseSensitive, setCaseSensitive] = useState(false);
  const jobRef = useRef<string | null>(null);
  const seq = useRef(0);

  // Results belong to a document revision: drop them when it changes.
  useEffect(() => {
    setHits([]);
    setActiveIndex(0);
  }, [docId, revision]);

  const run = async (q: string, cs: boolean) => {
    const my = ++seq.current;
    if (jobRef.current) {
      await cancelJob(jobRef.current).catch(() => undefined);
      jobRef.current = null;
    }
    if (!docId || q.trim().length === 0) {
      setHits([]);
      setSearching(false);
      return;
    }
    const jobId = crypto.randomUUID();
    jobRef.current = jobId;
    setSearching(true);
    try {
      const res = await searchDocument(docId, q, cs, jobId);
      if (my !== seq.current) return;
      setHits(res);
      setActiveIndex((i) => (res.length > 0 ? Math.min(i, res.length - 1) : 0));
    } catch {
      if (my === seq.current) setHits([]);
    } finally {
      if (my === seq.current) setSearching(false);
      if (jobRef.current === jobId) jobRef.current = null;
    }
  };

  useEffect(() => {
    const t = window.setTimeout(() => void run(query, caseSensitive), 250);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, caseSensitive, docId, revision]);

  const cancel = async () => {
    seq.current++;
    if (jobRef.current) {
      await cancelJob(jobRef.current).catch(() => undefined);
      jobRef.current = null;
    }
    setSearching(false);
  };

  return {
    query,
    setQuery,
    hits,
    activeIndex,
    setActiveIndex,
    searching,
    caseSensitive,
    setCaseSensitive,
    cancel,
  };
}
