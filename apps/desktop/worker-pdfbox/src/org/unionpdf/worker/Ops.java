package org.unionpdf.worker;

import java.io.File;
import java.io.IOException;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.apache.pdfbox.Loader;
import org.apache.pdfbox.cos.COSBase;
import org.apache.pdfbox.cos.COSDictionary;
import org.apache.pdfbox.cos.COSName;
import org.apache.pdfbox.multipdf.PDFMergerUtility;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.encryption.InvalidPasswordException;
import org.apache.pdfbox.pdmodel.graphics.color.PDColor;
import org.apache.pdfbox.pdmodel.graphics.image.PDImageXObject;
import org.apache.pdfbox.pdmodel.graphics.color.PDDeviceRGB;
import org.apache.pdfbox.pdmodel.interactive.action.PDAction;
import org.apache.pdfbox.pdmodel.interactive.action.PDActionGoTo;
import org.apache.pdfbox.pdmodel.interactive.action.PDActionURI;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotation;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationFreeText;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationHighlight;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationLink;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationStrikeout;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationText;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationTextMarkup;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationUnderline;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotationWidget;
import org.apache.pdfbox.pdmodel.interactive.documentnavigation.destination.PDDestination;
import org.apache.pdfbox.pdmodel.interactive.documentnavigation.destination.PDNamedDestination;
import org.apache.pdfbox.pdmodel.interactive.documentnavigation.destination.PDPageDestination;
import org.apache.pdfbox.pdmodel.interactive.documentnavigation.outline.PDDocumentOutline;
import org.apache.pdfbox.pdmodel.interactive.documentnavigation.outline.PDOutlineItem;
import org.apache.pdfbox.pdmodel.interactive.documentnavigation.outline.PDOutlineNode;
import org.apache.pdfbox.pdmodel.interactive.form.PDAcroForm;
import org.apache.pdfbox.pdmodel.interactive.form.PDCheckBox;
import org.apache.pdfbox.pdmodel.interactive.form.PDChoice;
import org.apache.pdfbox.pdmodel.interactive.form.PDComboBox;
import org.apache.pdfbox.pdmodel.interactive.form.PDField;
import org.apache.pdfbox.pdmodel.interactive.form.PDListBox;
import org.apache.pdfbox.pdmodel.interactive.form.PDNonTerminalField;
import org.apache.pdfbox.pdmodel.interactive.form.PDRadioButton;
import org.apache.pdfbox.pdmodel.interactive.form.PDSignatureField;
import org.apache.pdfbox.pdmodel.interactive.form.PDTerminalField;
import org.apache.pdfbox.pdmodel.interactive.form.PDTextField;

/** Document operations. Each request opens its own documents; nothing is shared between requests. */
final class Ops {
    interface Progress {
        void stage(String text);
    }

    private Ops() {}

    static Object run(String op, Map<String, Object> p, Progress progress) throws Exception {
        if ("ping".equals(op)) return map("pdfbox", org.apache.pdfbox.util.Version.getVersion());
        if ("inspect".equals(op)) return inspect(p);
        if ("extract".equals(op)) return extract(p, progress);
        if ("merge".equals(op)) return merge(p, progress);
        if ("fill_form".equals(op)) return fillForm(p, progress);
        if ("add_annotations".equals(op)) return addAnnotations(p, progress);
        if ("images_to_pdf".equals(op)) return imagesToPdf(p, progress);
        throw new WorkerException("unknown_op", "operasi tidak dikenal: " + op);
    }

    // ------------------------------------------------------------------ helpers

    static Map<String, Object> map(Object... kv) {
        Map<String, Object> m = new LinkedHashMap<String, Object>();
        for (int k = 0; k < kv.length; k += 2) m.put((String) kv[k], kv[k + 1]);
        return m;
    }

    static String str(Map<String, Object> p, String key) throws WorkerException {
        Object v = p.get(key);
        if (!(v instanceof String) || ((String) v).isEmpty()) throw new WorkerException("bad_request", "parameter '" + key + "' wajib");
        return (String) v;
    }

    static boolean bool(Map<String, Object> p, String key) {
        return Boolean.TRUE.equals(p.get(key));
    }

    @SuppressWarnings("unchecked")
    static List<Object> list(Map<String, Object> p, String key) throws WorkerException {
        Object v = p.get(key);
        if (!(v instanceof List)) throw new WorkerException("bad_request", "parameter '" + key + "' harus array");
        return (List<Object>) v;
    }

