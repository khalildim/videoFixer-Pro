from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class FilePicker(QWidget):
    def __init__(self, label: str, mode: str = "file", optional: bool = False) -> None:
        super().__init__()
        self.mode = mode
        self.optional = optional
        self.label = QLabel(label)
        self.edit = DropLineEdit()
        self.edit.setPlaceholderText("Optional" if optional else "")
        self.button = QPushButton("Browse...")
        self.button.clicked.connect(self.browse)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.button)

    def path(self) -> str:
        return self.edit.text().strip()

    def set_path(self, path: str) -> None:
        self.edit.setText(path)

    def browse(self) -> None:
        if self.mode == "folder":
            selected = QFileDialog.getExistingDirectory(self, "Select folder", self.path() or str(Path.home()))
        else:
            selected, _ = QFileDialog.getOpenFileName(
                self,
                "Select video",
                self.path() or str(Path.home()),
                "Video files (*.mp4 *.mov *.m4v *.3gp);;All files (*.*)",
            )
        if selected:
            self.set_path(selected)


class DropLineEdit(QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        urls = event.mimeData().urls()
        if urls:
            self.setText(urls[0].toLocalFile())
            event.acceptProposedAction()


def make_section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return label
