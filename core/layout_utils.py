from PyQt6.QtWidgets import QLayout
from core.settings import SettingsManager

def apply_compact(layout: QLayout):
    """Past compacte layout toe als compact_mode in settings is ingeschakeld."""
    if SettingsManager.instance().get("compact_mode"):
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)