    static float[] floats(Object v, int n, String what) throws WorkerException {
        if (!(v instanceof List) || ((List<?>) v).size() != n) throw new WorkerException("bad_request", what + " harus " + n + " angka");
        float[] f = new float[n];
        for (int k = 0; k < n; k++) f[k] = ((Number) ((List<?>) v).get(k)).floatValue();
        return f;
    }

    static PDDocument load(String path) throws IOException, WorkerException {
        File f = new File(path);
        if (!f.isFile()) throw new WorkerException("file_not_found", "berkas tidak ditemukan: " + f.getName());
        try {
            return Loader.loadPDF(f);
        } catch (InvalidPasswordException e) {
            throw new WorkerException("password_required", "dokumen dilindungi kata sandi");
        }
    }

    static void save(PDDocument doc, String output, Progress progress) throws IOException {
        progress.stage("Menulis berkas");
        doc.save(new File(output));
    }

    static Integer destPage(PDDocument doc, PDDestination d) throws IOException {
        if (d instanceof PDNamedDestination) d = doc.getDocumentCatalog().findNamedDestinationPage((PDNamedDestination) d);
        if (d instanceof PDPageDestination) {
            PDPageDestination pd = (PDPageDestination) d;
            PDPage page = pd.getPage();
            if (page != null) {
                int idx = doc.getPages().indexOf(page);
                return idx >= 0 ? idx : null;
            }
            int n = pd.getPageNumber();
            return n >= 0 ? n : null;
        }
        return null;
    }

    static PDDestination actionDest(PDAction a) throws IOException {
        return a instanceof PDActionGoTo ? ((PDActionGoTo) a).getDestination() : null;
    }

    static Integer itemPage(PDDocument doc, PDOutlineItem it) throws IOException {
        PDDestination d = it.getDestination();
        if (d == null) d = actionDest(it.getAction());
        return d == null ? null : destPage(doc, d);
    }

    static Integer linkPage(PDDocument doc, PDAnnotationLink l) throws IOException {
        PDDestination d = l.getDestination();
        if (d == null) d = actionDest(l.getAction());
        return d == null ? null : destPage(doc, d);
    }

    /** Widget dictionary -> page index, by scanning page /Annots (widget /P is optional). */
    static Map<COSDictionary, Integer> widgetPages(PDDocument doc) throws IOException {
        Map<COSDictionary, Integer> m = new IdentityHashMap<COSDictionary, Integer>();
        int i = 0;
        for (PDPage page : doc.getPages()) {
            for (PDAnnotation a : page.getAnnotations()) m.put(a.getCOSObject(), i);
            i++;
        }
        return m;
    }

    static String fieldType(PDField f) {
        if (f instanceof PDTextField) return "text";
        if (f instanceof PDCheckBox) return "checkbox";
        if (f instanceof PDRadioButton) return "radio";
        if (f instanceof PDComboBox) return "combo";
        if (f instanceof PDListBox) return "list";
        if (f instanceof PDSignatureField) return "signature";
        return "other";
    }

    static List<Object> outlineList(PDDocument doc) throws IOException {
        List<Object> out = new ArrayList<Object>();
        PDDocumentOutline o = doc.getDocumentCatalog().getDocumentOutline();
        if (o != null) walkOutline(doc, o, 0, out);
        return out;
    }

    static void walkOutline(PDDocument doc, PDOutlineNode node, int level, List<Object> out) throws IOException {
        for (PDOutlineItem it : node.children()) {
            out.add(map("title", it.getTitle(), "level", level, "page", itemPage(doc, it)));
            walkOutline(doc, it, level + 1, out);
        }
    }

