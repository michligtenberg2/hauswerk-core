import os
import importlib.util
import json
import zipfile
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QComboBox, QMenuBar, QMenu, QHBoxLayout
)
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtCore import Qt, QPoint

from widgets.pluginstoregrid import PluginStoreGridWidget
from widgets.dashboard import DashboardTab
from core.log_tab import LogTab
from core.show_splash import show_splash
from core.settings import SettingsManager
from core.style import StyleManager
from core.logger import Logger
from widgets.hpb import PluginGeneratorWidget
from widgets.hpb import PluginUploadTab
from widgets.experimental import ExperimentalTab


PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")
LAB_ICON_PATH = os.path.join(os.path.dirname(__file__), "resources", "icons", "magic.svg")

def load_plugin(path):
    Logger.log(f"🔄 Plugin wordt geladen vanaf: {path}")

    metadata_path = os.path.join(path, "metadata.json")
    if not os.path.isfile(metadata_path):
        Logger.log(f"⚠️ 'metadata.json' ontbreekt in {path}, plugin wordt overgeslagen")
        return None

    try:
        with open(metadata_path) as f:
            meta = json.load(f)
    except Exception as e:
        Logger.log(f"⚠️ Kan metadata.json niet lezen in {path}: {e}")
        return None

    required = {"name", "entry", "class"}
    if not required.issubset(meta):
        Logger.log(f"⚠️ metadata.json mist vereiste velden in {path}, plugin wordt overgeslagen")
        return None

    entry_path = os.path.join(path, meta["entry"])
    if not os.path.isfile(entry_path):
        Logger.log(f"⚠️ Entry-bestand '{entry_path}' ontbreekt, plugin wordt overgeslagen")
        return None

    try:
        spec = importlib.util.spec_from_file_location(meta["name"], entry_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin_class = getattr(module, meta["class"])
        icon_path = os.path.join(path, meta.get("icon", ""))
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        Logger.log(f"✅ Plugin '{meta['name']}' geladen")
        return (meta["name"], plugin_class(), icon)
    except Exception as e:
        Logger.log(f"⚠️ Fout bij laden van plugin uit {path}: {e}")
        return None

def install_zip_plugin(zip_path, output_dir=PLUGIN_DIR):
    try:
        Logger.log(f"📦 Plugin wordt geïnstalleerd vanuit: {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(output_dir)
        Logger.log(f"✅ Plugin geïnstalleerd vanuit {zip_path}")
    except Exception as e:
        Logger.log(f"❌ Fout bij installeren van plugin: {e}")

class HauswerkCore(QMainWindow):
    def __init__(self):
        super().__init__()
        Logger.log("🧱 Initialiseren van HauswerkCore GUI")
        self.setWindowTitle("Hauswerk Core")
        self.resize(1024, 720)

        show_splash(theme=SettingsManager.instance().get("theme", "light"), parent_window=None)

        menubar = QMenuBar(self)
        file_menu = QMenu("Bestand", self)
        help_menu = QMenu("Help", self)

        install_action = QAction("Plugin installeren...", self)
        install_action.triggered.connect(self.select_zip_plugin)
        exit_action = QAction("Afsluiten", self)
        exit_action.triggered.connect(self.close)
        about_action = QAction("Over Hauswerk", self)
        about_action.triggered.connect(self.show_about)

        file_menu.addAction(install_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        help_menu.addAction(about_action)
        menubar.addMenu(file_menu)
        menubar.addMenu(help_menu)
        self.setMenuBar(menubar)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.setCentralWidget(self.tabs)


        self.dashboard = DashboardTab()
        quick_btn = QPushButton("🔁 Herlaad plugins")
        quick_btn.clicked.connect(self.reload_plugins)
        self.dashboard.layout().addWidget(quick_btn)
        info_label = QLabel("ℹ️ Hauswerk is een modulaire desktopomgeving voor audiovisuele creatie.\nVerken de tabs om video- en mediaplugins te installeren, combineren of zelf te ontwikkelen.\nPlugins kunnen dynamisch geladen, herladen en beheerd worden vanuit één centrale interface.")
        info_label.setWordWrap(True)
        self.dashboard.layout().addWidget(info_label)

        self.tabs.addTab(self.dashboard, QIcon(), "🏠 Dashboard")
        self.tabs.addTab(PluginStoreGridWidget(), QIcon(), "🛍️ Store")
        self.tabs.addTab(PluginUploadTab(), QIcon(), "Upload")
        self.tabs.addTab(LogTab(), QIcon(), "📜 Log")
        if SettingsManager.instance().get("experimental_features"):
            self.tabs.addTab(ExperimentalTab(), QIcon(LAB_ICON_PATH), "Lab")
            self.tabs.addTab(PluginGeneratorWidget(), QIcon(), "Generator")

        # 🔢 Bepaal hoeveel vaste tabs er initieel zijn
        self.initial_tab_count = self.tabs.count()

        self.reload_plugins()

    def reload_plugins(self):
        Logger.log("♻️ Plugins worden opnieuw geladen")
        # Verwijder alleen dynamisch toegevoegde plugintabs
        while self.tabs.count() > self.initial_tab_count:
            self.tabs.removeTab(self.initial_tab_count)

        if not os.path.exists(PLUGIN_DIR):
            Logger.log(f"📁 Pluginmap ontbreekt, aanmaken: {PLUGIN_DIR}")
            os.makedirs(PLUGIN_DIR)

        plugin_count = 0
        for name in os.listdir(PLUGIN_DIR):
            path = os.path.join(PLUGIN_DIR, name)
            if os.path.isdir(path):
                result = load_plugin(path)
                if result:
                    name, widget, icon = result
                    self.tabs.addTab(widget, icon, name)
                    plugin_count += 1
        Logger.log(f"🔢 Totaal aantal plugins geladen: {plugin_count}")

    def select_zip_plugin(self):
        Logger.log("📂 Open dialoog voor ZIP-installatie")
        zip_path, _ = QFileDialog.getOpenFileName(self, "Kies plugin-zip", "", "ZIP-bestanden (*.zip)")
        if zip_path:
            install_zip_plugin(zip_path)
            self.reload_plugins()

    def show_about(self):
        Logger.log("ℹ️ Over-venster geopend")
        QMessageBox.information(self, "Over Hauswerk", "Hauswerk Core\nModulaire plugin engine voor creatieve tools.\n© M. Ligtenberg 2025")

    def show_tab_context_menu(self, pos: QPoint):
        index = self.tabs.tabBar().tabAt(pos)
        if index < self.initial_tab_count:
            return
        plugin_name = self.tabs.tabText(index)
        menu = QMenu()
        delete_action = QAction(f"🗑️ Verwijder plugin '{plugin_name}'", self)
        delete_action.triggered.connect(lambda: self.remove_plugin(plugin_name))
        menu.addAction(delete_action)
        menu.exec(self.tabs.mapToGlobal(pos))

    def remove_plugin(self, name):
        plugin_path = os.path.join(PLUGIN_DIR, name)
        Logger.log(f"🚮 Verzoek tot verwijderen van plugin: {name}")
        if not os.path.exists(plugin_path):
            QMessageBox.warning(self, "Niet gevonden", f"Pluginmap '{plugin_path}' niet gevonden.")
            return
        confirm = QMessageBox.question(
            self, "Bevestig verwijdering", f"Weet je zeker dat je plugin '{name}' wilt verwijderen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                shutil.rmtree(plugin_path)
                self.reload_plugins()
                Logger.log(f"🗑️ Plugin '{name}' is verwijderd.")
            except Exception as e:
                Logger.log(f"❌ Fout bij verwijderen van plugin '{name}': {e}")
                QMessageBox.critical(self, "Fout", f"Kon pluginmap niet verwijderen:\n{e}")

if __name__ == "__main__":
    Logger.log("🚀 Start Hauswerk applicatie")
    app = QApplication([])
    s = SettingsManager.instance()
    StyleManager.apply_theme(app, s.get("theme", "light"), s.get("font_size", 12), s.get("accent_color", "#44cc88"))
    window = HauswerkCore()
    window.show()
    app.exec()
