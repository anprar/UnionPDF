import { FormPanel } from "./FormPanel";
import { Thumbnails } from "./Thumbnails";
import type { DocInfo, FormField } from "../types";

interface Props {
  open: boolean;
  doc: DocInfo | null;
  current: number;
  revision: number;
  formOpen: boolean;
  fields: FormField[] | null;
  fieldsLoading: boolean;
  busy: boolean;
  onSelectPage: (index: number) => void;
  onApplyForm: (values: Record<string, string | boolean>) => void;
  onGoToPage: (index: number) => void;
}

export function Sidebar(p: Props) {
  if (!p.open || !p.doc) return null;
  return (
    <aside className="sidebar" aria-label="Panel navigasi">
      <div className="sidebar-section">
        <div className="sidebar-title">Halaman</div>
        <Thumbnails docId={p.doc.doc_id} pages={p.doc.pages} current={p.current} revision={p.revision} onSelect={p.onSelectPage} />
      </div>
      {p.formOpen && (
        <div className="sidebar-section form">
          <FormPanel fields={p.fields} loading={p.fieldsLoading} busy={p.busy} onApply={p.onApplyForm} onGoToPage={p.onGoToPage} />
        </div>
      )}
    </aside>
  );
}
