package org.unionpdf.worker;

import java.util.Map;

/** Error with a stable code that is reported to the host as a structured error response. */
final class WorkerException extends Exception {
    final String code;
    final Map<String, Object> details;

    WorkerException(String code, String message) {
        this(code, message, null);
    }

    WorkerException(String code, String message, Map<String, Object> details) {
        super(message);
        this.code = code;
        this.details = details;
    }
}
