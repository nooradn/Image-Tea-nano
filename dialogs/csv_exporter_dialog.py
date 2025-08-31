from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QLabel, QGridLayout, QWidget, QPushButton, QHBoxLayout, QLineEdit, QFileDialog, QProgressDialog, QApplication
from PySide6.QtCore import Qt
import json
import os
from config import BASE_PATH
from helpers.csv_exporter import export_csv_for_platforms
import qtawesome as qta

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
            "123RF",
            "Vecteezy",
            "Pond5"
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

        # Output path entry and select button
        output_layout = QHBoxLayout()
        self.output_lineedit = QLineEdit()
        self.output_lineedit.setPlaceholderText("Select output folder...")
        output_layout.addWidget(self.output_lineedit)

        # Paste button
        self.paste_output_btn = QPushButton(qta.icon('fa6s.paste'), "")
        self.paste_output_btn.setToolTip("Paste path from clipboard")
        self.paste_output_btn.setFixedWidth(32)
        self.paste_output_btn.clicked.connect(self.paste_output_path)
        output_layout.addWidget(self.paste_output_btn)

        # Select output button
        self.select_output_btn = QPushButton(qta.icon('fa6s.folder-open'), "Select Output")
        self.select_output_btn.setToolTip("Select output folder")
        self.select_output_btn.clicked.connect(self.select_output_path)
        output_layout.addWidget(self.select_output_btn)

        main_layout.addLayout(output_layout)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton(qta.icon('fa6s.file-csv'), "Export")
        self.ok_btn.setToolTip("Export metadata to CSV")
        self.ok_btn.clicked.connect(self.export_csv)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        main_layout.addLayout(btn_layout)

    def paste_output_path(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.output_lineedit.setText(text)

    def select_output_path(self):
        home_dir = os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder", home_dir)
        if path:
            self.output_lineedit.setText(path)

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

    def export_csv(self):
        selected = [p for p, cb in self.checkbox_map.items() if cb.isChecked()]
        output_path = self.output_lineedit.text()
        if not selected or not output_path:
            self.accept()
            return
        from database.db_operation import ImageTeaDB
        db = ImageTeaDB()
        files = db.get_all_files()
        total_files = len(files) * len(selected)
        progress = QProgressDialog("Exporting CSV...", "Cancel", 0, total_files, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        def progress_callback():
            value = progress.value() + 1
            progress.setValue(value)
        export_csv_for_platforms(selected, output_path, progress_callback)
        progress.setValue(total_files)
        self.accept()
