import os
import json
import requests
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QGridLayout, QScrollArea,
    QVBoxLayout, QFrame, QMessageBox, QLineEdit, QComboBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from io import BytesIO
from zipfile import ZipFile
from core.show_splash import show_splash

PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))
PLUGIN_JSON_URL = "https://raw.githubusercontent.com/michligtenberg2/hauswerk-plugins/main/plugins.json"

class PluginStoreGridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plugin Store")
        self.all_plugins = []

        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Zoek plugins...")
        self.search_input.textChanged.connect(self.filter_plugins)
        layout.addWidget(self.search_input)

        self.tag_filter = QComboBox()
        self.tag_filter.addItem("Alle tags")
        self.tag_filter.currentTextChanged.connect(self.filter_plugins)
        layout.addWidget(self.tag_filter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll)

        self.load_plugins()

    def load_plugins(self):
        try:
            response = requests.get(PLUGIN_JSON_URL)
            response.raise_for_status()
            plugins = response.json()
            self.all_plugins = plugins
        except Exception as e:
            error_label = QLabel(f"❌ Fout bij laden van pluginlijst: {e}")
            self.grid_layout.addWidget(error_label, 0, 0)
            return

        self.display_plugins(self.all_plugins)

    def filter_plugins(self):
        term = self.search_input.text().strip().lower()
        selected_tag = self.tag_filter.currentText()

        filtered = []
        for plugin in self.all_plugins:
            name_match = term in plugin['name'].lower()
            tag_match = selected_tag == "Alle tags"
            if name_match and tag_match:
                filtered.append(plugin)

        self.display_plugins(filtered)

    def display_plugins(self, plugins):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        row, col = 0, 0
        for plugin in plugins:
            card = self.create_plugin_card(plugin)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def create_plugin_card(self, plugin):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 6px; padding: 10px; }")
        layout = QVBoxLayout(frame)

        if plugin.get("icon_url"):
            try:
                icon_data = requests.get(plugin["icon_url"]).content
                pixmap = QPixmap()
                pixmap.loadFromData(icon_data)
                image = QLabel()
                image.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
                image.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(image)
            except:
                layout.addWidget(QLabel("🧩"))
        else:
            layout.addWidget(QLabel("🧩"))

        title = QLabel(f"<b>{plugin['name']}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(plugin['description'])
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        btn = QPushButton("➕ Installeer")
        btn.clicked.connect(lambda _, p=plugin: self.install_plugin(p))
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return frame

    def install_plugin(self, plugin):
        try:
            zip_url = plugin['zip_url']
            response = requests.get(zip_url)
            response.raise_for_status()
            with ZipFile(BytesIO(response.content)) as zip_file:
                zip_file.extractall(os.path.join(PLUGIN_DIR, plugin['name'].lower()))
            QMessageBox.information(self, "Installatie voltooid", f"✅ '{plugin['name']}' is geïnstalleerd.")
        except Exception as e:
            QMessageBox.critical(self, "Fout bij installatie", f"❌ {e}")
