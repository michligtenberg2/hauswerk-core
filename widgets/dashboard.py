from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap, QDesktopServices
from PyQt6.QtCore import Qt, QUrl
import os

class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 20)

        # Logo bovenaan
        logo_path = os.path.join(os.path.dirname(__file__), "../resources/logo.svg")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setPixmap(QPixmap(logo_path).scaledToHeight(80, Qt.TransformationMode.SmoothTransformation))
            layout.addWidget(logo_label)

        # Card
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet("background:rgba(255,255,255,0.08); border-radius:20px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 22, 32, 24)

        html = (
            "<div style='font-size:14pt; text-align:center;'>"
            "<b>Hauswerk</b><br><br>"
            "Jouw modulaire werkomgeving voor creatieve video- en mediaplugins.<br>"
            "Gebruik de zijtabs om tools te installeren, te combineren of zelf te ontwikkelen.<br><br>"
            "<span style='font-size:10pt;'>Versie 1.0 — Python + PyQt6</span><br>"
            "<a href='https://github.com/michligtenberg2/hauswerk'>🔗 GitHub projectpagina</a>"
            "</div>"
        )

        lbl = QLabel(html)
        lbl.setOpenExternalLinks(True)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setTextFormat(Qt.TextFormat.RichText)
        card_layout.addWidget(lbl)

        # Extra snelkoppelingen
        btn_pluginmap = QPushButton("📂 Open pluginmap")
        btn_pluginmap.clicked.connect(self.open_plugin_folder)
        card_layout.addWidget(btn_pluginmap)

        btn_settings = QPushButton("⚙️ Instellingen")
        btn_settings.clicked.connect(self.open_settings_dialog)
        card_layout.addWidget(btn_settings)

        btn_changelog = QPushButton("📝 Bekijk changelog")
        btn_changelog.clicked.connect(self.open_changelog)
        card_layout.addWidget(btn_changelog)

        # Footer
        info_footer = QLabel("<div style='font-size:9pt; text-align:center; color:gray;'>"
                             "Laatste update: 15 juli 2025<br>"
                             "Gemaakt door <b>M. Ligtenberg</b> — met ❤️ in PyQt6"
                             "</div>")
        info_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_footer.setTextFormat(Qt.TextFormat.RichText)
        card_layout.addWidget(info_footer)

        card_layout.addStretch()
        layout.addWidget(card, stretch=1)
        layout.addStretch()

    def open_plugin_folder(self):
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../plugins"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def open_changelog(self):
        changelog_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../CHANGELOG.md"))
        if os.path.exists(changelog_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(changelog_path))
        else:
            QMessageBox.information(self, "Changelog niet gevonden", "Het changelog-bestand kon niet worden gevonden.")

    def open_settings_dialog(self):
        from core.settings import SettingsDialog
        dlg = SettingsDialog(self)
        dlg.exec()
