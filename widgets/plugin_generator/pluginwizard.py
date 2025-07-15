from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QMessageBox, QHBoxLayout, QComboBox, QFrame, QProgressBar, QInputDialog, QFileDialog
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

from core.settings import SettingsManager
from .plugin_template_fallback import generate_fallback_main_py
from .ollama_integration import is_ollama_installed, run_ollama_prompt

PLUGIN_OUTPUT_DIR = Path(SettingsManager.instance().get("output_dir", "official"))

class ModelDownloader(QThread):
    progress = pyqtSignal(str)
    done = pyqtSignal(bool)

    def __init__(self, model):
        super().__init__()
        self.model = model

    def run(self):
        print(f"[DEBUG] Start download van model: {self.model}")
        try:
            proc = subprocess.Popen(
                ["ollama", "pull", self.model],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            while proc.poll() is None:
                line = proc.stdout.readline()
                if line:
                    print(f"[OLLAMA DL] {line.strip()}")
                    self.progress.emit(line.strip())
            self.done.emit(proc.returncode == 0)
        except Exception as e:
            print(f"[ERROR] Download exception: {e}")
            self.progress.emit(f"❌ Fout: {e}")
            self.done.emit(False)

class ModelTestRunner(QThread):
    progress = pyqtSignal(str)
    def __init__(self, model, prompt):
        super().__init__()
        self.model = model
        self.prompt = prompt

    def run(self):
        self.progress.emit(f"🧪 Test het model '{self.model}' met prompt: {self.prompt!r}")
        print(f"[DEBUG] Start modeltest voor: {self.model} met prompt: {self.prompt}")
        try:
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=self.prompt,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                print("[MODEL OUTPUT]", output)
                self.progress.emit("🧠 Reactie:\n" + output[:1000])
            else:
                print("[MODEL ERROR]", result.stderr.strip())
                self.progress.emit(f"⚠️ Fout tijdens test: {result.stderr.strip()}")
        except Exception as e:
            print(f"[ERROR] Modeltest exception: {e}")
            self.progress.emit(f"❌ Exception bij modeltest: {e}")

class PluginGeneratorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Plugin Generator")

        layout = QVBoxLayout(self)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Wat moet deze plugin doen?")
        layout.addWidget(QLabel("🧠 Beschrijf je plugin:"))
        layout.addWidget(self.prompt_input)

        self.model_choice = QComboBox()
        self.model_choice.addItems(["gemma:2b (licht)", "phi", "mistral"])
        self.model_choice.setToolTip("Kies welk lokaal AI-model je wilt gebruiken voor de generatie")
        layout.addWidget(QLabel("🧠 Kies AI-model (lokaal via Ollama):"))
        layout.addWidget(self.model_choice)

        self.name_display = QLineEdit()
        self.name_display.setReadOnly(True)
        layout.addWidget(QLabel("💛 Pluginnaam (slug):"))
        layout.addWidget(self.name_display)

        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton("🚀 Genereer Plugin")
        self.generate_btn.clicked.connect(self.generate_plugin)
        btn_row.addWidget(self.generate_btn)

        self.install_ollama_btn = QPushButton("⬇️ Installeer Ollama")
        self.install_ollama_btn.clicked.connect(self.install_ollama)
        btn_row.addWidget(self.install_ollama_btn)

        self.open_folder_btn = QPushButton("📂 Open pluginmap")
        self.open_folder_btn.clicked.connect(self._open_plugin_folder)
        btn_row.addWidget(self.open_folder_btn)

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
            self.install_ollama_btn.setVisible(False)
            self.log("✅ Ollama gevonden op dit systeem.")
        else:
            self.install_ollama_btn.setVisible(True)
            self.log("⚠️ Ollama niet gevonden. Je kunt fallback gebruiken of installeren.")

    def install_ollama(self):
        model, ok = QInputDialog.getItem(
            self, "Model kiezen", "Welk model wil je installeren?",
            ["phi", "mistral", "llama2"], 0, False
        )
        if not ok or not model:
            return
        self.log(f"📦 Gekozen model: {model}")
        self._download_model(model)

    def _download_model(self, model):
        self.progressbar.show()
        self.downloader = ModelDownloader(model)
        self.downloader.progress.connect(self.log)
        self.downloader.done.connect(self._on_download_done)
        self.log(f"⬇️ Start download van model: {model}")
        self.downloader.start()

    def _on_download_done(self, success):
        self.progressbar.hide()
        if success:
            self.log("✅ Model gedownload en klaar voor gebruik!")
            self._test_model(self.downloader.model)
        else:
            self.log("❌ Download mislukt.")

    def _test_model(self, model):
        prompt, ok = QInputDialog.getText(
            self, "Test het model", "Voer een testprompt in:", text="Zeg hallo"
        )
        if not ok or not prompt.strip():
            self.log("⏩ Test prompt overgeslagen.")
            return
        self.testrunner = ModelTestRunner(model, prompt)
        self.testrunner.progress.connect(self.log)
        self.testrunner.start()

    def generate_plugin(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Fout", "Geef een beschrijving op.")
            return

        slug = self._generate_slug(prompt)
        if not slug:
            QMessageBox.warning(self, "Fout", "Slug kon niet worden gegenereerd.")
            return
        classname = slug.capitalize() + "Plugin"
        self.name_display.setText(slug)

        plugin_dir = PLUGIN_OUTPUT_DIR / slug
        plugin_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "name": slug,
            "version": "1.0",
            "description": prompt,
            "author": "Onbekend",
            "tags": [],
            "verified": False,
            "rating": 0,
            "compatibility": ["Hauswerk >=1.0"],
            "changelog": "Gegenereerd via Plugin Wizard",
            "preview": "preview.png",
            "entry": "main.py",
            "class": classname
        }

        (plugin_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        self.log(f"📁 metadata.json opgeslagen in {plugin_dir}")

        try:
            if is_ollama_installed():
                model = self.model_choice.currentText().split()[0]
                code = run_ollama_prompt(model, f"Schrijf een PyQt6 QWidget class genaamd '{classname}' die dit doet: {prompt}")
                self.log(f"🧠 gegenereerd via Ollama model: {model}")
                self.log("--- Preview Code ---\n" + code[:300])
            else:
                code = generate_fallback_main_py(classname, prompt)
                self.log("⚠️ Ollama niet beschikbaar — fallback gebruikt")
        except Exception as e:
            self.log(f"❌ Fout bij genereren: {e}")
            QMessageBox.critical(self, "AI-fout", str(e))
            return

        (plugin_dir / "main.py").write_text(code)
        (plugin_dir / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (plugin_dir / "preview.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        self.log("✅ Bestandenset gegenereerd.")

        preview_path = plugin_dir / "preview.png"
        if preview_path.exists():
            pixmap = QPixmap(str(preview_path)).scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setText("")
        else:
            self.preview_label.setText("❌ Geen preview gevonden.")

    def _generate_slug(self, text):
        base = "".join(c for c in text.lower() if c.isalnum() or c in " -_")
        base = re.sub(r'[^a-z0-9_-]', '', base.strip())
        return "-".join(base.split())[:20]

    def _open_plugin_folder(self):
        QFileDialog.getOpenFileName(self, "Bekijk pluginmap", str(PLUGIN_OUTPUT_DIR), "")
