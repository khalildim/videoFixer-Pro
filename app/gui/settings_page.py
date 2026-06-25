from __future__ import annotations

from PySide6.QtCore import Signal
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
from app.i18n import language_items, t
from app.models.app_settings import AppSettings


class SettingsPage(QWidget):
    language_changed = Signal(str)

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.path_browse_buttons: list[QPushButton] = []

        self.ffmpeg_path = self._path_row(settings.resolve_ffmpeg())
        self.ffprobe_path = self._path_row(settings.resolve_ffprobe())
        self.untrunc_path = self._path_row(settings.resolve_untrunc())
        self.output_folder = self._path_row(settings.default_output_folder, folder=True)

        self.default_mode = QComboBox()
        self.mode_items = [
            ("auto_repair", "auto"),
            ("remux_only", "remux"),
            ("faststart", "faststart"),
            ("reencode", "reencode"),
            ("recover_with_reference", "untrunc"),
            ("extract_streams", "extract"),
        ]
        self._populate_modes()
        index = self.default_mode.findData(settings.default_repair_mode)
        if index >= 0:
            self.default_mode.setCurrentIndex(index)

        self.language = QComboBox()
        for label, value in language_items():
            self.language.addItem(label, value)
        index = self.language.findData(settings.language)
        if index >= 0:
            self.language.setCurrentIndex(index)

        self.overwrite = QCheckBox()
        self.overwrite.setChecked(settings.overwrite_existing)
        self.keep_temp = QCheckBox()
        self.keep_temp.setChecked(settings.keep_temp_files)
        self.hardware = QCheckBox()
        self.hardware.setChecked(settings.hardware_acceleration)

        self.crf = QSpinBox()
        self.crf.setRange(0, 51)
        self.crf.setValue(settings.crf_quality)

        self.preset = QComboBox()
        self.preset.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"])
        self.preset.setCurrentText(settings.reencode_preset)

        self.save_button = QPushButton()
        self.save_button.clicked.connect(self.save)

        self.form_labels: dict[str, QLabel] = {}
        form = QFormLayout()
        self._add_row(form, "ffmpeg_path", self.ffmpeg_path)
        self._add_row(form, "ffprobe_path", self.ffprobe_path)
        self._add_row(form, "untrunc_path", self.untrunc_path)
        self._add_row(form, "default_output_folder", self.output_folder)
        self._add_row(form, "default_repair_mode", self.default_mode)
        self._add_row(form, "language", self.language)
        self._add_row(form, "overwrite_existing_files", self.overwrite)
        self._add_row(form, "keep_temporary_files", self.keep_temp)
        self._add_row(form, "hardware_acceleration", self.hardware)
        self._add_row(form, "default_crf_quality", self.crf)
        self._add_row(form, "default_reencode_preset", self.preset)

        self.section_title = make_section_title("")
        layout = QVBoxLayout(self)
        layout.addWidget(self.section_title)
        layout.addLayout(form)
        layout.addWidget(self.save_button)
        layout.addStretch(1)
        self.retranslate()

    def _populate_modes(self) -> None:
        current = self.default_mode.currentData()
        self.default_mode.blockSignals(True)
        self.default_mode.clear()
        for label, value in [
            (t(key, self.settings.language), value) for key, value in self.mode_items
        ]:
            self.default_mode.addItem(label, value)
        if current:
            index = self.default_mode.findData(current)
            if index >= 0:
                self.default_mode.setCurrentIndex(index)
        self.default_mode.blockSignals(False)

    def save(self) -> None:
        previous_language = self.settings.language
        self.settings.ffmpeg_path = self.ffmpeg_path.findChild(QLineEdit).text().strip()
        self.settings.ffprobe_path = self.ffprobe_path.findChild(QLineEdit).text().strip()
        self.settings.untrunc_path = self.untrunc_path.findChild(QLineEdit).text().strip()
        self.settings.default_output_folder = self.output_folder.findChild(QLineEdit).text().strip()
        self.settings.default_repair_mode = self.default_mode.currentData()
        self.settings.language = self.language.currentData()
        self.settings.overwrite_existing = self.overwrite.isChecked()
        self.settings.keep_temp_files = self.keep_temp.isChecked()
        self.settings.hardware_acceleration = self.hardware.isChecked()
        self.settings.crf_quality = self.crf.value()
        self.settings.reencode_preset = self.preset.currentText()
        self.settings.save()
        if self.settings.language != previous_language:
            self.retranslate()
            self.language_changed.emit(self.settings.language)
        QMessageBox.information(self, t("settings_saved", self.settings.language), t("settings_saved_message", self.settings.language))

    def _path_row(self, value: str, folder: bool = False) -> QWidget:
        container = QWidget()
        edit = QLineEdit(value)
        button = QPushButton()
        self.path_browse_buttons.append(button)

        def browse() -> None:
            if folder:
                selected = QFileDialog.getExistingDirectory(self, t("select_folder", self.settings.language), edit.text())
            else:
                selected, _ = QFileDialog.getOpenFileName(
                    self,
                    t("select_executable", self.settings.language),
                    edit.text(),
                    t("executables_filter", self.settings.language),
                )
            if selected:
                edit.setText(selected)

        button.clicked.connect(browse)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        return container

    def _add_row(self, form: QFormLayout, key: str, widget: QWidget) -> None:
        label = QLabel()
        self.form_labels[key] = label
        form.addRow(label, widget)

    def retranslate(self) -> None:
        language = self.settings.language
        current_mode = self.default_mode.currentData()
        self._populate_modes()
        if current_mode:
            index = self.default_mode.findData(current_mode)
            if index >= 0:
                self.default_mode.setCurrentIndex(index)
        for key, label in self.form_labels.items():
            label.setText(t(key, language))
        for button in self.path_browse_buttons:
            button.setText(t("browse", language))
        self.section_title.setText(t("settings", language))
        self.save_button.setText(t("save_settings", language))
