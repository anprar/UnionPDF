"""Pemantau pekerjaan latar (background job).

Pola: ``QThreadPool`` + ``QRunnable`` + objek ``QObject`` terpisah untuk
signal (PySide6 hanya mengizinkan ``Signal`` pada turunan ``QObject``).

Bukti spike: docs/TECH_SPIKES.md S9.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class JobResult:
    """Hasil akhir sebuah pekerjaan."""

    status: JobStatus
    value: Any = None
    error: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status is JobStatus.SUCCEEDED


class CancelToken:
    """Token pembatalan yang dapat diperiksa worker pada loop."""

    __slots__ = ("_cancelled",)

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled


class JobSignals(QObject):
    """Signal untukQJ worker (harus turunan QObject)."""

    progress = Signal(int, int, str)
    finished = Signal(object)
    failed = Signal(str)


@dataclass(slots=True)
class JobSpec:
    """Deskripsi pekerjaan yang bisa dijalankan."""

    name: str
    func: Callable[..., Any]
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    total_steps: int = 0
    label: str = ""


class Job:
    """Satu pekerjaan yang sedang berjalan."""

    def __init__(self, spec: JobSpec) -> None:
        self.spec = spec
        self.token = CancelToken()
        self.signals = JobSignals()
        self.result: JobResult | None = None

    def cancel(self) -> None:
        self.token.cancel()


class _Worker(QRunnable):
    def __init__(self, job: Job) -> None:
        super().__init__()
        self._job = job

    def run(self) -> None:  # pragma: no cover - dijalankan di thread pool
        spec = self._job.spec
        try:
            value = spec.func(
                *spec.args,
                progress=self._job.signals.progress.emit,
                cancel_token=self._job.token,
                **spec.kwargs,
            )
            if self._job.token.cancelled:
                self._job.signals.finished.emit(
                    JobResult(status=JobStatus.CANCELLED, value=value)
                )
            else:
                self._job.signals.finished.emit(
                    JobResult(status=JobStatus.SUCCEEDED, value=value)
                )
        except Exception as exc:  # noqa: BLE001
            self._job.signals.finished.emit(
                JobResult(status=JobStatus.FAILED, error=str(exc))
            )


class JobRunner:
    """Menjalankan pekerjaan di luar thread UI."""

    def __init__(self, max_threads: int = 2) -> None:
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(max_threads)
        self._jobs: list[Job] = []

    def submit(
        self,
        spec: JobSpec,
        on_progress: Callable[[int, int, str], None] | None = None,
        on_finished: Callable[[JobResult], None] | None = None,
    ) -> Job:
        job = Job(spec)
        if on_progress is not None:
            job.signals.progress.connect(on_progress)
        if on_finished is not None:
            job.signals.finished.connect(on_finished)
        self._jobs.append(job)
        self._pool.start(_Worker(job))
        return job

    def cancel_all(self) -> None:
        for job in self._jobs:
            job.cancel()

    def wait_for_all(self, timeout_ms: int = 30_000) -> bool:
        return self._pool.waitForDone(timeout_ms)