    static List<Object> fieldList(PDDocument doc) throws IOException {
        List<Object> out = new ArrayList<Object>();
        PDAcroForm form = doc.getDocumentCatalog().getAcroForm();
        if (form == null) return out;
        Map<COSDictionary, Integer> wp = widgetPages(doc);
        for (PDField f : form.getFieldTree()) {
            if (!(f instanceof PDTerminalField)) continue;
            List<Object> pages = new ArrayList<Object>();
            for (PDAnnotationWidget w : ((PDTerminalField) f).getWidgets()) {
                Integer pg = wp.get(w.getCOSObject());
                if (pg != null && !pages.contains(pg)) pages.add(pg);
            }
            Map<String, Object> e = map("name", f.getFullyQualifiedName(), "type", fieldType(f),
                    "value", f.getValueAsString(), "read_only", f.isReadOnly(), "pages", pages);
            if (f instanceof PDCheckBox) e.put("on_value", ((PDCheckBox) f).getOnValue());
            if (f instanceof PDRadioButton) e.put("options", new ArrayList<Object>(((PDRadioButton) f).getOnValues()));
            if (f instanceof PDChoice) {
                e.put("value", String.join(", ", ((PDChoice) f).getValue()));
                e.put("options", new ArrayList<Object>(((PDChoice) f).getOptionsExportValues()));
                e.put("option_labels", new ArrayList<Object>(((PDChoice) f).getOptionsDisplayValues()));
            }
            out.add(e);
        }
        return out;
    }

    // ------------------------------------------------------------------ inspect

    static Object inspect(Map<String, Object> p) throws Exception {
        PDDocument doc = load(str(p, "input"));
        try {
            List<Object> links = new ArrayList<Object>();
            List<Object> annotations = new ArrayList<Object>();
            int i = 0;
            for (PDPage page : doc.getPages()) {
                for (PDAnnotation a : page.getAnnotations()) {
                    if (a instanceof PDAnnotationLink) {
                        PDAnnotationLink l = (PDAnnotationLink) a;
                        String kind = l.getAction() instanceof PDActionURI ? "uri" : (linkPage(doc, l) != null ? "goto" : "other");
                        links.add(map("page", i, "kind", kind, "dest_page", linkPage(doc, l)));
                    } else {
                        PDRectangle r = a.getRectangle();
                        Map<String, Object> e = map("page", i, "type", a.getSubtype());
                        if (r != null) {
                            e.put("bbox", new float[] {r.getLowerLeftX(), r.getLowerLeftY(), r.getUpperRightX(), r.getUpperRightY()});
                        }
                        e.put("contents", a.getContents());
                        annotations.add(e);
                    }
                }
                i++;
            }
            return map("page_count", doc.getNumberOfPages(), "outline", outlineList(doc), "links", links,
                    "annotations", annotations, "fields", fieldList(doc), "tagged", doc.getDocumentCatalog().getStructureTreeRoot() != null);
        } finally {
            doc.close();
        }
    }

    // ------------------------------------------------------------------ extract

    static COSDictionary dictOf(COSDictionary d, COSName key) {
        COSBase b = d.getDictionaryObject(key);
        return b instanceof COSDictionary ? (COSDictionary) b : null;
    }

    /** Removes an outline item from its parent's sibling chain (PDFBox 3.0.8 has no delete()). */
    static void unlinkOutlineItem(COSDictionary item) {
        COSDictionary parent = dictOf(item, COSName.PARENT);
        COSDictionary prev = dictOf(item, COSName.PREV);
        COSDictionary next = dictOf(item, COSName.NEXT);
        if (prev != null) {
            if (next != null) prev.setItem(COSName.NEXT, next); else prev.removeItem(COSName.NEXT);
        } else if (parent != null) {
            if (next != null) parent.setItem(COSName.FIRST, next); else parent.removeItem(COSName.FIRST);
        }
        if (next != null) {
            if (prev != null) next.setItem(COSName.PREV, prev); else next.removeItem(COSName.PREV);
        } else if (parent != null) {
            if (prev != null) parent.setItem(COSName.LAST, prev); else parent.removeItem(COSName.LAST);
        }
    }

    /** Recomputes /Count. Returns the number of entries visible below `node` if it is open. */
    static int recount(PDOutlineNode node, boolean isRoot) {
        int visible = 0;
        for (PDOutlineItem it : node.children()) {
            boolean open = it.getCOSObject().getInt(COSName.COUNT, 0) > 0;
            int below = recount(it, false);
            visible += 1 + (open ? below : 0);
        }
        COSDictionary d = node.getCOSObject();
        if (visible == 0) {
            d.removeItem(COSName.COUNT);
        } else if (isRoot || d.getInt(COSName.COUNT, 0) > 0) {
            d.setInt(COSName.COUNT, visible);
        } else {
            d.setInt(COSName.COUNT, -visible);
        }
        return visible;
    }

