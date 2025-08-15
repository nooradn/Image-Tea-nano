from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class StatsSectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label_total = QLabel("Total Images: 0")
        self.label_selected = QLabel("Selected: 0")
        self.label_failed = QLabel("Failed: 0")
        layout.addWidget(self.label_total)
        layout.addWidget(self.label_selected)
        layout.addWidget(self.label_failed)
