
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication, QSplashScreen
import os

def show_splash(theme="light", parent_window=None, duration=1500):
    splash = None
    base_path = os.path.dirname(__file__)
    # search for resources one directory up from the core package
    res_path = os.path.normpath(os.path.join(base_path, "..", "resources"))

    svg_path = os.path.join(res_path, f"splash_{theme}.svg")
    if not os.path.exists(svg_path):
        # fall back to the generic logo
        svg_path = os.path.join(res_path, "logo.svg")
    if not os.path.exists(svg_path):
        svg_path = None

    if svg_path:
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPixmap(pixmap)
        renderer.render(painter)
        splash_pix = pixmap
    else:
        png_path = os.path.join(res_path, f"splash_{theme}.png")
        if not os.path.exists(png_path):
            # fall back to the generic logo
            png_path = os.path.join(res_path, "logo.png")
        if os.path.exists(png_path):
            splash_pix = QPixmap(png_path).scaledToWidth(500, Qt.TransformationMode.SmoothTransformation)
        else:
            return

    splash = QSplashScreen(splash_pix)
    splash.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    splash.setWindowOpacity(0.0)
    splash.show()
    app = QApplication.instance()
    app.processEvents()

    fade_in = QPropertyAnimation(splash, b"windowOpacity")
    fade_in.setDuration(800)
    fade_in.setStartValue(0.0)
    fade_in.setEndValue(1.0)
    fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
    fade_in.start()

    def fade_out():
        fade = QPropertyAnimation(splash, b"windowOpacity")
        fade.setDuration(400)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.Type.InOutQuad)
        fade.finished.connect(lambda: splash.finish(parent_window) if parent_window else splash.close())
        fade.start()

    QTimer.singleShot(duration, fade_out)
