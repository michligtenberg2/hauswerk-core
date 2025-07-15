from PyQt6.QtWidgets import QPushButton, QMessageBox
from plugin_template_fallback import generate_fallback_main_py
from pathlib import Path
import json

def create_test_plugin_button():
    btn = QPushButton("🧪 Testplugin maken")
    btn.setToolTip("Genereer een testplugin in de official/ map")

    def generate_test_plugin():
        slug = "testplugin"
        class_name = "TestPlugin"
        plugin_dir = Path("official") / slug
        plugin_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "name": slug,
            "version": "1.0",
            "description": "Testplugin gegenereerd vanuit GUI",
            "author": "Hauswerk System",
            "tags": ["test"],
            "verified": False,
            "rating": 0,
            "compatibility": ["Hauswerk >=1.0"],
            "changelog": "Initiële testplugin",
            "preview": "preview.jpg",
            "entry": "main.py",
            "class": class_name
        }

        (plugin_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        (plugin_dir / "main.py").write_text(generate_fallback_main_py(class_name, "Testplugin voorbeeld"))
        (plugin_dir / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (plugin_dir / "preview.jpg").write_bytes(b"\x89PNG\r\n\x1a\n")

        QMessageBox.information(btn, "✅ Testplugin", "De testplugin is gegenereerd in 'official/testplugin/'.")

    btn.clicked.connect(generate_test_plugin)
    return btn
