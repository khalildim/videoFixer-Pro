from __future__ import annotations

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QPushButton, QTextEdit, QVBoxLayout, QWidget, QMessageBox

from app.gui.widgets import FilePicker, make_section_title
from app.i18n import t
from app.models.app_settings import AppSettings
from app.models.video_info import VideoInfo
from app.workers.analysis_worker import AnalysisWorker


class AnalysisPage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.thread: QThread | None = None
        self.worker: AnalysisWorker | None = None

        self.file_picker = FilePicker("")
        self.analyze_button = QPushButton()
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.analyze_button.clicked.connect(self.start_analysis)

        self.section_title = make_section_title("")
        layout = QVBoxLayout(self)
        layout.addWidget(self.section_title)
        layout.addWidget(self.file_picker)
        layout.addWidget(self.analyze_button)
        layout.addWidget(self.output, 1)
        self.retranslate()

    def start_analysis(self) -> None:
        language = self.settings.language
        path = self.file_picker.path()
        if not path:
            QMessageBox.warning(self, t("missing_file", language), t("choose_video_to_analyze", language))
            return
        self.output.setPlainText(t("analyzing", language))
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
        language = self.settings.language
        self.analyze_button.setEnabled(True)
        self.output.setPlainText(
            "\n".join(
                [
                    f"{t('path', language)}: {info.path}",
                    f"{t('readable', language)}: {self._yes_no(info.readable)}",
                    f"{t('duration', language)}: {info.duration or t('unknown', language)}",
                    f"{t('video_codec', language)}: {info.codec_video or t('none', language)}",
                    f"{t('audio_codec', language)}: {info.codec_audio or t('none', language)}",
                    f"{t('resolution', language)}: {info.width or '?'}x{info.height or '?'}",
                    f"{t('fps', language)}: {info.fps or t('unknown', language)}",
                    f"{t('has_video', language)}: {self._yes_no(info.has_video)}",
                    f"{t('has_audio', language)}: {self._yes_no(info.has_audio)}",
                    f"{t('moov_atom_missing', language)}: {self._yes_no(info.moov_atom_missing)}",
                    f"{t('error', language)}: {info.error_message or t('none', language)}",
                ]
            )
        )

    def on_failed(self, message: str) -> None:
        self.analyze_button.setEnabled(True)
        self.output.setPlainText(message)

    def _clear_refs(self) -> None:
        self.thread = None
        self.worker = None

    def retranslate(self) -> None:
        language = self.settings.language
        self.file_picker.retranslate(t("video_file", language), language)
        self.analyze_button.setText(t("analyze", language))
        self.section_title.setText(t("analyze_video", language))

    def _yes_no(self, value: bool) -> str:
        return t("yes" if value else "no", self.settings.language)
