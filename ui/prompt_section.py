from PySide6.QtWidgets import QWidget, QHBoxLayout, QSpinBox, QSizePolicy, QLabel, QPushButton, QSpacerItem
from PySide6.QtCore import Qt
import qtawesome as qta
import json
import os
from config import BASE_PATH
from dialogs.edit_prompt_dialog import EditPromptDialog

class PromptSectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.setContentsMargins(0, 0, 0, 0)

        min_title_label = QLabel("Min Title Length")
        self.min_title_spin = QSpinBox()
        self.min_title_spin.setRange(1, 1000)
        self.min_title_spin.setValue(50)
        self.min_title_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        max_title_label = QLabel("Max Title Length")
        self.max_title_spin = QSpinBox()
        self.max_title_spin.setRange(1, 1000)
        self.max_title_spin.setValue(80)
        self.max_title_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        tag_count_label = QLabel("Tag Count")
        self.tag_count_spin = QSpinBox()
        self.tag_count_spin.setRange(1, 100)
        self.tag_count_spin.setValue(20)
        self.tag_count_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        min_title_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        max_title_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        tag_count_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        main_layout.addWidget(min_title_label)
        main_layout.addWidget(self.min_title_spin)
        main_layout.addWidget(max_title_label)
        main_layout.addWidget(self.max_title_spin)
        main_layout.addWidget(tag_count_label)
        main_layout.addWidget(self.tag_count_spin)

        main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.edit_prompt_btn = QPushButton(qta.icon('fa5s.edit'), "Prompt")
        self.edit_prompt_btn.setToolTip("Edit the prompt configuration")
        self.edit_prompt_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(self.edit_prompt_btn)

        self.setLayout(main_layout)

        self.config_path = os.path.join(BASE_PATH, "configs", "ai_prompt.json")
        self.min_title_spin.valueChanged.connect(self.save_prompt_config)
        self.max_title_spin.valueChanged.connect(self.save_prompt_config)
        self.tag_count_spin.valueChanged.connect(self.save_prompt_config)
        self.load_prompt_config()

        self.edit_prompt_btn.clicked.connect(self.open_edit_prompt_dialog)

    def open_edit_prompt_dialog(self):
        dlg = EditPromptDialog(self)
        dlg.exec()

    def load_prompt_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.min_title_spin.setValue(data["min_title_length"])
            self.max_title_spin.setValue(data["max_title_length"])
            self.tag_count_spin.setValue(data["required_tag_count"])
        except Exception as e:
            print(f"Failed to load prompt config: {e}")

    def save_prompt_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data["min_title_length"] = self.min_title_spin.value()
        data["max_title_length"] = self.max_title_spin.value()
        data["required_tag_count"] = self.tag_count_spin.value()
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save prompt config: {e}")