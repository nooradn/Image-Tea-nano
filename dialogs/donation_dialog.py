from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
from config import BASE_PATH

class DonateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Donate")
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)
        label = QLabel("Scan QRIS to donate:")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        image_path = os.path.join(BASE_PATH, "res", "images", "qris.jpeg")
        img_label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            img_label.setPixmap(pixmap.scaledToWidth(300))
            img_label.setAlignment(Qt.AlignCenter)
        else:
            img_label.setText("QRIS image not found.")
            img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label)
