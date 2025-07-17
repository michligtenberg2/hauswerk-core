class Logger:
    """Simple GUI logger that buffers messages until a widget is attached."""

    _log_widget = None
    _buffer = []
    _enabled = True

    @classmethod
    def init(cls, widget):
        cls._log_widget = widget
        if cls._buffer:
            for msg in cls._buffer:
                cls._append(msg)
            cls._buffer.clear()

    @classmethod
    def log(cls, message):
        if not cls._enabled:
            return
        if cls._log_widget:
            cls._append(message)
        else:
            cls._buffer.append(message)

    @classmethod
    def set_enabled(cls, state: bool):
        cls._enabled = state

    @classmethod
    def _append(cls, msg):
        cls._log_widget.append(msg)
        sb = cls._log_widget.verticalScrollBar()
        sb.setValue(sb.maximum())
