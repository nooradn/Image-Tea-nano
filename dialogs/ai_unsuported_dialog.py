from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class AIUnsuportedDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Unsupported")
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)
        self.label = QLabel(message)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

    def set_message(self, message):
        self.label.setText(message)
