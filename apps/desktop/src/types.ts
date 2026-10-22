export interface PageInfo {
  index: number;
  /** Displayed size in PDF points (after /Rotate). */
  width: number;
  height: number;
  rotation: number;
}

export interface DocInfo {
  doc_id: number;
  path: string;
  file_name: string;
  page_count: number;
  pages: PageInfo[];
  dirty: boolean;
  /** Increases on every in-memory change; used to invalidate rendered pages. */
  revision: number;
  has_form: boolean;
  outline_count: number;
}

export interface OpResult {
  output_path: string;
  page_count: number;
  verified: boolean;
  engine: string;
  checks: string[];
  changes: string[];
  limitations: string[];
}

export interface Preflight {
  engine: string;
  changes: string[];
  limitations: string[];
  requires_confirmation: boolean;
}

export interface EngineStatus {
  available: boolean;
  engine: string | null;
  library_path: string | null;
  error: string | null;
  authoring_available: boolean;
  authoring_java: string | null;
  authoring_error: string | null;
}

export type FieldType = "text" | "checkbox" | "radio" | "combo" | "list" | "signature" | "other";

export interface FormField {
  name: string;
  type: FieldType;
  value: string;
  read_only: boolean;
  pages: number[];
  on_value?: string;
  options?: string[];
  option_labels?: string[];
}

export type AnnotationKind = "highlight" | "underline" | "strikeout" | "note" | "freetext";

export interface AnnotationRequest {
  page: number;
  kind: AnnotationKind;
  /** Displayed-page rectangle in points, origin top-left. */
  rect: [number, number, number, number];
  contents?: string | null;
}

export interface ApiError {
  code: string;
  message: string;
}

/** A text run in displayed page space (origin top-left, points). */
export interface TextSpan {
  text: string;
  left: number;
  top: number;
  width: number;
  height: number;
}

/** A bookmark entry (outline node) of the document. */
export interface OutlineNode {
  title: string;
  page: number | null;
  children: OutlineNode[];
}

/** A search match in displayed page space (origin top-left, points). */
export interface SearchHit {
  page: number;
  text: string;
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface RenderedPage {
  width: number;
  height: number;
  pixels: Uint8ClampedArray<ArrayBuffer>;
}
