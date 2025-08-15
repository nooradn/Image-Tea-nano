from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
import os
import json
from config import BASE_PATH

class EditPromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Prompt")
        self.setFixedSize(400, 500)
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit(self)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.text_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.text_edit.setAcceptRichText(False)
        layout.addWidget(self.text_edit, 1)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.config_path = os.path.join(BASE_PATH, "configs", "ai_prompt.json")
        self.load_prompt()
        self.save_btn.clicked.connect(self.save_prompt)

    def load_prompt(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            prompt = data["ai_prompt"]
            self.text_edit.setPlainText(prompt)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load prompt: {e}")

    def save_prompt(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["ai_prompt"] = self.text_edit.toPlainText()
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save prompt: {e}")
