from PyQt6.QtWidgets import QMessageBox
from pathlib import Path
import json
import os
import zipfile
import re
from core.utils import slugify

def generate_slug(text):
    """Backward compatible wrapper around :func:`slugify`."""
    return slugify(text)

def write_metadata_file(plugin_dir: Path, slug: str, classname: str, metadata: dict, log_func):
    metadata.update({
        "name": slug,
        "entry": "main.py",
        "preview": "preview.png",
        "class": classname
    })
    try:
        (plugin_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        log_func(f"📁 metadata.json opgeslagen in {plugin_dir}")
    except Exception as e:
        log_func(f"❌ Kon metadata.json niet opslaan: {e}")

def write_plugin_files(plugin_dir: Path, code: str, log_func):
    try:
        (plugin_dir / "main.py").write_text(code)
        (plugin_dir / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (plugin_dir / "preview.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        log_func("✅ Bestandenset gegenereerd.")
    except Exception as e:
        log_func(f"❌ Fout bij wegschrijven van bestanden: {e}")

def export_plugin_as_zip(plugin_dir: Path, log_func):
    try:
        zip_path = plugin_dir.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(plugin_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, plugin_dir.parent)
                    zipf.write(filepath, arcname)
        log_func(f"📦 ZIP-bestand opgeslagen: {zip_path}")
    except Exception as e:
        log_func(f"❌ ZIP export mislukt: {e}")

def show_error_dialog(parent, message):
    QMessageBox.critical(parent, "Fout", message)

def confirm_warning(parent, message):
    return QMessageBox.warning(parent, "Let op", message, QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