    static void pruneOutline(PDDocument doc, PDOutlineNode node, Set<Integer> removed,
                             List<Object> removedTitles, List<Object> detachedTitles) throws IOException {
        List<PDOutlineItem> kids = new ArrayList<PDOutlineItem>();
        for (PDOutlineItem it : node.children()) kids.add(it);
        for (PDOutlineItem it : kids) {
            pruneOutline(doc, it, removed, removedTitles, detachedTitles);
            Integer pg = itemPage(doc, it);
            if (pg == null || !removed.contains(pg)) continue;
            if (it.hasChildren()) {
                it.getCOSObject().removeItem(COSName.DEST);
                it.getCOSObject().removeItem(COSName.A);
                detachedTitles.add(it.getTitle());
            } else {
                unlinkOutlineItem(it.getCOSObject());
                removedTitles.add(it.getTitle());
            }
        }
    }

    static Object extract(Map<String, Object> p, Progress progress) throws Exception {
        String output = bool(p, "dry_run") ? null : str(p, "output");
        progress.stage("Memuat dokumen");
        PDDocument doc = load(str(p, "input"));
        try {
            int n = doc.getNumberOfPages();
            Set<Integer> keep = new HashSet<Integer>();
            for (Object o : list(p, "pages")) {
                int k = ((Number) o).intValue();
                if (k < 0 || k >= n) throw new WorkerException("bad_request", "halaman " + (k + 1) + " di luar rentang");
                keep.add(k);
            }
            if (keep.isEmpty()) throw new WorkerException("bad_request", "tidak ada halaman yang dipilih");
            Set<Integer> removed = new HashSet<Integer>();
            for (int k = 0; k < n; k++) if (!keep.contains(k)) removed.add(k);

            progress.stage("Memangkas bookmark dan link");
            List<Object> bmRemoved = new ArrayList<Object>(), bmDetached = new ArrayList<Object>();
            PDDocumentOutline outline = doc.getDocumentCatalog().getDocumentOutline();
            if (outline != null) {
                pruneOutline(doc, outline, removed, bmRemoved, bmDetached);
                recount(outline, true);
            }
            int linksRemoved = 0;
            for (int k : keep) {
                PDPage page = doc.getPage(k);
                List<PDAnnotation> annots = page.getAnnotations();
                List<PDAnnotation> kept = new ArrayList<PDAnnotation>();
                for (PDAnnotation a : annots) {
                    if (a instanceof PDAnnotationLink) {
                        Integer pg = linkPage(doc, (PDAnnotationLink) a);
                        if (pg != null && removed.contains(pg)) { linksRemoved++; continue; }
                    }
                    kept.add(a);
                }
                if (kept.size() != annots.size()) page.setAnnotations(kept);
            }

            progress.stage("Memangkas field form");
            List<Object> fieldsRemoved = new ArrayList<Object>();
            int widgetsRemoved = 0;
            PDAcroForm form = doc.getDocumentCatalog().getAcroForm();
            if (form != null) {
                Map<COSDictionary, Integer> wp = widgetPages(doc);
                List<PDField> drop = new ArrayList<PDField>();
                for (PDField f : form.getFieldTree()) {
                    if (!(f instanceof PDTerminalField)) continue;
                    List<PDAnnotationWidget> ws = ((PDTerminalField) f).getWidgets();
                    List<PDAnnotationWidget> keepW = new ArrayList<PDAnnotationWidget>();
                    for (PDAnnotationWidget w : ws) {
                        Integer pg = wp.get(w.getCOSObject());
                        if (pg == null || !removed.contains(pg)) keepW.add(w);
                    }
                    if (keepW.isEmpty() && !ws.isEmpty()) drop.add(f);
                    else if (keepW.size() != ws.size()) {
                        widgetsRemoved += ws.size() - keepW.size();
                        ((PDTerminalField) f).setWidgets(keepW);
                    }
                }
                for (PDField f : drop) {
                    fieldsRemoved.add(f.getFullyQualifiedName());
                    removeField(form, f);
                }
            }

            progress.stage("Menghapus halaman");
            for (int k = n - 1; k >= 0; k--) if (removed.contains(k)) doc.removePage(k);
            List<Object> warnings = new ArrayList<Object>();
            if (doc.getDocumentCatalog().getStructureTreeRoot() != null)
                warnings.add("Struktur tag (aksesibilitas) tidak dipangkas dan dapat merujuk halaman yang dihapus.");
            if (output != null) save(doc, output, progress);
            return map("page_count", doc.getNumberOfPages(), "bookmarks_removed", bmRemoved,
                    "bookmarks_detached", bmDetached, "links_removed", linksRemoved,
                    "fields_removed", fieldsRemoved, "widgets_removed", widgetsRemoved,
                    "bookmarks_after", outlineList(doc).size(), "warnings", warnings);
        } finally {
            doc.close();
        }
    }

