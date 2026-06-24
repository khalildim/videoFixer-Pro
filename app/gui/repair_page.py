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

        self.input_picker = FilePicker("Damaged video")
        self.reference_picker = FilePicker("Reference video", optional=True)
        self.output_picker = FilePicker("Output folder", mode="folder")
        if settings.default_output_folder:
            self.output_picker.set_path(settings.default_output_folder)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Auto repair", "auto")
        self.mode_combo.addItem("Remux only", "remux")
        self.mode_combo.addItem("Faststart / moov relocation", "faststart")
        self.mode_combo.addItem("Re-encode", "reencode")
        self.mode_combo.addItem("Recover with reference video", "untrunc")
        self.mode_combo.addItem("Extract streams", "extract")
        self._select_mode(settings.default_repair_mode)

        self.start_button = QPushButton("Start Repair")
        self.cancel_button = QPushButton("Cancel")
        self.open_output_button = QPushButton("Open Output Folder")
        self.cancel_button.setEnabled(False)
        self.open_output_button.setEnabled(False)

        self.progress = QProgressBar()
        self.status = QLabel("Ready")
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        self.start_button.clicked.connect(self.start_repair)
        self.cancel_button.clicked.connect(self.cancel_repair)
        self.open_output_button.clicked.connect(self.open_output)

        form = QFormLayout()
        form.addRow(self.input_picker)
        form.addRow(self.reference_picker)
        form.addRow(self.output_picker)
        form.addRow("Repair mode", self.mode_combo)

        button_row = QHBoxLayout()
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.cancel_button)
        button_row.addStretch(1)
        button_row.addWidget(self.open_output_button)

        layout = QVBoxLayout(self)
        layout.addWidget(make_section_title("Repair Video"))
        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addWidget(self.log_view, 1)

    def start_repair(self) -> None:
        input_file = self.input_picker.path()
        output_folder = self.output_picker.path()
        if not input_file or not output_folder:
            QMessageBox.warning(self, "Missing input", "Choose a damaged video and an output folder.")
            return

        self.log_view.clear()
        self.progress.setValue(0)
        self.status.setText("Repair running...")
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
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status.setText(result.message)
        self.last_output = result.output_file or result.log_file
        self.open_output_button.setEnabled(bool(self.last_output))
        self.repair_finished.emit(result)
        if result.success:
            QMessageBox.information(self, "Repair complete", result.message)
        else:
            QMessageBox.warning(self, "Repair failed", result.message)

    def on_failed(self, message: str) -> None:
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status.setText(message)
        QMessageBox.critical(self, "Repair error", message)

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
