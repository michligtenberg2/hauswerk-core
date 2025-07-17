import sys
import types
import unittest
from PyQt6.QtWidgets import QApplication

# Stub QSoundEffect to avoid libpulse dependency during tests
multimedia_stub = types.ModuleType("PyQt6.QtMultimedia")
class DummySoundEffect:
    def __init__(self, *args, **kwargs):
        pass
multimedia_stub.QSoundEffect = DummySoundEffect
sys.modules.setdefault("PyQt6.QtMultimedia", multimedia_stub)

from widgets.pluginstoregrid import PluginStoreGridWidget

class TestTagFilter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        # Prevent network loading of plugins in __init__
        self._original_load = PluginStoreGridWidget.load_plugins
        PluginStoreGridWidget.load_plugins = lambda self: None
        self.widget = PluginStoreGridWidget()
        PluginStoreGridWidget.load_plugins = self._original_load

        self.captured = None
        def capture(plugins):
            self.captured = plugins
        self.widget.display_plugins = capture

        self.widget.all_plugins = [
            {"name": "Alpha", "tags": ["audio"]},
            {"name": "Beta", "tags": ["video"]},
        ]

        self.widget.tag_filter.clear()
        self.widget.tag_filter.addItems(["Alle tags", "audio", "video"])

    def test_filter_audio_tag(self):
        self.widget.tag_filter.setCurrentText("audio")
        self.widget.filter_plugins()
        self.assertEqual(len(self.captured), 1)
        self.assertEqual(self.captured[0]["name"], "Alpha")

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

if __name__ == "__main__":
    unittest.main()
