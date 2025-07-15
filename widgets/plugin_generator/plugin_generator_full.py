from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QHBoxLayout, QComboBox, QFrame, QProgressBar, QFileDialog, QDialog, QTextEdit, QDialogButtonBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from pathlib import Path
import json
from .plugin_generator_metadata import MetadataFields
from .plugin_generator_helpers import (
    generate_slug, write_metadata_file, write_plugin_files,
    export_plugin_as_zip, show_error_dialog
)
from .plugin_generator_llm import run_model_prompt
from core.settings import SettingsManager

class PluginGeneratorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Plugin Generator")
        layout = QVBoxLayout(self)

        # Template keuze + prompt
        self.template_choice = QComboBox()
        self.template_choice.addItems(["Leeg widget", "Formulier", "Beeldgenerator", "Effectpaneel"])
        layout.addWidget(QLabel("📦 Plugin template:"))
        layout.addWidget(self.template_choice)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Wat moet deze plugin doen?")
        layout.addWidget(QLabel("🧠 Beschrijf je plugin:"))
        layout.addWidget(self.prompt_input)

        self.model_choice = QComboBox()
        self.model_choice.addItems(["phi", "mistral", "gemma:2b"])
        layout.addWidget(QLabel("🧠 Kies AI-model:"))
        layout.addWidget(self.model_choice)

        # Metadata velden
        self.metadata_fields = MetadataFields()
        layout.addWidget(self.metadata_fields)

        self.name_display = QLineEdit()
        self.name_display.setReadOnly(True)
        layout.addWidget(QLabel("💛 Pluginnaam (slug):"))
        layout.addWidget(self.name_display)

        # Buttons
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

        self.preview_label = QLabel("🔍 Preview verschijnt hier na genereren")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFrameStyle(QFrame.Shape.StyledPanel.value)
        layout.addWidget(self.preview_label)

        self.setLayout(layout)
        self.generated_code = ""
        self.current_plugin_dir = None

        # Laad defaults uit instellingen
        settings = SettingsManager.instance()
        self.model_choice.setCurrentText(settings.get("ai_model", "phi"))
        self.template_choice.setCurrentText(settings.get("default_template", "Leeg widget"))

    def generate_plugin(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            show_error_dialog(self, "Geef een beschrijving op.")
            return

        template = self.template_choice.currentText()
        full_prompt = f"Template: {template}. {prompt}"
        slug = generate_slug(prompt)
        classname = slug.capitalize() + "Plugin"
        self.name_display.setText(slug)

        plugin_dir = Path(SettingsManager.instance().get("output_dir") or "official") / slug
        plugin_dir.mkdir(parents=True, exist_ok=True)

        metadata = self.metadata_fields.get_metadata()
        write_metadata_file(plugin_dir, slug, classname, metadata, print)

        try:
            model = self.model_choice.currentText().split()[0]
            code = run_model_prompt(full_prompt, classname, model, print)
        except Exception as e:
            show_error_dialog(self, f"Fout bij genereren: {e}")
            return

        write_plugin_files(plugin_dir, code, print)

        # Preview tonen
        preview_path = plugin_dir / "preview.png"
        if preview_path.exists():
            pixmap = QPixmap(str(preview_path)).scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setText("")
        else:
            self.preview_label.setText("❌ Geen preview gevonden.")

        self.generated_code = code
        self.current_plugin_dir = plugin_dir
        self.view_code_btn.setEnabled(True)
        self.zip_btn.setEnabled(True)

    def show_code_editor(self):
        if not self.generated_code:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Preview Code")
        dlg.resize(700, 500)
        layout = QVBoxLayout(dlg)
        code_edit = QTextEdit()
        code_edit.setPlainText(self.generated_code)
        code_edit.setReadOnly(True)
        layout.addWidget(code_edit)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        dlg.exec()

    def export_as_zip(self):
        if self.current_plugin_dir:
            export_plugin_as_zip(self.current_plugin_dir, print)
