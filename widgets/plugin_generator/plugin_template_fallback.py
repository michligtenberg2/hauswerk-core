def generate_fallback_main_py(class_name: str, prompt: str) -> str:
    return f"""from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

class {class_name}(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("🔧 Plugin gegenereerd zonder AI\\n\\nPrompt: {prompt}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
"""
