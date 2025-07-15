from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

class ExperimentalTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🧪 Welkom in het experimentele Lab!"))

        btn = QPushButton("Voer geheime test uit")
        layout.addWidget(btn)

        self.setLayout(layout)
