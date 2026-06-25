from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from app.gui.analysis_page import AnalysisPage
from app.gui.repair_page import RepairPage
from app.gui.settings_page import SettingsPage
from app.i18n import t
from app.models.app_settings import AppSettings


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = AppSettings.load()
        self.setWindowTitle("Video Fixer Pro")
        self._set_window_icon()
        self.resize(QSize(1100, 720))

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(210)
        self.nav_items = []
        for key in ["repair_video", "analyze_video", "settings"]:
            item = QListWidgetItem()
            self.sidebar.addItem(item)
            self.nav_items.append((item, key))

        self.stack = QStackedWidget()
        self.repair_page = RepairPage(self.settings)
        self.analysis_page = AnalysisPage(self.settings)
        self.settings_page = SettingsPage(self.settings)
        self.settings_page.language_changed.connect(self.retranslate)
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
        self.retranslate()
        self._load_stylesheet()

    def retranslate(self) -> None:
        language = self.settings.language
        for item, key in self.nav_items:
            item.setText(t(key, language))
        self.repair_page.retranslate()
        self.analysis_page.retranslate()
        self.settings_page.retranslate()

    def _load_stylesheet(self) -> None:
        style_path = Path(__file__).with_name("styles.qss")
        if style_path.exists():
            self.setStyleSheet(style_path.read_text(encoding="utf-8"))

    def _set_window_icon(self) -> None:
        icon_dir = Path(__file__).resolve().parents[1] / "assets" / "icon"
        for icon_path in (icon_dir / "icon.ico", icon_dir / "icon.png"):
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                break
