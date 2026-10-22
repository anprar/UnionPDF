import { useRef, useState } from "react";
import { IconAutoScroll, IconChevronDown, IconChevronUp } from "./icons";

export type ScrollDirection = "down" | "up";

interface Props {
  open: boolean;
  running: boolean;
  direction: ScrollDirection;
  /** Pixels per second at speed 1. */
  speed: number;
  paused: boolean;
  /** True when the document cannot scroll further in the current direction. */
  atEdge: boolean;
  onToggle: () => void;
  onDirection: (d: ScrollDirection) => void;
  onSpeed: (s: number) => void;
  onClose: () => void;
}

/**
 * Auto-scroll control: explicit direction buttons (up/down), start/pause, speed slider and the
 * current speed value. The speed is expressed in pixels per second and applied by the parent,
 * which owns the single timer.
 */
export function AutoScrollControl(p: Props) {
  const [local, setLocal] = useState(p.speed);
  const last = useRef(p.speed);
  if (last.current !== p.speed) {
    last.current = p.speed;
    setLocal(p.speed);
  }
  if (!p.open) return null;
  const stopped = p.atEdge && !p.paused;
  return (
    <div className="autoscroll" role="group" aria-label="Gulir otomatis">
      <IconAutoScroll />
      <div className="autoscroll-dir" role="group" aria-label="Arah gulir">
        <button
          className={`cmd-btn ${p.direction === "up" ? "active" : ""}`}
          aria-pressed={p.direction === "up"}
          aria-label="Gulir ke atas"
          title="Gulir ke atas (ke halaman sebelumnya)"
          disabled={p.running && p.atEdge}
          onClick={() => p.onDirection("up")}
        >
          <IconChevronUp /> <span>Naik</span>
        </button>
        <button
          className={`cmd-btn ${p.direction === "down" ? "active" : ""}`}
          aria-pressed={p.direction === "down"}
          aria-label="Gulir ke bawah"
          title="Gulir ke bawah (ke halaman berikutnya)"
          disabled={p.running && p.atEdge}
          onClick={() => p.onDirection("down")}
        >
          <IconChevronDown /> <span>Turun</span>
        </button>
      </div>
      <button
        className={`icon-btn ${p.running ? "active" : ""}`}
        onClick={p.onToggle}
        aria-pressed={p.running}
        aria-label={p.running ? "Jeda gulir otomatis" : "Mulai gulir otomatis"}
        title={p.running ? "Jeda" : "Mulai"}
        disabled={stopped}
      >
        {p.running ? "❚❚" : "▶"}
      </button>
      <input
        className="speed-slider"
        type="range"
        min={0.2}
        max={4}
        step={0.1}
        value={local}
        onChange={(e) => {
          const v = Number(e.target.value);
          setLocal(v);
          p.onSpeed(v);
        }}
        aria-label="Kecepatan gulir otomatis"
        title="Kecepatan (piksel per detik)"
      />
      <span className="speed-value" aria-live="polite">
        {local.toFixed(1)}×
      </span>
      {p.paused && <span className="muted small">jeda</span>}
      {stopped && <span className="muted small">ujung dokumen</span>}
      <button className="icon-btn" onClick={p.onClose} aria-label="Tutup gulir otomatis" title="Tutup">
        ×
      </button>
    </div>
  );
}
