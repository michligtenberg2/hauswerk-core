from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QMessageBox, QHBoxLayout, QComboBox, QFrame, QProgressBar, QInputDialog, QFileDialog,
    QDialog, QDialogButtonBox, QCheckBox, QGroupBox, QFormLayout
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
import json
import platform
import shutil
import subprocess
import os
import re
import zipfile

from core.settings import SettingsManager
from .plugin_template_fallback import generate_fallback_main_py
from .ollama_integration import is_ollama_installed, run_ollama_prompt
from core.utils import slugify

class MetadataFields(QGroupBox):
    def __init__(self):
        super().__init__("Geavanceerde Metadata")
        self.layout = QFormLayout(self)

        self.author_edit = QLineEdit()
        self.version_edit = QLineEdit("1.0")
        self.tags_edit = QLineEdit()
        self.compat_edit = QLineEdit("Hauswerk >=1.0")
        self.changelog_edit = QTextEdit("Gegenereerd via Plugin Wizard")
        self.changelog_edit.setFixedHeight(60)

        self.layout.addRow("Auteur:", self.author_edit)
        self.layout.addRow("Versie:", self.version_edit)
        self.layout.addRow("Tags (komma's):", self.tags_edit)
        self.layout.addRow("Compatibiliteit:", self.compat_edit)
        self.layout.addRow("Changelog:", self.changelog_edit)

    def get_metadata(self):
        return {
            "author": self.author_edit.text() or "Onbekend",
            "version": self.version_edit.text() or "1.0",
            "tags": [t.strip() for t in self.tags_edit.text().split(",") if t.strip()],
            "compatibility": [self.compat_edit.text().strip()] if self.compat_edit.text().strip() else ["Hauswerk >=1.0"],
            "changelog": self.changelog_edit.toPlainText() or "Gegenereerd via Plugin Wizard"
        }

class PluginGeneratorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Plugin Generator")

        layout = QVBoxLayout(self)

        self.template_choice = QComboBox()
        self.template_choice.addItems(["Leeg widget", "Formulier", "Beeldgenerator", "Effectpaneel"])
        layout.addWidget(QLabel("📦 Plugin template:"))
        layout.addWidget(self.template_choice)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Wat moet deze plugin doen?")
        layout.addWidget(QLabel("🧠 Beschrijf je plugin:"))
        layout.addWidget(self.prompt_input)

        self.model_choice = QComboBox()
        self.model_choice.addItems(["gemma:2b (licht)", "phi", "mistral"])
        self.model_choice.setToolTip("Kies welk lokaal AI-model je wilt gebruiken voor de generatie")
        layout.addWidget(QLabel("🧠 Kies AI-model (lokaal via Ollama):"))
        layout.addWidget(self.model_choice)

        self.metadata_fields = MetadataFields()
        layout.addWidget(self.metadata_fields)

        self.name_display = QLineEdit()
        self.name_display.setReadOnly(True)
        layout.addWidget(QLabel("💛 Pluginnaam (slug):"))
        layout.addWidget(self.name_display)

        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton("🚀 Genereer Plugin")
        self.generate_btn.clicked.connect(self.generate_plugin)
        btn_row.addWidget(self.generate_btn)

        self.view_code_btn = QPushButton("👁️ Bekijk Code")
        self.view_code_btn.clicked.connect(self.show_code_editor)
        self.view_code_btn.setEnabled(False)
        btn_row.addWidget(self.view_code_btn)

        self.zip_btn = QPushButton("📦 Exporteer als ZIP")
        self.zip_btn.clicked.connect(self.export_as_zip)
        self.zip_btn.setEnabled(False)
        btn_row.addWidget(self.zip_btn)

        layout.addLayout(btn_row)

        self.progressbar = QProgressBar()
        self.progressbar.setRange(0, 0)
        self.progressbar.hide()
        layout.addWidget(self.progressbar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(100)
        layout.addWidget(QLabel("📄 Log:"))
        layout.addWidget(self.log_output)

        self.preview_label = QLabel("🔍 Preview verschijnt hier na genereren")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFrameStyle(QFrame.Shape.StyledPanel.value)
        layout.addWidget(self.preview_label)

        self.setLayout(layout)
        self.check_ollama()

    def log(self, msg):
        try:
            self.log_output.append(msg)
        except Exception:
            self.log_output.append("[FOUT] Kan logregel niet weergeven.")
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def check_ollama(self):
        if is_ollama_installed():
            self.log("✅ Ollama gevonden op dit systeem.")
        else:
            self.log("⚠️ Ollama niet gevonden. Je kunt fallback gebruiken of installeren.")

    def generate_plugin(self):
        prompt = self.prompt_input.toPlainText().strip()
        template = self.template_choice.currentText()
        if not prompt:
            QMessageBox.warning(self, "Fout", "Geef een beschrijving op.")
            return

        full_prompt = f"Template: {template}. {prompt}"
        slug = slugify(prompt)
        if not slug:
            QMessageBox.warning(self, "Fout", "Slug kon niet worden gegenereerd.")
            return
        classname = slug.capitalize() + "Plugin"
        self.name_display.setText(slug)

        plugin_dir = Path(SettingsManager.instance().get("output_dir", "official")) / slug
        plugin_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "name": slug,
            "entry": "main.py",
            "preview": "preview.png",
            "class": classname
        }
        metadata.update(self.metadata_fields.get_metadata())

        (plugin_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        self.log(f"📁 metadata.json opgeslagen in {plugin_dir}")

        try:
            if is_ollama_installed():
                model = self.model_choice.currentText().split()[0]
                code = run_ollama_prompt(model, f"Schrijf een PyQt6 QWidget class genaamd '{classname}' die dit doet: {full_prompt}")
                self.log(f"🧠 gegenereerd via Ollama model: {model}")
                self.log("--- Preview Code ---\n" + code[:300])
            else:
                code = generate_fallback_main_py(classname, full_prompt)
                self.log("⚠️ Ollama niet beschikbaar — fallback gebruikt")
        except Exception as e:
            self.log(f"❌ Fout bij genereren: {e}")
            QMessageBox.critical(self, "AI-fout", str(e))
            return

        (plugin_dir / "main.py").write_text(code)
        (plugin_dir / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (plugin_dir / "preview.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        self.log("✅ Bestandenset gegenereerd.")

        self.generated_code = code
        self.current_plugin_dir = plugin_dir
        self.view_code_btn.setEnabled(True)
        self.zip_btn.setEnabled(True)

        preview_path = plugin_dir / "preview.png"
        if preview_path.exists():
            pixmap = QPixmap(str(preview_path)).scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setText("")
        else:
            self.preview_label.setText("❌ Geen preview gevonden.")

    def export_as_zip(self):
        if not hasattr(self, "current_plugin_dir"):
            return
        zip_path = self.current_plugin_dir.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.current_plugin_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, self.current_plugin_dir.parent)
                    zipf.write(filepath, arcname)
        self.log(f"📦 ZIP-bestand opgeslagen: {zip_path}")

    def show_code_editor(self):
        if not hasattr(self, "generated_code"):
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Code Preview")
        dlg.resize(700, 500)
        layout = QVBoxLayout(dlg)
        textedit = QTextEdit()
        textedit.setPlainText(self.generated_code)
        textedit.setReadOnly(True)
        layout.addWidget(textedit)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        dlg.exec()

    def _generate_slug(self, text):
        """Deprecated helper kept for backward compatibility."""
        return slugify(text)
