from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from app.gui.analysis_page import AnalysisPage
from app.gui.repair_page import RepairPage
from app.gui.settings_page import SettingsPage
from app.models.app_settings import AppSettings


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = AppSettings.load()
        self.setWindowTitle("VideoFixer Pro")
        self.resize(QSize(1100, 720))

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(210)
        for label in ["Repair Video", "Analyze Video", "Settings"]:
            self.sidebar.addItem(QListWidgetItem(label))

        self.stack = QStackedWidget()
        self.repair_page = RepairPage(self.settings)
        self.analysis_page = AnalysisPage(self.settings)
        self.settings_page = SettingsPage(self.settings)
        self.stack.addWidget(self.repair_page)
        self.stack.addWidget(self.analysis_page)
        self.stack.addWidget(self.settings_page)

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self._load_stylesheet()

    def _load_stylesheet(self) -> None:
        style_path = Path(__file__).with_name("styles.qss")
        if style_path.exists():
            self.setStyleSheet(style_path.read_text(encoding="utf-8"))
