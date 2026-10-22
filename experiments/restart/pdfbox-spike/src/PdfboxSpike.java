// UnionPDF controlled-restart spike for Apache PDFBox 3.0.8 (Java 8). NOT production code.
//
// Usage (from experiments/restart):
//   java -cp "pdfbox-spike/build;deps/pdfbox/jars/*" PdfboxSpike all
// Output: raw/compare/pdfbox/*.pdf + raw/compare/pdfbox/result.json

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.Security;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Collection;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.apache.pdfbox.Loader;
import org.apache.pdfbox.cos.COSName;
import org.apache.pdfbox.multipdf.PDFMergerUtility;
import org.apache.pdfbox.multipdf.PageExtractor;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.PDResources;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.apache.pdfbox.pdmodel.graphics.color.PDColor;
import org.apache.pdfbox.pdmodel.graphics.color.PDDeviceRGB;
import org.apache.pdfbox.pdmodel.interactive.annotation.*;
import org.apache.pdfbox.pdmodel.interactive.digitalsignature.PDSignature;
import org.apache.pdfbox.pdmodel.interactive.digitalsignature.SignatureInterface;
import org.apache.pdfbox.pdmodel.interactive.form.*;
import org.bouncycastle.asn1.x500.X500Name;
import org.bouncycastle.cert.X509CertificateHolder;
import org.bouncycastle.cert.jcajce.JcaCertStore;
import org.bouncycastle.cert.jcajce.JcaX509CertificateConverter;
import org.bouncycastle.cert.jcajce.JcaX509v3CertificateBuilder;
import org.bouncycastle.cms.CMSProcessableByteArray;
import org.bouncycastle.cms.CMSSignedData;
import org.bouncycastle.cms.CMSSignedDataGenerator;
import org.bouncycastle.cms.SignerInformation;
import org.bouncycastle.cms.jcajce.JcaSignerInfoGeneratorBuilder;
import org.bouncycastle.cms.jcajce.JcaSimpleSignerInfoVerifierBuilder;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.operator.ContentSigner;
import org.bouncycastle.operator.jcajce.JcaContentSignerBuilder;
import org.bouncycastle.operator.jcajce.JcaDigestCalculatorProviderBuilder;
import org.bouncycastle.util.Store;

public class PdfboxSpike {
    static final File ROOT = new File(".").getAbsoluteFile();
    static final File GEN = new File(ROOT, "fixtures/generated");
    static final File OUT = new File(ROOT, "raw/compare/pdfbox");
    static final StringBuilder LOG = new StringBuilder();

