from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.core.analyzer import analyze_video
from app.models.app_settings import AppSettings


class AnalysisWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, path: str, settings: AppSettings) -> None:
        super().__init__()
        self.path = path
        self.settings = settings

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(analyze_video(self.path, self.settings))
        except Exception as exc:
            self.failed.emit(str(exc))
