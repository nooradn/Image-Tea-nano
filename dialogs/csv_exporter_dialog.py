from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QLabel, QGridLayout, QWidget
from PySide6.QtCore import Qt
import json
import os
from config import BASE_PATH

class CSVExporterDialog(QDialog):
    CONFIG_PATH = os.path.join(BASE_PATH, "configs", "csv_config.json")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Metadata to CSV")
        self.setFixedWidth(400)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        label = QLabel("Select platforms to export:")
        main_layout.addWidget(label)

        self.platform_checkboxes = []
        self.platforms = [
            "Freepik",
            "Adobe Stock",
            "Shutterstock",
            "iStock",
            "Dreamstime",
            "123RF",
            "Depositphotos",
            "Alamy",
            "Bigstock"
        ]

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)
        main_layout.addWidget(grid_widget)

        columns = 2
        self.checkbox_map = {}
        self.config = self.load_config()

        for idx, platform in enumerate(self.platforms):
            checkbox = QCheckBox(platform)
            row = idx // columns
            col = idx % columns
            grid_layout.addWidget(checkbox, row, col)
            self.platform_checkboxes.append(checkbox)
            self.checkbox_map[platform] = checkbox
            checkbox.setChecked(self.config.get(platform, False))
            checkbox.stateChanged.connect(self.save_config_realtime)

    def load_config(self):
        if os.path.exists(self.CONFIG_PATH):
            try:
                with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config_realtime(self):
        config = {}
        for platform, checkbox in self.checkbox_map.items():
            config[platform] = checkbox.isChecked()
        try:
            with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
