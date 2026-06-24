from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal, Slot

from app.core.repair_engine import run_repair
from app.models.app_settings import AppSettings
from app.models.repair_result import RepairJob


class RepairWorker(QObject):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, job: RepairJob, settings: AppSettings) -> None:
        super().__init__()
        self.job = job
        self.settings = settings
        self._cancel_event = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            result = run_repair(
                self.job,
                settings=self.settings,
                log_callback=self.log.emit,
                progress_callback=self.progress.emit,
                cancel_event=self._cancel_event,
            )
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))

    @Slot()
    def cancel(self) -> None:
        self._cancel_event.set()
        self.log.emit("Cancel requested. Waiting for the running process to stop...")