    // ---------- tiny JSON helpers (no extra dependency) ----------
    static String q(Object o) {
        if (o == null) return "null";
        if (o instanceof Number || o instanceof Boolean) return o.toString();
        String s = o.toString().replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "");
        return "\"" + s + "\"";
    }

    static String obj(Map<String, Object> m) {
        StringBuilder b = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, Object> e : m.entrySet()) {
            if (!first) b.append(',');
            first = false;
            b.append(q(e.getKey())).append(':');
            Object v = e.getValue();
            if (v instanceof RawJson) b.append(((RawJson) v).s);
            else b.append(q(v));
        }
        return b.append('}').toString();
    }

    static final class RawJson {
        final String s;
        RawJson(String s) { this.s = s; }
    }

    static RawJson arr(List<String> items) {
        return new RawJson("[" + String.join(",", items) + "]");
    }

    static Map<String, Object> m() { return new LinkedHashMap<String, Object>(); }

    static PDColor rgb(float r, float g, float b) {
        return new PDColor(new float[] {r, g, b}, PDDeviceRGB.INSTANCE);
    }

    static PDRectangle rect(float l, float b, float r, float t) {
        return new PDRectangle(l, b, r - l, t - b);
    }

    // ---------- RS-02 annotations ----------
    static String rs02() throws IOException {
        List<String> created = new ArrayList<String>();
        List<String> errors = new ArrayList<String>();
        File in = new File(GEN, "rs02_annot_base.pdf");
        // targets measured by the fixture generator (PDF user space l,b,r,t)
        Map<String, float[]> targets = readTargets();
        try (PDDocument doc = Loader.loadPDF(in)) {
            PDPage p1 = doc.getPage(1);
            String[] kinds = {"highlight", "underline", "strikeout", "squiggly"};
            float[][] colors = {{1f, .9f, 0f}, {0f, .47f, 1f}, {.86f, 0f, 0f}, {0f, .63f, .24f}};
            for (int i = 0; i < kinds.length; i++) {
                float[] r = targets.get(kinds[i]);
                try {
                    PDAnnotationTextMarkup a;
                    if (i == 0) a = new PDAnnotationHighlight();
                    else if (i == 1) a = new PDAnnotationUnderline();
                    else if (i == 2) a = new PDAnnotationStrikeout();
                    else a = new PDAnnotationSquiggly();
                    a.setRectangle(rect(r[0], r[1], r[2], r[3]));
                    a.setQuadPoints(new float[] {r[0], r[3], r[2], r[3], r[0], r[1], r[2], r[1]});
                    a.setColor(rgb(colors[i][0], colors[i][1], colors[i][2]));
                    a.setContents("RS02-" + kinds[i]);
                    a.setPrinted(true);
                    a.constructAppearances(doc);
                    p1.getAnnotations().add(a);
                    created.add(createdJson(1, kinds[i], r, "PDFBox constructAppearances"));
                } catch (Exception e) {
                    errors.add(errJson(1, kinds[i], e));
                }
            }
            PDPage p0 = doc.getPage(0);
            Object[][] items = {
                {"text", new float[] {60, 700, 84, 724}},
                {"freetext", new float[] {120, 690, 320, 730}},
                {"square", new float[] {60, 560, 200, 660}},
                {"circle", new float[] {240, 560, 360, 660}},
                {"stamp", new float[] {380, 560, 540, 640}},
                {"ink", new float[] {60, 420, 300, 520}},
                {"line", new float[] {320, 420, 540, 470}},
                {"polygon", new float[] {60, 300, 200, 400}},
                {"polyline", new float[] {240, 300, 380, 400}},
                {"caret", new float[] {420, 330, 440, 350}},
            };
            for (Object[] it : items) {
                String kind = (String) it[0];
                float[] r = (float[]) it[1];
                try {
                    PDAnnotation a = makeAnnot(kind, r);
                    a.setContents("RS02-" + kind);
                    a.setPrinted(true);
                    String via = "PDFBox constructAppearances";
                    if (a instanceof PDAnnotationMarkup && !(a instanceof PDAnnotationRubberStamp)) {
                        ((PDAnnotationMarkup) a).constructAppearances(doc);
                    } else if (a instanceof PDAnnotationRubberStamp) {
                        via = "PDFBox (stamp: tanpa appearance handler; AP tidak dibuat)";
                    }
                    p0.getAnnotations().add(a);
                    created.add(createdJson(0, kind, r, via));
                } catch (Exception e) {
                    errors.add(errJson(0, kind, e));
                }
            }
            doc.save(new File(OUT, "rs02_annotated.pdf"));
        }
        Map<String, Object> res = m();
        res.put("output", "rs02_annotated.pdf");
        res.put("created", arr(created));
        res.put("errors", arr(errors));
        return obj(res);
    }

    static PDAnnotation makeAnnot(String kind, float[] r) {
        PDRectangle rr = rect(r[0], r[1], r[2], r[3]);
        PDAnnotation a;
        switch (kind) {
            case "text": {
                PDAnnotationText t = new PDAnnotationText();
                t.setColor(rgb(1f, .78f, 0f));
                a = t;
                break;
            }
            case "freetext": {
                PDAnnotationFreeText f = new PDAnnotationFreeText();
                f.setDefaultAppearance("/Helv 10 Tf 0 g");
                f.setColor(rgb(0f, 0f, 0f));
                a = f;
                break;
            }
            case "square": {
                PDAnnotationSquare s = new PDAnnotationSquare();
                s.setColor(rgb(.78f, 0f, .78f));
                a = s;
                break;
            }
            case "circle": {
                PDAnnotationCircle c = new PDAnnotationCircle();
                c.setColor(rgb(0f, .35f, .78f));
                a = c;
                break;
            }
            case "stamp": {
                PDAnnotationRubberStamp s = new PDAnnotationRubberStamp();
                s.setName(PDAnnotationRubberStamp.NAME_DRAFT);
                s.setColor(rgb(0f, .5f, .5f));
                a = s;
                break;
            }
            case "ink": {
                PDAnnotationInk ink = new PDAnnotationInk();
                float[] path = new float[24];
                for (int k = 0; k < 12; k++) {
                    path[2 * k] = r[0] + 20 * k;
                    path[2 * k + 1] = r[1] + 30 + (k % 2 == 0 ? 0 : 40);
                }
                ink.setInkList(new float[][] {path});
                ink.setColor(rgb(.78f, .24f, 0f));
                a = ink;
                break;
            }
            case "line": {
                PDAnnotationLine l = new PDAnnotationLine();
                l.setLine(new float[] {r[0], r[3], r[2], r[1]});
                l.setColor(rgb(0f, 0f, .6f));
                a = l;
                break;
            }
            case "polygon": {
                PDAnnotationPolygon p = new PDAnnotationPolygon();
                p.setVertices(new float[] {r[0], r[3], r[2], r[3], r[2], r[1], r[0] + 30, r[1]});
                p.setColor(rgb(.3f, .3f, .3f));
                a = p;
                break;
            }
            case "polyline": {
                PDAnnotationPolyline p = new PDAnnotationPolyline();
                p.setVertices(new float[] {r[0], r[3], r[0] + 70, r[1], r[2], r[3]});
                p.setColor(rgb(.5f, 0f, .5f));
                a = p;
                break;
            }
            default: {
                PDAnnotationCaret c = new PDAnnotationCaret();
                c.setColor(rgb(0f, .5f, 0f));
                a = c;
            }
        }
        a.setRectangle(rr);
        return a;
    }

    static String createdJson(int page, String kind, float[] r, String via) {
        Map<String, Object> c = m();
        c.put("page", page);
        c.put("kind", kind);
        c.put("via", via);
        c.put("rect", new RawJson("[" + r[0] + "," + r[1] + "," + r[2] + "," + r[3] + "]"));
        c.put("contents", "RS02-" + kind);
        return obj(c);
    }

    static String errJson(int page, String kind, Exception e) {
        Map<String, Object> c = m();
        c.put("page", page);
        c.put("kind", kind);
        c.put("error", e.getClass().getSimpleName() + ": " + e.getMessage());
        return obj(c);
    }

    static Map<String, float[]> readTargets() throws IOException {
        String json = new String(Files.readAllBytes(new File(GEN, "manifest.json").toPath()), "UTF-8");
        Map<String, float[]> t = new LinkedHashMap<String, float[]>();
        for (String k : new String[] {"highlight", "underline", "strikeout", "squiggly"}) {
            int i = json.indexOf("\"markup_targets_pdf_rect\"");
            int j = json.indexOf("\"" + k + "\"", i);
            int s = json.indexOf('[', j), e = json.indexOf(']', s);
            String[] parts = json.substring(s + 1, e).split(",");
            float[] v = new float[4];
            for (int n = 0; n < 4; n++) v[n] = Float.parseFloat(parts[n].trim());
            t.put(k, v);
        }
        return t;
    }

    // ---------- RS-03 form fill ----------
    static String rs03() throws IOException {
        List<String> actions = new ArrayList<String>();
        try (PDDocument doc = Loader.loadPDF(new File(GEN, "rs03_form.pdf"))) {
            PDAcroForm form = doc.getDocumentCatalog().getAcroForm();
            String[][] plan = {{"nama", "Diisi PDFBox RS03"}, {"setuju", "check"}, {"pilihan", "B"}, {"kota", "Surabaya"}};
            for (String[] p : plan) {
                Map<String, Object> a = m();
                a.put("field", p[0]);
                try {
                    PDField f = form.getField(p[0]);
                    a.put("type", f == null ? null : f.getClass().getSimpleName());
                    if (f instanceof PDTextField) ((PDTextField) f).setValue(p[1]);
                    else if (f instanceof PDCheckBox) ((PDCheckBox) f).check();
                    else if (f instanceof PDRadioButton) ((PDRadioButton) f).setValue(p[1]);
                    else if (f instanceof PDComboBox) ((PDComboBox) f).setValue(p[1]);
                    else throw new IllegalStateException("field tidak ditemukan / tipe tak dikenal");
                    a.put("ok", true);
                    a.put("value_after", f.getValueAsString());
                } catch (Exception e) {
                    a.put("ok", false);
                    a.put("error", e.getClass().getSimpleName() + ": " + e.getMessage());
                }
                actions.add(obj(a));
            }
            doc.save(new File(OUT, "rs03_filled.pdf"));
        }
        Map<String, Object> res = m();
        res.put("output", "rs03_filled.pdf");
        res.put("actions", arr(actions));
        return obj(res);
    }

    // ---------- RS-04 field authoring ----------
    static String rs04() throws IOException {
        List<String> errors = new ArrayList<String>();
        try (PDDocument doc = new PDDocument()) {
            PDPage page = new PDPage(PDRectangle.A4);
            doc.addPage(page);
            PDType1Font helv = new PDType1Font(Standard14Fonts.FontName.HELVETICA);
            try (PDPageContentStream cs = new PDPageContentStream(doc, page)) {
                cs.beginText();
                cs.setFont(helv, 12);
                cs.newLineAtOffset(50, 782);
                cs.showText("RS04 field authoring");
                cs.endText();
            }
            PDAcroForm acro = new PDAcroForm(doc);
            doc.getDocumentCatalog().setAcroForm(acro);
            PDResources dr = new PDResources();
            dr.put(COSName.getPDFName("Helv"), helv);
            dr.put(COSName.getPDFName("ZaDb"), new PDType1Font(Standard14Fonts.FontName.ZAPF_DINGBATS));
            acro.setDefaultResources(dr);
            acro.setDefaultAppearance("/Helv 0 Tf 0 g");
            try {
                PDTextField tf = new PDTextField(acro);
                tf.setPartialName("rs04_text");
                tf.setDefaultAppearance("/Helv 12 Tf 0 0 0 rg");
                acro.getFields().add(tf);
                PDAnnotationWidget w = tf.getWidgets().get(0);
                w.setRectangle(rect(50, 842 - 124, 300, 842 - 100));
                w.setPage(page);
                w.setPrinted(true);
                page.getAnnotations().add(w);
                tf.setValue("awal");
            } catch (Exception e) {
                errors.add(q("text: " + e));
            }
            try {
                PDCheckBox cb = new PDCheckBox(acro);
                cb.setPartialName("rs04_check");
                acro.getFields().add(cb);
                PDAnnotationWidget w = cb.getWidgets().get(0);
                PDRectangle r = rect(50, 842 - 156, 66, 842 - 140);
                w.setRectangle(r);
                w.setPage(page);
                w.setPrinted(true);
                page.getAnnotations().add(w);
                // PDFBox tidak membangkitkan appearance checkbox otomatis: bangun /Yes dan /Off (pola contoh resmi CreateCheckBox).
                PDAppearanceDictionary ap = new PDAppearanceDictionary();
                PDAppearanceEntry normal = new PDAppearanceEntry(new org.apache.pdfbox.cos.COSDictionary());
                ap.setNormalAppearance(normal);
                w.setAppearance(ap);
                org.apache.pdfbox.cos.COSDictionary n = (org.apache.pdfbox.cos.COSDictionary) normal.getCOSObject();
                n.setItem(COSName.getPDFName("Yes"), checkboxStream(doc, r, true));
                n.setItem(COSName.Off, checkboxStream(doc, r, false));
                w.getCOSObject().setItem(COSName.AS, COSName.Off);
                cb.getCOSObject().setItem(COSName.V, COSName.Off);
            } catch (Exception e) {
                errors.add(q("checkbox: " + e));
            }
            doc.save(new File(OUT, "rs04_fields.pdf"));
        }
        Map<String, Object> res = m();
        res.put("output", "rs04_fields.pdf");
        res.put("errors", arr(errors));
        res.put("note", "appearance checkbox dibangun manual (tanpa generator otomatis di PDFBox)");
        return obj(res);
    }

    static PDAppearanceStream checkboxStream(PDDocument doc, PDRectangle r, boolean on) throws IOException {
        PDAppearanceStream s = new PDAppearanceStream(doc);
        s.setBBox(new PDRectangle(r.getWidth(), r.getHeight()));
        PDResources res = new PDResources();
        res.put(COSName.getPDFName("ZaDb"), new PDType1Font(Standard14Fonts.FontName.ZAPF_DINGBATS));
        s.setResources(res);
        try (PDPageContentStream cs = new PDPageContentStream(doc, s)) {
            cs.setLineWidth(1);
            cs.addRect(0.5f, 0.5f, r.getWidth() - 1, r.getHeight() - 1);
            cs.stroke();
            if (on) {
                cs.beginText();
                cs.setFont(new PDType1Font(Standard14Fonts.FontName.ZAPF_DINGBATS), 12);
                cs.newLineAtOffset(2.5f, 3.5f);
                cs.showText("\u2714");
                cs.endText();
            }
        }
        return s;
    }

    // ---------- RS-05 merge / extract ----------
    static String rs05() throws IOException {
        List<String> ops = new ArrayList<String>();
        File src = new File(GEN, "rs05_structure.pdf");
        File extra = new File(GEN, "rs05_merge_source.pdf");
        long t = System.nanoTime();
        try (PDDocument dest = Loader.loadPDF(src); PDDocument add = Loader.loadPDF(extra)) {
            new PDFMergerUtility().appendDocument(dest, add);
            dest.save(new File(OUT, "rs05_merge.pdf"));
        }
        ops.add(opJson("merge (PDFMergerUtility.appendDocument ke dokumen structure)", "rs05_merge.pdf", t));
        t = System.nanoTime();
        try (PDDocument doc = Loader.loadPDF(src)) {
            PDDocument part = new PageExtractor(doc, 2, 4).extract();
            part.save(new File(OUT, "rs05_extract_pageextractor.pdf"));
            part.close();
        }
        ops.add(opJson("extract p2-4 (PageExtractor ke dokumen baru)", "rs05_extract_pageextractor.pdf", t));
        t = System.nanoTime();
        try (PDDocument doc = Loader.loadPDF(src)) {
            // pertahankan p2-4 dengan menghapus halaman lain di dokumen yang sama
            doc.removePage(5);
            doc.removePage(4);
            doc.removePage(0);
            doc.save(new File(OUT, "rs05_extract_inplace.pdf"));
        }
        ops.add(opJson("extract p2-4 (hapus halaman lain secara in-place)", "rs05_extract_inplace.pdf", t));
        Map<String, Object> res = m();
        res.put("operations", arr(ops));
        return obj(res);
    }

    static String opJson(String op, String out, long t0) {
        Map<String, Object> o = m();
        o.put("op", op);
        o.put("output", out);
        o.put("ms", Math.round((System.nanoTime() - t0) / 1e4) / 100.0);
        return obj(o);
    }

    // ---------- RS-08 signature (test certificate only) ----------
    static String rs08() throws Exception {
        Security.addProvider(new BouncyCastleProvider());
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
        KeyPair kp = kpg.generateKeyPair();
        X500Name subject = new X500Name("CN=UnionPDF Spike Test Signer, O=UnionPDF Test Only");
        Date now = new Date();
        X509CertificateHolder holder = new JcaX509v3CertificateBuilder(subject, BigInteger.valueOf(now.getTime()),
                new Date(now.getTime() - 60000L), new Date(now.getTime() + 2L * 86400000L), subject, kp.getPublic())
                .build(new JcaContentSignerBuilder("SHA256WithRSA").build(kp.getPrivate()));
        final X509Certificate cert = new JcaX509CertificateConverter().getCertificate(holder);
        final PrivateKey key = kp.getPrivate();

        File in = new File(GEN, "rs02_annot_base.pdf");
        File out = new File(OUT, "rs08_signed.pdf");
        try (PDDocument doc = Loader.loadPDF(in); FileOutputStream fos = new FileOutputStream(out)) {
            PDSignature sig = new PDSignature();
            sig.setFilter(PDSignature.FILTER_ADOBE_PPKLITE);
            sig.setSubFilter(PDSignature.SUBFILTER_ADBE_PKCS7_DETACHED);
            sig.setName("UnionPDF Spike Test Signer");
            sig.setReason("RS-08 spike (test certificate, not trusted)");
            sig.setSignDate(Calendar.getInstance());
            doc.addSignature(sig, new SignatureInterface() {
                public byte[] sign(InputStream content) throws IOException {
                    try {
                        ByteArrayOutputStream bos = new ByteArrayOutputStream();
                        byte[] buf = new byte[8192];
                        int n;
                        while ((n = content.read(buf)) > 0) bos.write(buf, 0, n);
                        CMSSignedDataGenerator gen = new CMSSignedDataGenerator();
                        ContentSigner signer = new JcaContentSignerBuilder("SHA256WithRSA").build(key);
                        gen.addSignerInfoGenerator(new JcaSignerInfoGeneratorBuilder(
                                new JcaDigestCalculatorProviderBuilder().build()).build(signer, cert));
                        gen.addCertificates(new JcaCertStore(Arrays.asList(cert)));
                        return gen.generate(new CMSProcessableByteArray(bos.toByteArray()), false).getEncoded();
                    } catch (Exception e) {
                        throw new IOException(e);
                    }
                }
            });
            doc.saveIncremental(fos);
        }
        byte[] signedBytes = Files.readAllBytes(out.toPath());
        Map<String, Object> verifyOriginal = verify(signedBytes);
        byte[] tampered = signedBytes.clone();
        int pos = 400; // di dalam rentang byte pertama (sebelum /Contents)
        tampered[pos] = (byte) (tampered[pos] ^ 0x01);
        Files.write(new File(OUT, "rs08_signed_tampered.pdf").toPath(), tampered);
        Map<String, Object> verifyTampered = verify(tampered);
        Map<String, Object> res = m();
        res.put("output", "rs08_signed.pdf");
        res.put("certificate", "self-signed test certificate generated in-process (RSA 2048, valid 2 days); NOT trusted, no chain");
        res.put("verify_original_by_bouncycastle", new RawJson(obj(verifyOriginal)));
        res.put("verify_tampered_by_bouncycastle", new RawJson(obj(verifyTampered)));
        res.put("note", "verifikasi oleh library yang sama (BC) — bukan validator independen; rantai kepercayaan tidak dinilai");
        return obj(res);
    }

    static Map<String, Object> verify(byte[] pdf) {
        Map<String, Object> r = m();
        try (PDDocument doc = Loader.loadPDF(pdf)) {
            List<PDSignature> sigs = doc.getSignatureDictionaries();
            r.put("signature_count", sigs.size());
            if (sigs.isEmpty()) return r;
            PDSignature sig = sigs.get(0);
            int[] br = sig.getByteRange();
            r.put("byte_range", new RawJson(Arrays.toString(br)));
            r.put("byte_range_covers_file_except_contents", br.length == 4 && br[0] == 0 && (long) br[2] + br[3] == pdf.length);
            byte[] contents = sig.getContents(pdf);
            byte[] signed = sig.getSignedContent(pdf);
            CMSSignedData cms = new CMSSignedData(new CMSProcessableByteArray(signed), contents);
            Store<X509CertificateHolder> certs = cms.getCertificates();
            boolean ok = false;
            for (SignerInformation si : cms.getSignerInfos().getSigners()) {
                @SuppressWarnings("unchecked")
                Collection<X509CertificateHolder> match = certs.getMatches(si.getSID());
                X509CertificateHolder ch = match.iterator().next();
                ok = si.verify(new JcaSimpleSignerInfoVerifierBuilder().setProvider("BC").build(ch));
                r.put("signer_subject", ch.getSubject().toString());
            }
            r.put("cms_signature_valid_against_embedded_cert", ok);
        } catch (Exception e) {
            r.put("error", e.getClass().getSimpleName() + ": " + e.getMessage());
            r.put("cms_signature_valid_against_embedded_cert", false);
        }
        return r;
    }

    public static void main(String[] args) throws Exception {
        OUT.mkdirs();
        Map<String, Object> res = m();
        res.put("engine", "Apache PDFBox 3.0.8 + Bouncy Castle 1.84 on Java " + System.getProperty("java.version"));
        String[] steps = {"rs02", "rs03", "rs04", "rs05", "rs08"};
        for (String s : steps) {
            try {
                String r;
                if (s.equals("rs02")) r = rs02();
                else if (s.equals("rs03")) r = rs03();
                else if (s.equals("rs04")) r = rs04();
                else if (s.equals("rs05")) r = rs05();
                else r = rs08();
                res.put(s, new RawJson(r));
            } catch (Exception e) {
                Map<String, Object> err = m();
                err.put("fatal", e.getClass().getName() + ": " + e.getMessage());
                res.put(s, new RawJson(obj(err)));
            }
        }
        res.put("rs07", new RawJson(obj(new LinkedHashMap<String, Object>() {{
            put("status", "NOT_RUN");
            put("reason", "PDFBox 3.0.8 tidak menyediakan API redaksi; butuh implementasi kustom penyuntingan content stream");
        }})));
        String json = obj(res);
        Files.write(new File(OUT, "result.json").toPath(), json.getBytes("UTF-8"));
        System.out.println(json);
    }
}
