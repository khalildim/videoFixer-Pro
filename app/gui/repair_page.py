from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.file_utils import open_folder
from app.gui.widgets import FilePicker, make_section_title
from app.i18n import t
from app.models.app_settings import AppSettings
from app.models.repair_result import RepairJob, RepairResult
from app.workers.repair_worker import RepairWorker


class RepairPage(QWidget):
    repair_started = Signal()
    repair_finished = Signal(object)

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.worker: RepairWorker | None = None
        self.thread: QThread | None = None
        self.last_output: str | None = None

        self.input_picker = FilePicker("")
        self.reference_picker = FilePicker("", optional=True)
        self.output_picker = FilePicker("", mode="folder")
        if settings.default_output_folder:
            self.output_picker.set_path(settings.default_output_folder)

        self.mode_combo = QComboBox()
        self.mode_items = [
            ("auto_repair", "auto"),
            ("remux_only", "remux"),
            ("faststart", "faststart"),
            ("reencode", "reencode"),
            ("recover_with_reference", "untrunc"),
            ("extract_streams", "extract"),
        ]
        self._populate_modes()
        self._select_mode(settings.default_repair_mode)

        self.start_button = QPushButton()
        self.cancel_button = QPushButton()
        self.open_output_button = QPushButton()
        self.cancel_button.setEnabled(False)
        self.open_output_button.setEnabled(False)

        self.progress = QProgressBar()
        self.status = QLabel()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        self.start_button.clicked.connect(self.start_repair)
        self.cancel_button.clicked.connect(self.cancel_repair)
        self.open_output_button.clicked.connect(self.open_output)

        form = QFormLayout()
        form.addRow(self.input_picker)
        form.addRow(self.reference_picker)
        form.addRow(self.output_picker)
        self.mode_label = QLabel()
        form.addRow(self.mode_label, self.mode_combo)

        button_row = QHBoxLayout()
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.cancel_button)
        button_row.addStretch(1)
        button_row.addWidget(self.open_output_button)

        self.section_title = make_section_title("")
        layout = QVBoxLayout(self)
        layout.addWidget(self.section_title)
        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addWidget(self.log_view, 1)
        self.retranslate()

    def start_repair(self) -> None:
        language = self.settings.language
        input_file = self.input_picker.path()
        output_folder = self.output_picker.path()
        if not input_file or not output_folder:
            QMessageBox.warning(self, t("missing_input", language), t("choose_damaged_video_and_output", language))
            return

        self.log_view.clear()
        self.progress.setValue(0)
        self.status.setText(t("repair_running", language))
        self.last_output = None
        self.open_output_button.setEnabled(False)

        job = RepairJob(
            input_file=input_file,
            output_folder=output_folder,
            reference_file=self.reference_picker.path() or None,
            mode=self.mode_combo.currentData(),
        )
        self.thread = QThread(self)
        self.worker = RepairWorker(job, self.settings)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.append_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_worker_refs)

        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.repair_started.emit()
        self.thread.start()

    def cancel_repair(self) -> None:
        if self.worker:
            self.worker.cancel()
        self.cancel_button.setEnabled(False)

    def append_log(self, message: str) -> None:
        self.log_view.append(message)
        self.log_view.moveCursor(QTextCursor.End)

    def on_finished(self, result: RepairResult) -> None:
        language = self.settings.language
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status.setText(result.message)
        self.last_output = result.output_file or result.log_file
        self.open_output_button.setEnabled(bool(self.last_output))
        self.repair_finished.emit(result)
        if result.success:
            QMessageBox.information(self, t("repair_complete", language), result.message)
        else:
            QMessageBox.warning(self, t("repair_failed", language), result.message)

    def on_failed(self, message: str) -> None:
        language = self.settings.language
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status.setText(message)
        QMessageBox.critical(self, t("repair_error", language), message)

    def open_output(self) -> None:
        target = self.last_output or self.output_picker.path()
        if target:
            open_folder(Path(target))

    def _clear_worker_refs(self) -> None:
        self.worker = None
        self.thread = None

    def _select_mode(self, mode: str) -> None:
        index = self.mode_combo.findData(mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)

    def _populate_modes(self) -> None:
        current = self.mode_combo.currentData()
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        for key, value in self.mode_items:
            self.mode_combo.addItem(t(key, self.settings.language), value)
        if current:
            self._select_mode(str(current))
        self.mode_combo.blockSignals(False)

    def retranslate(self) -> None:
        language = self.settings.language
        current = self.mode_combo.currentData()
        self._populate_modes()
        if current:
            self._select_mode(str(current))
        self.input_picker.retranslate(t("damaged_video", language), language)
        self.reference_picker.retranslate(t("reference_video", language), language)
        self.output_picker.retranslate(t("output_folder", language), language)
        self.mode_label.setText(t("repair_mode", language))
        self.start_button.setText(t("start_repair", language))
        self.cancel_button.setText(t("cancel", language))
        self.open_output_button.setText(t("open_output_folder", language))
        self.section_title.setText(t("repair_video", language))
        if not self.thread:
            self.status.setText(t("ready", language))
