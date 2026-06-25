from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from app.gui.widgets import make_section_title
from app.models.app_settings import AppSettings


class SettingsPage(QWidget):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings

        self.ffmpeg_path = self._path_row(settings.resolve_ffmpeg())
        self.ffprobe_path = self._path_row(settings.resolve_ffprobe())
        self.untrunc_path = self._path_row(settings.resolve_untrunc())
        self.output_folder = self._path_row(settings.default_output_folder, folder=True)

        self.default_mode = QComboBox()
        for label, value in [
            ("Auto repair", "auto"),
            ("Remux only", "remux"),
            ("Faststart / moov relocation", "faststart"),
            ("Re-encode", "reencode"),
            ("Recover with reference video", "untrunc"),
            ("Extract streams", "extract"),
        ]:
            self.default_mode.addItem(label, value)
        index = self.default_mode.findData(settings.default_repair_mode)
        if index >= 0:
            self.default_mode.setCurrentIndex(index)

        self.overwrite = QCheckBox()
        self.overwrite.setChecked(settings.overwrite_existing)
        self.keep_temp = QCheckBox()
        self.keep_temp.setChecked(settings.keep_temp_files)
        self.hardware = QCheckBox()
        self.hardware.setChecked(settings.hardware_acceleration)

        self.theme = QComboBox()
        self.theme.addItems(["dark", "light"])
        self.theme.setCurrentText(settings.theme)

        self.crf = QSpinBox()
        self.crf.setRange(0, 51)
        self.crf.setValue(settings.crf_quality)

        self.preset = QComboBox()
        self.preset.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"])
        self.preset.setCurrentText(settings.reencode_preset)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save)

        form = QFormLayout()
        form.addRow("FFmpeg path", self.ffmpeg_path)
        form.addRow("FFprobe path", self.ffprobe_path)
        form.addRow("Untrunc path", self.untrunc_path)
        form.addRow("Default output folder", self.output_folder)
        form.addRow("Default repair mode", self.default_mode)
        form.addRow("Overwrite existing files", self.overwrite)
        form.addRow("Keep temporary files", self.keep_temp)
        form.addRow("Theme", self.theme)
        form.addRow("Hardware acceleration", self.hardware)
        form.addRow("Default CRF quality", self.crf)
        form.addRow("Default re-encode preset", self.preset)

        layout = QVBoxLayout(self)
        layout.addWidget(make_section_title("Settings"))
        layout.addLayout(form)
        layout.addWidget(self.save_button)
        layout.addStretch(1)

    def save(self) -> None:
        self.settings.ffmpeg_path = self.ffmpeg_path.findChild(QLineEdit).text().strip()
        self.settings.ffprobe_path = self.ffprobe_path.findChild(QLineEdit).text().strip()
        self.settings.untrunc_path = self.untrunc_path.findChild(QLineEdit).text().strip()
        self.settings.default_output_folder = self.output_folder.findChild(QLineEdit).text().strip()
        self.settings.default_repair_mode = self.default_mode.currentData()
        self.settings.overwrite_existing = self.overwrite.isChecked()
        self.settings.keep_temp_files = self.keep_temp.isChecked()
        self.settings.theme = self.theme.currentText()
        self.settings.hardware_acceleration = self.hardware.isChecked()
        self.settings.crf_quality = self.crf.value()
        self.settings.reencode_preset = self.preset.currentText()
        self.settings.save()
        QMessageBox.information(self, "Settings saved", "Settings were saved.")

    def _path_row(self, value: str, folder: bool = False) -> QWidget:
        container = QWidget()
        edit = QLineEdit(value)
        button = QPushButton("Browse...")

        def browse() -> None:
            if folder:
                selected = QFileDialog.getExistingDirectory(self, "Select folder", edit.text())
            else:
                selected, _ = QFileDialog.getOpenFileName(self, "Select executable", edit.text(), "Executables (*.exe);;All files (*.*)")
            if selected:
                edit.setText(selected)

        button.clicked.connect(browse)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        return container
