from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
import os
import json
from config import BASE_PATH

class EditPromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Prompt")
        self.setFixedSize(500, 800)
        layout = QVBoxLayout(self)

        self.ai_prompt_label = QLabel("AI Prompt:")
        self.ai_prompt_edit = QTextEdit(self)
        self.ai_prompt_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.ai_prompt_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.ai_prompt_edit.setAcceptRichText(False)

        self.negative_prompt_label = QLabel("Negative Prompt:")
        self.negative_prompt_edit = QTextEdit(self)
        self.negative_prompt_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.negative_prompt_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.negative_prompt_edit.setAcceptRichText(False)

        self.system_prompt_label = QLabel("System Prompt (do not modify):")
        self.system_prompt_edit = QTextEdit(self)
        self.system_prompt_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.system_prompt_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.system_prompt_edit.setAcceptRichText(False)
        self.system_prompt_edit.setReadOnly(True)

        layout.addWidget(self.ai_prompt_label)
        layout.addWidget(self.ai_prompt_edit, 1)
        layout.addWidget(self.negative_prompt_label)
        layout.addWidget(self.negative_prompt_edit, 1)
        layout.addWidget(self.system_prompt_label)
        layout.addWidget(self.system_prompt_edit, 1)

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
            prompt_data = data.get("prompt", {})
            self.ai_prompt_edit.setPlainText(prompt_data.get("ai_prompt", ""))
            self.negative_prompt_edit.setPlainText(prompt_data.get("negative_prompt", ""))
            self.system_prompt_edit.setPlainText(prompt_data.get("system_prompt", ""))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load prompt: {e}")

    def save_prompt(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "prompt" not in data:
                data["prompt"] = {}
            data["prompt"]["ai_prompt"] = self.ai_prompt_edit.toPlainText()
            data["prompt"]["negative_prompt"] = self.negative_prompt_edit.toPlainText()
            # system_prompt is not editable, so do not update it
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save prompt: {e}")