    static void removeField(PDAcroForm form, PDField f) {
        PDNonTerminalField parent = f.getParent();
        List<PDField> siblings = parent == null ? form.getFields() : parent.getChildren();
        List<PDField> keep = new ArrayList<PDField>();
        for (PDField s : siblings) if (s.getCOSObject() != f.getCOSObject()) keep.add(s);
        if (parent == null) form.setFields(keep); else parent.setChildren(keep);
    }

    // ------------------------------------------------------------------ merge

    static Object merge(Map<String, Object> p, Progress progress) throws Exception {
        String output = bool(p, "dry_run") ? null : str(p, "output");
        List<Object> inputs = list(p, "inputs");
        if (inputs.size() < 2) throw new WorkerException("bad_request", "minimal dua dokumen");
        progress.stage("Memuat dokumen");
        List<PDDocument> open = new ArrayList<PDDocument>();
        try {
            PDDocument dest = load((String) inputs.get(0));
            open.add(dest);
            int bookmarksIn = outlineList(dest).size();
            int fieldsIn = fieldList(dest).size();
            Map<String, Object> renamed = new LinkedHashMap<String, Object>();
            for (int k = 1; k < inputs.size(); k++) {
                PDDocument src = load((String) inputs.get(k));
                open.add(src);
                bookmarksIn += outlineList(src).size();
                fieldsIn += fieldList(src).size();
                Set<String> taken = rootFieldNames(dest);
                PDAcroForm sf = src.getDocumentCatalog().getAcroForm();
                if (sf != null) {
                    for (PDField f : sf.getFields()) {
                        String name = f.getPartialName();
                        if (name == null || !taken.contains(name)) continue;
                        int suffix = k + 1;
                        String candidate = name + "_" + suffix;
                        while (taken.contains(candidate) || hasRoot(sf, candidate)) candidate = name + "_" + (++suffix);
                        f.setPartialName(candidate);
                        renamed.put(name, candidate);
                    }
                }
                progress.stage("Menggabungkan dokumen " + (k + 1));
                new PDFMergerUtility().appendDocument(dest, src);
            }
            int bookmarksAfter = outlineList(dest).size();
            int fieldsAfter = fieldList(dest).size();
            List<Object> warnings = new ArrayList<Object>();
            if (bookmarksAfter != bookmarksIn)
                warnings.add("Jumlah bookmark berubah: " + bookmarksIn + " -> " + bookmarksAfter);
            if (fieldsAfter != fieldsIn)
                warnings.add("Jumlah field form berubah: " + fieldsIn + " -> " + fieldsAfter);
            if (output != null) save(dest, output, progress);
            return map("page_count", dest.getNumberOfPages(), "bookmarks_before", bookmarksIn,
                    "bookmarks_after", bookmarksAfter, "fields_before", fieldsIn, "fields_after", fieldsAfter,
                    "fields_renamed", renamed, "warnings", warnings);
        } finally {
            for (PDDocument d : open) d.close();
        }
    }

    static Set<String> rootFieldNames(PDDocument doc) {
        Set<String> s = new HashSet<String>();
        PDAcroForm f = doc.getDocumentCatalog().getAcroForm();
        if (f != null) for (PDField x : f.getFields()) if (x.getPartialName() != null) s.add(x.getPartialName());
        return s;
    }

    static boolean hasRoot(PDAcroForm form, String name) {
        for (PDField x : form.getFields()) if (name.equals(x.getPartialName())) return true;
        return false;
    }

    // ------------------------------------------------------------------ form fill

