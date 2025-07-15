from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
from core.logger import Logger

class LogTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        title = QLabel("📜 Logoverzicht")
        title.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(title)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        clear_btn = QPushButton("🧹 Wissen")
        clear_btn.clicked.connect(self.clear)
        layout.addWidget(clear_btn)

        self.setLayout(layout)
        Logger.init(self.log_view)

    def clear(self):
        self.log_view.clear()
