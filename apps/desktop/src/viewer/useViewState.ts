import { useEffect, useRef } from "react";
import * as api from "../api";

export interface ViewState {
  mode: string;
  scrollTop: number;
  scrollHeight: number;
  clientWidth: number;
  clientHeight: number;
  pageCount: number;
  /** Page indices currently rendered in the viewport. */
  renderedPages: number[];
  zoomPercent: number;
  activePage: number;
}

/**
 * Reports the viewport state to the backend (throttled). The backend keeps the last report so
 * automated UI tests can verify the continuous scrolling objectively (scroll height, rendered
 * page range) without simulating mouse input.
 */
export function useViewStateReporter(el: React.RefObject<HTMLElement | null>, build: () => ViewState, enabled: boolean) {
  const timer = useRef(0);
  const last = useRef(0);

  useEffect(() => {
    if (!enabled) return;
    const send = (force = false) => {
      const now = Date.now();
      if (!force && now - last.current < 250) return;
      last.current = now;
      api.reportViewState(build()).catch(() => undefined);
    };
    const node = el.current;
    const onScroll = () => {
      if (timer.current) return;
      timer.current = window.setTimeout(() => {
        timer.current = 0;
        send();
      }, 120);
    };
    node?.addEventListener("scroll", onScroll, { passive: true });
    send(true);
    const interval = window.setInterval(() => send(), 1000);
    return () => {
      node?.removeEventListener("scroll", onScroll);
      if (timer.current) window.clearTimeout(timer.current);
      window.clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [el, enabled]);
}
