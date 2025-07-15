import os
import json
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QSpinBox,
    QPushButton, QDialogButtonBox, QFileDialog, QApplication
)

class SettingsManager(QObject):
    settingsChanged = pyqtSignal()
    SETTINGS_FILE = os.path.expanduser("~/.megatool_settings.json")
    _instance = None

    def __init__(self):
        super().__init__()
        self._settings = {
            "output_dir": "",
            "theme": "light",
            "max_layers": 6,
            "presets_dir": os.path.expanduser("~/.megatool_presets"),
            "font_size": 12
        }
        self.load()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = SettingsManager()
        return cls._instance

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self.save()
        self.settingsChanged.emit()

    def as_dict(self):
        return dict(self._settings)

    def load(self):
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r") as f:
                    self._settings.update(json.load(f))
            except Exception:
                pass

    def save(self):
        with open(self.SETTINGS_FILE, "w") as f:
            json.dump(self._settings, f, indent=2)

    @staticmethod
    def styles_dir():
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(here, '..', 'resources', 'themes'))

    @staticmethod
    def available_styles():
        theme_dir = SettingsManager.styles_dir()
        if not os.path.exists(theme_dir):
            return []
        return [f[:-4] for f in os.listdir(theme_dir) if f.endswith('.qss')]

    def get_presets_dir(self):
        return self._settings.get("presets_dir", os.path.expanduser("~/.megatool_presets"))

    def ensure_presets_dir(self):
        path = self.get_presets_dir()
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Instellingen")
        self.resize(400, 250)
        layout = QVBoxLayout(self)

        # Output map
        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(QLabel("Standaard outputmap:"))
        self.outdir_edit = QLineEdit()
        hlayout1.addWidget(self.outdir_edit)
        browse_btn = QPushButton("Bladeren…")
        browse_btn.clicked.connect(self._browse_folder)
        hlayout1.addWidget(browse_btn)
        layout.addLayout(hlayout1)

        # Thema dropdown
        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(QLabel("Thema:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(SettingsManager.available_styles())
        hlayout2.addWidget(self.theme_combo)
        layout.addLayout(hlayout2)

        # Fontgrootte dropdown
        hlayout2b = QHBoxLayout()
        hlayout2b.addWidget(QLabel("Fontgrootte:"))
        self.fontsize_spin = QSpinBox()
        self.fontsize_spin.setRange(8, 22)
        hlayout2b.addWidget(self.fontsize_spin)
        layout.addLayout(hlayout2b)

        # Max collage-lagen
        hlayout3 = QHBoxLayout()
        hlayout3.addWidget(QLabel("Max. collage-lagen:"))
        self.max_layers_spin = QSpinBox()
        self.max_layers_spin.setRange(1, 20)
        hlayout3.addWidget(self.max_layers_spin)
        layout.addLayout(hlayout3)

        # Presets map
        hlayout4 = QHBoxLayout()
        hlayout4.addWidget(QLabel("Presets-map:"))
        self.presets_dir_edit = QLineEdit()
        browse_btn2 = QPushButton("Bladeren…")
        browse_btn2.clicked.connect(self._browse_presets_folder)
        hlayout4.addWidget(self.presets_dir_edit)
        hlayout4.addWidget(browse_btn2)
        layout.addLayout(hlayout4)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.settings = SettingsManager.instance()
        self._load_settings()

        # Live preview op wissel thema of fontgrootte
        self.theme_combo.currentTextChanged.connect(self._preview_theme)
        self.fontsize_spin.valueChanged.connect(self._preview_theme)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Kies outputmap")
        if folder:
            self.outdir_edit.setText(folder)

    def _browse_presets_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Kies presets-map")
        if folder:
            self.presets_dir_edit.setText(folder)

    def _load_settings(self):
        s = self.settings.as_dict()
        self.outdir_edit.setText(s.get("output_dir", ""))
        style_list = SettingsManager.available_styles()
        theme = s.get("theme", "light").lower()
        if theme in style_list:
            self.theme_combo.setCurrentText(theme)
        else:
            self.theme_combo.setCurrentIndex(0)
        self.fontsize_spin.setValue(int(s.get("font_size", 12)))
        self.max_layers_spin.setValue(int(s.get("max_layers", 6)))
        self.presets_dir_edit.setText(s.get("presets_dir", os.path.expanduser("~/.megatool_presets")))

    def _preview_theme(self):
        theme = self.theme_combo.currentText()
        font_size = self.fontsize_spin.value()
        app = QApplication.instance()
        from core.style import StyleManager
        StyleManager.apply_theme(app, theme, font_size)

    def accept(self):
        self.settings.set("output_dir", self.outdir_edit.text())
        self.settings.set("theme", self.theme_combo.currentText())
        self.settings.set("max_layers", self.max_layers_spin.value())
        self.settings.set("presets_dir", self.presets_dir_edit.text())
        self.settings.set("font_size", self.fontsize_spin.value())
        super().accept()
