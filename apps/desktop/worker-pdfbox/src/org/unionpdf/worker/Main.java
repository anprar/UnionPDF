package org.unionpdf.worker;

import java.io.BufferedReader;
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * UnionPDF PDFBox worker. Protocol (one JSON object per line, UTF-8):
 *   host -> worker: {"id": "...", "op": "...", "params": {...}}
 *   worker -> host: {"type": "ready", "protocol": 1, ...} once at start, then per request
 *                   {"id", "type": "progress", "stage"} (0..n) and exactly one
 *                   {"id", "type": "result", "data"} or {"id", "type": "error", "code", "message"}.
 * Only protocol messages are written to stdout; System.out is redirected to stderr so that
 * library output can never corrupt the response channel. Requests are processed sequentially.
 */
public final class Main {
    public static final int PROTOCOL = 1;
    private static PrintStream proto;

    private Main() {}

    public static void main(String[] args) throws IOException {
        proto = new PrintStream(new FileOutputStream(FileDescriptor.out), true, "UTF-8");
        System.setOut(System.err);
        Logger root = Logger.getLogger("");
        root.setLevel(Level.SEVERE);
        for (Handler h : root.getHandlers()) h.setLevel(Level.SEVERE);

        send(Ops.map("type", "ready", "protocol", PROTOCOL, "pdfbox", org.apache.pdfbox.util.Version.getVersion(),
                "java", System.getProperty("java.version")));
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String line;
        while ((line = in.readLine()) != null) {
            if (line.trim().isEmpty()) continue;
            if (!handle(line)) break;
        }
    }

    private static synchronized void send(Map<String, Object> msg) {
        proto.println(Json.write(msg));
        proto.flush();
    }

    @SuppressWarnings("unchecked")
    private static boolean handle(String line) {
        String id = null;
        try {
            Object parsed;
            try {
                parsed = Json.parse(line);
            } catch (RuntimeException e) {
                throw new WorkerException("bad_request", "JSON tidak valid: " + e.getMessage());
            }
            if (!(parsed instanceof Map)) throw new WorkerException("bad_request", "request harus objek JSON");
            Map<String, Object> req = (Map<String, Object>) parsed;
            id = req.get("id") instanceof String ? (String) req.get("id") : null;
            if (id == null) throw new WorkerException("bad_request", "request tanpa id");
            String op = req.get("op") instanceof String ? (String) req.get("op") : "";
            if ("shutdown".equals(op)) {
                send(Ops.map("id", id, "type", "result", "data", Ops.map()));
                return false;
            }
            Map<String, Object> params = req.get("params") instanceof Map ? (Map<String, Object>) req.get("params") : Ops.map();
            final String rid = id;
            Object data = Ops.run(op, params, new Ops.Progress() {
                public void stage(String text) {
                    send(Ops.map("id", rid, "type", "progress", "stage", text));
                }
            });
            send(Ops.map("id", id, "type", "result", "data", data));
        } catch (WorkerException e) {
            Map<String, Object> m = Ops.map("id", id, "type", "error", "code", e.code, "message", e.getMessage());
            if (e.details != null) m.put("details", e.details);
            send(m);
        } catch (IOException e) {
            send(Ops.map("id", id, "type", "error", "code", "io", "message", e.getClass().getSimpleName() + ": " + e.getMessage()));
        } catch (Throwable t) {
            send(Ops.map("id", id, "type", "error", "code", "internal", "message", t.getClass().getName() + ": " + t.getMessage()));
        }
        return true;
    }
}
