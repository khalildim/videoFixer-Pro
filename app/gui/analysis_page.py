from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QPushButton, QTextEdit, QVBoxLayout, QWidget, QMessageBox

from app.gui.widgets import FilePicker, make_section_title
from app.models.app_settings import AppSettings
from app.models.video_info import VideoInfo
from app.workers.analysis_worker import AnalysisWorker


class AnalysisPage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.thread: QThread | None = None
        self.worker: AnalysisWorker | None = None

        self.file_picker = FilePicker("Video file")
        self.analyze_button = QPushButton("Analyze")
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.analyze_button.clicked.connect(self.start_analysis)

        layout = QVBoxLayout(self)
        layout.addWidget(make_section_title("Analyze Video"))
        layout.addWidget(self.file_picker)
        layout.addWidget(self.analyze_button)
        layout.addWidget(self.output, 1)

    def start_analysis(self) -> None:
        path = self.file_picker.path()
        if not path:
            QMessageBox.warning(self, "Missing file", "Choose a video file to analyze.")
            return
        self.output.setPlainText("Analyzing...")
        self.analyze_button.setEnabled(False)
        self.thread = QThread(self)
        self.worker = AnalysisWorker(path, self.settings)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_refs)
        self.thread.start()

    def on_finished(self, info: VideoInfo) -> None:
        self.analyze_button.setEnabled(True)
        self.output.setPlainText(
            "\n".join(
                [
                    f"Path: {info.path}",
                    f"Readable: {info.readable}",
                    f"Duration: {info.duration or 'unknown'}",
                    f"Video codec: {info.codec_video or 'none'}",
                    f"Audio codec: {info.codec_audio or 'none'}",
                    f"Resolution: {info.width or '?'}x{info.height or '?'}",
                    f"FPS: {info.fps or 'unknown'}",
                    f"Has video: {info.has_video}",
                    f"Has audio: {info.has_audio}",
                    f"Moov atom missing: {info.moov_atom_missing}",
                    f"Error: {info.error_message or 'none'}",
                ]
            )
        )

    def on_failed(self, message: str) -> None:
        self.analyze_button.setEnabled(True)
        self.output.setPlainText(message)

    def _clear_refs(self) -> None:
        self.thread = None
        self.worker = None
