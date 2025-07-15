from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer
from ollama_integration import is_ollama_installed

class OllamaStatusLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setFixedHeight(20)
        self.update_status()

        # Optional: refresh elke 10 sec
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(10000)

    def update_status(self):
        if is_ollama_installed():
            self.setText("🧠 Ollama: actief")
            self.setStyleSheet("color: green; padding: 2px;")
        else:
            self.setText("⚠️ Ollama: niet gevonden")
            self.setStyleSheet("color: red; padding: 2px;")