    @SuppressWarnings("unchecked")
    static Object fillForm(Map<String, Object> p, Progress progress) throws Exception {
        String output = str(p, "output");
        Object v = p.get("values");
        if (!(v instanceof Map)) throw new WorkerException("bad_request", "parameter 'values' harus objek");
        Map<String, Object> values = (Map<String, Object>) v;
        progress.stage("Memuat dokumen");
        PDDocument doc = load(str(p, "input"));
        try {
            PDAcroForm form = doc.getDocumentCatalog().getAcroForm();
            if (form == null) throw new WorkerException("no_form", "dokumen tidak memiliki form");
            List<Object> applied = new ArrayList<Object>();
            List<Object> errors = new ArrayList<Object>();
            progress.stage("Mengisi field");
            for (Map.Entry<String, Object> e : values.entrySet()) {
                PDField f = form.getField(e.getKey());
                try {
                    if (f == null) throw new WorkerException("field_not_found", "field tidak ditemukan");
                    if (f.isReadOnly()) throw new WorkerException("read_only", "field hanya-baca");
                    Object val = e.getValue();
                    if (f instanceof PDTextField) {
                        ((PDTextField) f).setValue(val == null ? "" : val.toString());
                    } else if (f instanceof PDCheckBox) {
                        if (Boolean.TRUE.equals(val)) ((PDCheckBox) f).check(); else ((PDCheckBox) f).unCheck();
                    } else if (f instanceof PDRadioButton) {
                        PDRadioButton r = (PDRadioButton) f;
                        if (val == null || "Off".equals(val)) {
                            r.getCOSObject().setItem(COSName.V, COSName.Off);
                            for (PDAnnotationWidget w : r.getWidgets()) w.setAppearanceState("Off");
                        } else {
                            if (!r.getOnValues().contains(val.toString()))
                                throw new WorkerException("bad_value", "pilihan '" + val + "' tidak tersedia");
                            r.setValue(val.toString());
                        }
                    } else if (f instanceof PDComboBox || f instanceof PDListBox) {
                        ((PDChoice) f).setValue(val == null ? "" : val.toString());
                    } else {
                        throw new WorkerException("unsupported", "jenis field belum didukung: " + fieldType(f));
                    }
                    applied.add(e.getKey());
                } catch (WorkerException we) {
                    errors.add(map("name", e.getKey(), "code", we.code, "message", we.getMessage()));
                } catch (Exception ex) {
                    errors.add(map("name", e.getKey(), "code", "fill_failed", "message", ex.getClass().getSimpleName() + ": " + ex.getMessage()));
                }
            }
            if (!errors.isEmpty()) throw new WorkerException("fill_failed", "sebagian field gagal diisi; tidak ada yang disimpan", map("errors", errors));
            save(doc, output, progress);
            return map("applied", applied, "fields", fieldList(doc));
        } finally {
            doc.close();
        }
    }

    // ------------------------------------------------------------------ annotations

    static PDColor rgb(float[] c) {
        return new PDColor(c, PDDeviceRGB.INSTANCE);
    }

    @SuppressWarnings("unchecked")
    /** Builds a PDF from image files (one page per image, page size = image size). */
    static Object imagesToPdf(Map<String, Object> p, Progress progress) throws Exception {
        List<Object> inputs = list(p, "inputs");
        if (inputs.isEmpty()) throw new WorkerException("bad_request", "tidak ada berkas gambar");
        String output = str(p, "output");
        progress.stage("Menyusun PDF");
        PDDocument doc = new PDDocument();
        try {
            int index = 0;
            for (Object o : inputs) {
                File f = new File((String) o);
                if (!f.isFile()) throw new WorkerException("file_not_found", "gambar tidak ditemukan: " + f.getName());
                BufferedImage img = ImageIO.read(f);
                if (img == null) throw new WorkerException("bad_image", "gambar tidak dapat dibaca: " + f.getName());
                float w = img.getWidth();
                float h = img.getHeight();
                PDPage page = new PDPage(new PDRectangle(w, h));
                doc.addPage(page);
                java.io.ByteArrayOutputStream png = new java.io.ByteArrayOutputStream();
                javax.imageio.ImageIO.write(img, "png", png);
                PDImageXObject xo = PDImageXObject.createFromByteArray(doc, png.toByteArray(), "png");
                try (PDPageContentStream cs = new PDPageContentStream(doc, page)) {
                    cs.drawImage(xo, 0, 0, w, h);
                }
                index++;
            }
            doc.save(new File(output));
            return map("page_count", index, "output", output);
        } finally {
            doc.close();
        }
    }

