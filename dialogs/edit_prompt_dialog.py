from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel, QMessageBox, QWidget, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_PATH

class EditPromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Prompt")
        self.setFixedSize(600, 500)
        main_layout = QVBoxLayout(self)

        top_widget = QWidget(self)
        top_grid = QGridLayout(top_widget)
        top_grid.setColumnStretch(0, 1)
        top_grid.setColumnStretch(1, 1)
        top_grid.setContentsMargins(0, 0, 0, 0)

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

        top_grid.addWidget(self.ai_prompt_label, 0, 0)
        top_grid.addWidget(self.negative_prompt_label, 0, 1)
        top_grid.addWidget(self.ai_prompt_edit, 1, 0)
        top_grid.addWidget(self.negative_prompt_edit, 1, 1)
        main_layout.addWidget(top_widget, 2)

        self.system_prompt_label = QLabel("System Prompt (do not modify):")
        self.system_prompt_edit = QTextEdit(self)
        self.system_prompt_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.system_prompt_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.system_prompt_edit.setAcceptRichText(False)
        self.system_prompt_edit.setReadOnly(True)
        self.system_prompt_edit.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.system_prompt_label)
        main_layout.addWidget(self.system_prompt_edit, 1)

        placeholder_info = QLabel(
            "Prompt Placeholders:\n"
            "The prompts use the following placeholders, which will be replaced automatically when generating metadata:\n"
            "  • _MIN_LEN_: Minimum title length\n"
            "  • _MAX_LEN_: Maximum title length\n"
            "  • _MAX_DESC_LEN_: Maximum description length\n"
            "  • _TAGS_COUNT_: Required number of tags\n"
            "These placeholders ensure your prompts always match the current configuration."
        )
        placeholder_info.setWordWrap(True)
        main_layout.addWidget(placeholder_info)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

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
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save prompt: {e}")
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
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save prompt: {e}")
