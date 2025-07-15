from PyQt6.QtWidgets import QGroupBox, QFormLayout, QLineEdit, QTextEdit

class MetadataFields(QGroupBox):
    def __init__(self):
        super().__init__("Geavanceerde Metadata")
        self.layout = QFormLayout(self)

        self.author_edit = QLineEdit()
        self.version_edit = QLineEdit("1.0")
        self.tags_edit = QLineEdit()
        self.compat_edit = QLineEdit("Hauswerk >=1.0")
        self.changelog_edit = QTextEdit("Gegenereerd via Plugin Wizard")
        self.changelog_edit.setFixedHeight(60)

        self.layout.addRow("Auteur:", self.author_edit)
        self.layout.addRow("Versie:", self.version_edit)
        self.layout.addRow("Tags (komma's):", self.tags_edit)
        self.layout.addRow("Compatibiliteit:", self.compat_edit)
        self.layout.addRow("Changelog:", self.changelog_edit)

    def get_metadata(self):
        return {
            "author": self.author_edit.text() or "Onbekend",
            "version": self.version_edit.text() or "1.0",
            "tags": [t.strip() for t in self.tags_edit.text().split(",") if t.strip()],
            "compatibility": [self.compat_edit.text().strip()] if self.compat_edit.text().strip() else ["Hauswerk >=1.0"],
            "changelog": self.changelog_edit.toPlainText() or "Gegenereerd via Plugin Wizard"
        }
