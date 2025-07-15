from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from ollama_integration import is_ollama_installed

def get_ollama_status_badge() -> QLabel:
    if is_ollama_installed():
        label = QLabel("🧠 Ollama beschikbaar")
        label.setStyleSheet("color: green; font-weight: bold;")
    else:
        label = QLabel("⚠️ Ollama niet gevonden")
        label.setStyleSheet("color: red; font-weight: bold;")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label
