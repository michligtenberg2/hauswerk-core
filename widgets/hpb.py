from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QFileDialog, QMessageBox, QComboBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os
import zipfile
import json
import requests
from pathlib import Path
import tempfile
import shutil

SUPABASE_URL = "https://izlcnpelomuuwxijnnuh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml6bGNucGVsb211dXd4aWpubnVoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1ODQ0NjEsImV4cCI6MjA2ODE2MDQ2MX0.ogKWbIDvRlq5BDyyVX9WNWdHYPYuSFm1dugP8_0u7fE"
BUCKET = "hauswerk.unofficial"
DEFAULT_ICON = Path(__file__).parent / "default_icon.png"

class PluginUploadTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔼 Upload Plugin")
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Plugin naam (slug)")
        layout.addWidget(QLabel("📛 Naam van de plugin:"))
        layout.addWidget(self.name_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Korte beschrijving...")
        layout.addWidget(QLabel("📝 Beschrijving:"))
        layout.addWidget(self.desc_input)

        self.tags = QComboBox()
        self.tags.addItems(["audio", "video", "tools", "fx", "misc"])
        layout.addWidget(QLabel("🏷️ Categorie:"))
        layout.addWidget(self.tags)

        self.zip_btn = QPushButton("📦 Kies plugin ZIP")
        self.zip_btn.clicked.connect(self.pick_zip)
        layout.addWidget(self.zip_btn)

        self.code_btn = QPushButton("📄 Of kies los .py bestand")
        self.code_btn.clicked.connect(self.pick_py)
        layout.addWidget(self.code_btn)

        self.preview_btn = QPushButton("🖼️ Kies preview.jpg")
        self.preview_btn.clicked.connect(self.pick_preview)
        layout.addWidget(self.preview_btn)

        self.preview_image = QLabel("Geen preview gekozen")
        self.preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image.setFixedHeight(120)
        layout.addWidget(self.preview_image)

        self.status = QTextEdit()
        self.status.setReadOnly(True)
        self.status.setFixedHeight(120)
        layout.addWidget(QLabel("📄 Status / Log:"))
        layout.addWidget(self.status)

        self.upload_btn = QPushButton("🚀 Upload alles naar Plugin Store")
        self.upload_btn.clicked.connect(self.upload_plugin)
        layout.addWidget(self.upload_btn)

        self.setLayout(layout)
        self.selected_zip = None
        self.selected_preview = None
        self.selected_py = None
        self.existing_slugs = self.fetch_existing_slugs()

    def log(self, msg):
        self.status.append(msg)

    def pick_zip(self):
        self.selected_py = None
        path, _ = QFileDialog.getOpenFileName(self, "Kies plugin ZIP", "", "ZIP bestanden (*.zip)")
        if path:
            self.selected_zip = path
            self.log(f"📦 Gekozen bestand: {path}")
            errors = self.validate_plugin_zip(path)
            if errors:
                for e in errors:
                    self.log(e)
                QMessageBox.warning(self, "Fout in ZIP", "Plugin ZIP is niet geldig.")
                self.selected_zip = None
            else:
                self.log("✅ ZIP gevalideerd")

    def pick_py(self):
        self.selected_zip = None
        path, _ = QFileDialog.getOpenFileName(self, "Kies .py bestand", "", "Python (*.py)")
        if path:
            self.selected_py = Path(path)
            self.name_input.setText(self.selected_py.stem)
            self.log(f"📄 Gekozen Python bestand: {path}")

    def pick_preview(self):
        path, _ = QFileDialog.getOpenFileName(self, "Kies preview.jpg", "", "Afbeelding (*.jpg *.jpeg *.png *.gif)")
        if path:
            self.selected_preview = path
            self.log(f"🖼️ Preview gekozen: {path}")
            pixmap = QPixmap(path)
            self.preview_image.setPixmap(pixmap.scaledToHeight(120, Qt.TransformationMode.SmoothTransformation))

    def fetch_existing_slugs(self):
        index_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/unofficial_plugins.json"
        try:
            r = requests.get(index_url)
            return [p.get("name", "").lower().replace(" ", "-") for p in r.json()] if r.ok else []
        except Exception as e:
            self.log(f"⚠️ Kon index niet ophalen: {e}")
            return []

    def validate_plugin_zip(self, zip_path):
        errors = []
        with zipfile.ZipFile(zip_path, 'r') as z:
            files = z.namelist()
            if not any(f.endswith(".py") for f in files):
                errors.append("❌ .py bestand ontbreekt")
            if not any("metadata.json" in f for f in files):
                errors.append("❌ metadata.json ontbreekt")
            try:
                meta_file = [f for f in files if f.endswith("metadata.json")][0]
                with z.open(meta_file) as f:
                    meta = json.load(f)
                    if "entry" not in meta or "class" not in meta:
                        errors.append("⚠️ metadata mist 'entry' of 'class'")
            except Exception as e:
                errors.append(f"❌ metadata.json fout: {e}")
        return errors

    def upload_plugin(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        tag = self.tags.currentText()

        if not name or not desc:
            QMessageBox.warning(self, "Invoer ontbreekt", "Naam en beschrijving zijn verplicht.")
            return

        slug = name.lower().replace(" ", "-")
        if slug in self.existing_slugs:
            QMessageBox.warning(self, "Bestaat al", f"De plugin '{slug}' bestaat al in de index.")
            return

        if self.selected_py:
            self.selected_zip = self.build_zip_from_py(slug, name)

        if not self.selected_zip:
            QMessageBox.warning(self, "Geen ZIP", "Kies of genereer een ZIP.")
            return

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }

        filename = f"{slug}.zip"
        with open(self.selected_zip, "rb") as f:
            res = requests.put(
                f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filename}",
                headers=headers,
                data=f,
            )
            if res.ok:
                self.log(f"✅ ZIP geüpload als {filename}")
            else:
                self.log(f"❌ Fout bij uploaden: {res.text}")
                return

        if self.selected_preview:
            with open(self.selected_preview, "rb") as f:
                res = requests.put(
                    f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{slug}/preview.jpg",
                    headers=headers,
                    data=f,
                )
                if res.ok:
                    self.log("🖼️ Preview geüpload")
                else:
                    self.log(f"⚠️ Kon preview niet uploaden: {res.text}")

        # Update index
        index_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/unofficial_plugins.json"
        try:
            r = requests.get(index_url)
            plugins = r.json() if r.ok else []
        except:
            plugins = []

        plugins = [p for p in plugins if p.get("name") != slug]
        plugins.append({
            "name": name,
            "description": desc,
            "zip_url": f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}",
            "preview_url": f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{slug}/preview.jpg",
            "tags": [tag]
        })

        put_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/unofficial_plugins.json"
        res = requests.put(
            put_url,
            headers={**headers, "Content-Type": "application/json"},
            data=json.dumps(plugins, indent=2)
        )
        if res.ok:
            self.log("✅ Index geüpdatet")
            QMessageBox.information(self, "Upload gelukt", "Plugin en index succesvol geüpload.")
        else:
            self.log(f"❌ Kon index niet bijwerken: {res.text}")

    def build_zip_from_py(self, slug, name):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / slug
            folder.mkdir()
            shutil.copy(self.selected_py, folder / self.selected_py.name)

            metadata = {
                "name": slug,
                "version": "1.0",
                "description": self.desc_input.toPlainText().strip(),
                "entry": self.selected_py.name,
                "class": slug.capitalize() + "Plugin"
            }
            with open(folder / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            if self.selected_preview:
                shutil.copy(self.selected_preview, folder / "preview.jpg")
            else:
                shutil.copy(DEFAULT_ICON, folder / "preview.jpg")

            shutil.copy(DEFAULT_ICON, folder / "icon.png")

            zip_path = Path(tmpdir) / f"{slug}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                for f in folder.iterdir():
                    z.write(f, f.name)

            final_path = Path(tempfile.gettempdir()) / f"{slug}.zip"
            shutil.copy(zip_path, final_path)
            return final_path
