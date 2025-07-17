import os
from core.settings import SettingsManager

class StyleManager:
    @staticmethod
    def apply_theme(app, theme_name, font_size=None, accent=None):
        qss_file = os.path.join(SettingsManager.styles_dir(), f"{theme_name}.qss")
        if os.path.exists(qss_file):
            with open(qss_file, "r") as f:
                qss = f.read()
            if accent is None:
                accent = SettingsManager.instance().get("accent_color", "#44cc88")
            qss = qss.replace("@accent", accent)
            if font_size:
                qss += f"\nQWidget {{ font-size: %dpx; }}\n" % int(font_size)
            app.setStyleSheet(qss)
        else:
            app.setStyleSheet("")