    static Object addAnnotations(Map<String, Object> p, Progress progress) throws Exception {
        String output = str(p, "output");
        List<Object> items = list(p, "annotations");
        if (items.isEmpty()) throw new WorkerException("bad_request", "tidak ada anotasi");
        progress.stage("Memuat dokumen");
        PDDocument doc = load(str(p, "input"));
        try {
            progress.stage("Membuat anotasi");
            List<Object> added = new ArrayList<Object>();
            for (Object o : items) {
                Map<String, Object> a = (Map<String, Object>) o;
                String type = str(a, "type");
                int pageIndex = ((Number) a.get("page")).intValue();
                if (pageIndex < 0 || pageIndex >= doc.getNumberOfPages())
                    throw new WorkerException("bad_request", "halaman di luar rentang");
                PDPage page = doc.getPage(pageIndex);
                float[] color = a.get("color") == null ? null : floats(a.get("color"), 3, "color");
                String contents = a.get("contents") instanceof String ? (String) a.get("contents") : null;
                PDAnnotation annot;
                if ("highlight".equals(type) || "underline".equals(type) || "strikeout".equals(type)) {
                    List<Object> quads = list(a, "quads");
                    if (quads.isEmpty()) throw new WorkerException("bad_request", "quads kosong");
                    float[] qp = new float[quads.size() * 8];
                    float l = Float.MAX_VALUE, b = Float.MAX_VALUE, r = -Float.MAX_VALUE, t = -Float.MAX_VALUE;
                    for (int k = 0; k < quads.size(); k++) {
                        float[] q = floats(quads.get(k), 4, "quad");
                        float[] pts = {q[0], q[3], q[2], q[3], q[0], q[1], q[2], q[1]};
                        System.arraycopy(pts, 0, qp, k * 8, 8);
                        l = Math.min(l, q[0]); b = Math.min(b, q[1]); r = Math.max(r, q[2]); t = Math.max(t, q[3]);
                    }
                    PDAnnotationTextMarkup m = "highlight".equals(type) ? new PDAnnotationHighlight()
                            : "underline".equals(type) ? new PDAnnotationUnderline() : new PDAnnotationStrikeout();
                    m.setRectangle(new PDRectangle(l, b, r - l, t - b));
                    m.setQuadPoints(qp);
                    m.setColor(rgb(color != null ? color : new float[] {1f, 0.85f, 0f}));
                    if (contents != null) m.setContents(contents);
                    m.setPrinted(true);
                    m.constructAppearances(doc);
                    annot = m;
                } else if ("note".equals(type)) {
                    float[] r = floats(a.get("rect"), 4, "rect");
                    PDAnnotationText t = new PDAnnotationText();
                    t.setRectangle(new PDRectangle(r[0], r[1], r[2] - r[0], r[3] - r[1]));
                    t.setColor(rgb(color != null ? color : new float[] {1f, 0.8f, 0f}));
                    t.setContents(contents == null ? "" : contents);
                    t.setPrinted(true);
                    t.constructAppearances(doc);
                    annot = t;
                } else if ("freetext".equals(type)) {
                    float[] r = floats(a.get("rect"), 4, "rect");
                    if (contents == null || contents.isEmpty()) throw new WorkerException("bad_request", "teks kosong");
                    float size = a.get("font_size") instanceof Number ? ((Number) a.get("font_size")).floatValue() : 12f;
                    PDAnnotationFreeText f = new PDAnnotationFreeText();
                    f.setRectangle(new PDRectangle(r[0], r[1], r[2] - r[0], r[3] - r[1]));
                    f.setDefaultAppearance("/Helv " + size + " Tf 0 g");
                    f.setColor(rgb(color != null ? color : new float[] {0f, 0f, 0f}));
                    f.setContents(contents);
                    f.setPrinted(true);
                    try {
                        f.constructAppearances(doc);
                    } catch (IllegalArgumentException e) {
                        throw new WorkerException("unsupported_text", "teks memuat karakter yang belum didukung font standar: " + e.getMessage());
                    }
                    annot = f;
                } else {
                    throw new WorkerException("unsupported", "jenis anotasi belum didukung: " + type);
                }
                annot.setModifiedDate(Calendar.getInstance());
                if (annot.getAppearance() == null || annot.getAppearance().getNormalAppearance() == null)
                    throw new WorkerException("no_appearance", "appearance tidak terbentuk untuk " + type);
                page.getAnnotations().add(annot);
                added.add(map("type", type, "page", pageIndex));
            }
            save(doc, output, progress);
            return map("added", added);
        } finally {
            doc.close();
        }
    }
}
