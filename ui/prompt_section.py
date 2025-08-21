from PySide6.QtWidgets import QWidget, QHBoxLayout, QSpinBox, QSizePolicy, QLabel, QSpacerItem, QVBoxLayout
from PySide6.QtCore import Qt
import json
import os
from config import BASE_PATH

class PromptSectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loading = False
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)

        min_title_label = QLabel("Min Title")
        self.min_title_spin = QSpinBox()
        self.min_title_spin.setRange(1, 1000)
        self.min_title_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.min_title_spin.setToolTip("Minimum title length in characters.\nShorter titles may be less descriptive.")

        max_title_label = QLabel("Max Title")
        self.max_title_spin = QSpinBox()
        self.max_title_spin.setRange(1, 1000)
        self.max_title_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.max_title_spin.setToolTip("Maximum title length in characters.\nTitles longer than this will be truncated.")

        max_desc_label = QLabel("Max Desc")
        self.max_desc_spin = QSpinBox()
        self.max_desc_spin.setRange(1, 2000)
        self.max_desc_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.max_desc_spin.setToolTip("Maximum description length in characters.\nKeep descriptions concise and clear.")

        tag_count_label = QLabel("Tag Count")
        self.tag_count_spin = QSpinBox()
        self.tag_count_spin.setRange(1, 100)
        self.tag_count_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.tag_count_spin.setToolTip("Number of keywords/tags to generate.\nExactly this many tags will be used.")

        batch_size_label = QLabel("Batch Size")
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 20)
        self.batch_size_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.batch_size_spin.setToolTip("Number of files processed per batch.\nMaximum is 20 per batch.")

        compression_label = QLabel("Compression")
        self.cache_spin = QSpinBox()
        self.cache_spin.setRange(1, 100)
        self.cache_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.cache_spin.setToolTip("Compression quality (1-100).\nLower value = higher compression, more efficient internet data usage.")

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(min_title_label)
        main_layout.addWidget(self.min_title_spin)
        main_layout.addWidget(max_title_label)
        main_layout.addWidget(self.max_title_spin)
        main_layout.addWidget(max_desc_label)
        main_layout.addWidget(self.max_desc_spin)
        main_layout.addWidget(tag_count_label)
        main_layout.addWidget(self.tag_count_spin)
        main_layout.addWidget(batch_size_label)
        main_layout.addWidget(self.batch_size_spin)
        main_layout.addWidget(compression_label)
        main_layout.addWidget(self.cache_spin)
        main_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        outer_layout.addLayout(main_layout)
        self.setLayout(outer_layout)

        self.config_path = os.path.join(BASE_PATH, "configs", "ai_config.json")
        self.min_title_spin.valueChanged.connect(self.save_prompt_config)
        self.max_title_spin.valueChanged.connect(self.save_prompt_config)
        self.max_desc_spin.valueChanged.connect(self.save_prompt_config)
        self.tag_count_spin.valueChanged.connect(self.save_prompt_config)
        self.batch_size_spin.valueChanged.connect(self.save_prompt_config)
        self.cache_spin.valueChanged.connect(self.save_prompt_config)
        self.load_prompt_config()

    def load_prompt_config(self):
        self._loading = True
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.min_title_spin.setValue(data["min_title_length"])
            self.max_title_spin.setValue(data["max_title_length"])
            self.max_desc_spin.setValue(data["max_description_length"])
            self.tag_count_spin.setValue(data["required_tag_count"])
            self.batch_size_spin.setValue(min(max(data["batch_size"], 1), 20))
            self.cache_spin.setValue(data["compression_quality"])
        except Exception as e:
            print(f"Failed to load prompt config: {e}")
        self._loading = False

    def save_prompt_config(self):
        if getattr(self, "_loading", False):
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data["min_title_length"] = self.min_title_spin.value()
        data["max_title_length"] = self.max_title_spin.value()
        data["max_description_length"] = self.max_desc_spin.value()
        data["required_tag_count"] = self.tag_count_spin.value()
        data["batch_size"] = self.batch_size_spin.value()
        data["compression_quality"] = self.cache_spin.value()
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save prompt config: {e}")