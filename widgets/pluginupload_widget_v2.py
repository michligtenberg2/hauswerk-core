import os
import zipfile
import json
import requests
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QFileDialog, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt

SUPABASE_URL = "https://izlcnpelomuuwxijnnuh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml6bGNucGVsb211dXd4aWpubnVoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1ODQ0NjEsImV4cCI6MjA2ODE2MDQ2MX0.ogKWbIDvRlq5BDyyVX9WNWdHYPYuSFm1dugP8_0u7fE"
BUCKET = "plugins-unofficial"

def validate_plugin_zip(zip_path):
    errors = []
    with zipfile.ZipFile(zip_path, 'r') as z:
        files = z.namelist()
        if not any("main.py" in f for f in files):
            errors.append("❌ main.py ontbreekt")
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

class PluginUploadWidget(QWidget):
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

        self.preview_btn = QPushButton("🖼️ Kies preview.jpg")
        self.preview_btn.clicked.connect(self.pick_preview)
        layout.addWidget(self.preview_btn)

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

    def log(self, msg):
        self.status.append(msg)

    def pick_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "Kies plugin ZIP", "", "ZIP bestanden (*.zip)")
        if path:
            self.selected_zip = path
            self.log(f"📦 Gekozen bestand: {path}")
            errors = validate_plugin_zip(path)
            if errors:
                for e in errors:
                    self.log(e)
                QMessageBox.warning(self, "Fout in ZIP", "Plugin ZIP is niet geldig.")
                self.selected_zip = None
            else:
                self.log("✅ ZIP gevalideerd")

    def pick_preview(self):
        path, _ = QFileDialog.getOpenFileName(self, "Kies preview.jpg", "", "Afbeelding (*.jpg *.jpeg)")
        if path:
            self.selected_preview = path
            self.log(f"🖼️ Preview gekozen: {path}")

    def upload_plugin(self):
        if not self.selected_zip:
            QMessageBox.warning(self, "Geen ZIP", "Kies een gevalideerde ZIP.")
            return

        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        tag = self.tags.currentText()

        if not name or not desc:
            QMessageBox.warning(self, "Invoer ontbreekt", "Naam en beschrijving zijn verplicht.")
            return

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }

        slug = name.lower().replace(" ", "-")
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

        # Load + update index json in Supabase
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
