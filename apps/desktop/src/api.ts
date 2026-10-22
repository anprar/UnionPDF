import { invoke } from "@tauri-apps/api/core";
import type { AnnotationRequest, ApiError, DocInfo, EngineStatus, FormField, OpResult, OutlineNode, Preflight, RenderedPage, SearchHit, TextSpan } from "./types";

export function toApiError(e: unknown): ApiError {
  if (e && typeof e === "object" && "message" in e) {
    const o = e as { code?: string; message: string };
    return { code: o.code ?? "unknown", message: o.message };
  }
  return { code: "unknown", message: String(e) };
}

export const engineStatus = () => invoke<EngineStatus>("engine_status");

export const openDocument = (path: string) => invoke<DocInfo>("open_document", { path });

export const closeDocument = (docId: number) => invoke<void>("close_document", { docId });

export const rotatePages = (docId: number, pages: number[], delta: number) =>
  invoke<DocInfo>("rotate_pages", { docId, pages, delta });

export const saveAs = (docId: number, dest: string, jobId: string) => invoke<OpResult>("save_as", { docId, dest, jobId });

export const extractPages = (docId: number, selection: string, dest: string, jobId?: string) =>
  invoke<OpResult>("extract_pages", { docId, selection, dest, jobId: jobId ?? crypto.randomUUID() });

export const mergeDocuments = (docId: number, others: string[], dest: string, jobId: string) =>
  invoke<OpResult>("merge_documents", { docId, others, dest, jobId });

export const preflightMerge = (docId: number, others: string[], jobId: string) =>
  invoke<Preflight>("preflight_merge", { docId, others, jobId });

export const convertDocument = (
  docId: number | null,
  format: "png" | "jpeg" | "txt" | "pdf",
  options: { range: string; dpi: number; quality: number; baseName: string },
  outDir: string,
  images: string[],
) => {
  const jobId = crypto.randomUUID();
  return invoke<{ outputDir: string; files: string[]; pages: number }>("convert_document", {
    docId,
    format,
    options,
    outDir,
    images,
    jobId,
  });
};

export const preflightExtract = (docId: number, selection: string, jobId: string) =>
  invoke<Preflight>("preflight_extract", { docId, selection, jobId });



export const formFields = (docId: number, jobId: string) => invoke<FormField[]>("form_fields", { docId, jobId });

export const fillForm = (docId: number, values: Record<string, string | boolean>, jobId: string) =>
  invoke<DocInfo>("fill_form", { docId, values, jobId });

export const addAnnotation = (docId: number, request: AnnotationRequest, jobId: string) =>
  invoke<DocInfo>("add_annotation", { docId, request, jobId });

export const documentOutline = (docId: number) => invoke<OutlineNode[]>("document_outline", { docId });

export const searchDocument = (docId: number, query: string, caseSensitive: boolean, jobId: string) =>
  invoke<SearchHit[]>("search_document", { docId, query, caseSensitive, jobId });

export const textSpans = (docId: number, pageIndex: number) => invoke<TextSpan[]>("text_spans", { docId, pageIndex });

export const reportViewState = (metrics: unknown) => invoke<void>("report_view_state", { metrics });

export const viewState = () => invoke<Record<string, unknown> | null>("view_state");

export const startupFile = () => invoke<string | null>("startup_file");

export const cancelJob = (jobId: string) => invoke<boolean>("cancel_job", { jobId });

/** Backend returns 8-byte header (width, height as u32 LE) followed by RGBA pixels. */
export async function renderPage(docId: number, pageIndex: number, scale: number): Promise<RenderedPage> {
  const raw = await invoke<ArrayBuffer | number[]>("render_page", { docId, pageIndex, scale });
  // The IPC fallback (postMessage) delivers binary responses as a JSON number array.
  const buf = raw instanceof ArrayBuffer ? raw : Uint8Array.from(raw).buffer;
  const view = new DataView(buf);
  const width = view.getUint32(0, true);
  const height = view.getUint32(4, true);
  return { width, height, pixels: new Uint8ClampedArray(buf, 8, width * height * 4) };
}

/** Largest bitmap the backend accepts (must match MAX_RENDER_PIXELS in engine.rs). */
export const MAX_RENDER_PIXELS = 60_000_000;

/** CSS pixels per PDF point at 100 % zoom (96 dpi / 72 pt). */
export const PX_PER_PT = 96 / 72;
