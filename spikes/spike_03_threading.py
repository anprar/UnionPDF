"""Spike 03 - Background job: progress, cancel, GUI non-blocking.

Menguji pola QThreadPool + QRunnable dengan token pembatalan,
di bawah QT_QPA_PLATFORM=offscreen sehingga tidak butuh display.

Output: spikes/out/spike_03_threading.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import (  # noqa: E402
    QCoreApplication,
    QObject,
    QRunnable,
    QThreadPool,
    QTimer,
    Signal,
)

OUT = Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)

results: dict = {"spike": "03_threading"}


class CancelToken:
    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled


class JobSignals(QObject):
    """PySide6 hanya mengizinkan Signal pada turunan QObject."""

    progress = Signal(int, int)
    finished = Signal(dict)
    failed = Signal(str)


class Worker(QRunnable):
    def __init__(self, total_steps: int, step_delay: float, token: CancelToken, signals: JobSignals) -> None:
        super().__init__()
        self.total_steps = total_steps
        self.step_delay = step_delay
        self.token = token
        self.signals = signals
        self.steps_done = 0

    def run(self) -> None:
        try:
            for i in range(1, self.total_steps + 1):
                if self.token.cancelled:
                    self.signals.finished.emit({"cancelled": True, "steps_done": self.steps_done})
                    return
                time.sleep(self.step_delay)
                self.steps_done = i
                self.signals.progress.emit(i, self.total_steps)
            self.signals.finished.emit({"cancelled": False, "steps_done": self.steps_done})
        except Exception as exc:  # noqa: BLE001
            self.signals.failed.emit(str(exc))


def run_case(app: QCoreApplication, total: int, delay: float, cancel_after_ms: int | None) -> dict:
    pool = QThreadPool()
    pool.setMaxThreadCount(2)
    token = CancelToken()
    signals = JobSignals()
    worker = Worker(total, delay, token, signals)
    state = {"progress_events": 0, "last": None, "result": None, "error": None}

    def on_progress(c: int, t: int) -> None:
        state["progress_events"] += 1
        state["last"] = (c, t)

    signals.progress.connect(on_progress)
    signals.finished.connect(lambda r: state.update(result=r))
    signals.failed.connect(lambda e: state.update(error=e))

    t0 = time.perf_counter()
    pool.start(worker)

    timer = None
    if cancel_after_ms is not None:
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(token.cancel)
        timer.start(cancel_after_ms)

    deadline = time.perf_counter() + 60
    while state["result"] is None and state["error"] is None and time.perf_counter() < deadline:
        app.processEvents()
        time.sleep(0.005)
    if timer is not None:
        timer.stop()
    elapsed = (time.perf_counter() - t0) * 1000
    pool.waitForDone(5000)
    return {
        "total_steps": total,
        "step_delay_s": delay,
        "cancel_after_ms": cancel_after_ms,
        "elapsed_ms": round(elapsed, 1),
        "progress_events": state["progress_events"],
        "last_progress": state["last"],
        "result": state["result"],
        "error": state["error"],
    }


def main() -> int:
    app = QCoreApplication(sys.argv)
    results["platform"] = os.environ.get("QT_QPA_PLATFORM")

    # Kasus 1: pekerjaan normal selesai penuh
    results["case_full_run"] = run_case(app, total=20, delay=0.02, cancel_after_ms=None)

    # Kasus 2: dibatalkan di tengah jalan
    results["case_cancelled"] = run_case(app, total=200, delay=0.02, cancel_after_ms=300)

    # Kasus 3: pembatalan instan (sebelum worker mulai)
    results["case_cancel_immediate"] = run_case(app, total=200, delay=0.02, cancel_after_ms=1)

    # Verifikasi: event loop tetap responsif selama worker berjalan?
    t0 = time.perf_counter()
    ticks = 0
    token = CancelToken()
    signals2 = JobSignals()
    worker = Worker(100, 0.01, token, signals2)
    pool = QThreadPool()
    pool.start(worker)
    while time.perf_counter() - t0 < 1.0:
        app.processEvents()
        ticks += 1
        time.sleep(0.001)
    results["event_loop_responsive"] = {
        "ticks_in_1s": ticks,
        "note": "tick >= 100 berarti loop tetap memproses event saat worker berjalan",
    }
    token.cancel()
    pool.waitForDone(5000)

    (OUT / "spike_03_threading.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
