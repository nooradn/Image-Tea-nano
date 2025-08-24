from PySide6.QtWidgets import QStatusBar, QLabel

class MainStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_label = QLabel("")
        self.addWidget(self.status_label)

    def set_status(self, text):
        self.status_label.setText(text)
