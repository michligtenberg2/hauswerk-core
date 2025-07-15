# widgets/standard_tool_layout.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

class StandardToolLayout(QWidget):
    def __init__(
        self, input_row=None, output_row=None, option_rows=None,
        button_row=None, progress_row=None, log_widget=None
    ):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)                      # <-- Meer ruimte tussen rijen
        layout.setContentsMargins(22, 14, 22, 14)  # <-- Bredere marges rondom
        if input_row:
            layout.addLayout(input_row)
        if output_row:
            layout.addLayout(output_row)
        if option_rows:
            for opt in option_rows:
                layout.addLayout(opt) if isinstance(opt, QHBoxLayout) else layout.addWidget(opt)
        if button_row:
            layout.addLayout(button_row)
        if progress_row:
            layout.addLayout(progress_row)
        if log_widget:
            layout.addWidget(log_widget)
        layout.addStretch()
        self.setLayout(layout)
