from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QLineEdit, QFileDialog, QProgressDialog, QApplication
from PySide6.QtCore import Qt
import json
import os
import sys
from config import BASE_PATH
from helpers.csv_exporter import export_csv
import qtawesome as qta

class CSVExporterDialog(QDialog):
    CONFIG_PATH = os.path.join(BASE_PATH, "configs", "csv_config.json")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Metadata to CSV")
        self.setFixedWidth(400)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Info label
        info_label = QLabel("Export all metadata to a unified CSV format:\n"
                           "• file_name, title, description, keywords\n"
                           "• ss_category (Shutterstock categories)\n"
                           "• as_code (Adobe Stock category code)")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666; font-size: 11px; padding: 10px; background-color: #f0f0f0; border-radius: 5px; }")
        main_layout.addWidget(info_label)

        # Output path entry and select button
        path_label = QLabel("Select output folder:")
        main_layout.addWidget(path_label)
        
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
        self.select_output_btn = QPushButton(qta.icon('fa6s.folder-open'), "Select")
        self.select_output_btn.setToolTip("Select output folder")
        self.select_output_btn.clicked.connect(self.select_output_path)
        output_layout.addWidget(self.select_output_btn)

        main_layout.addLayout(output_layout)

        # Export button
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton(qta.icon('fa6s.file-csv'), "Export CSV")
        self.export_btn.setToolTip("Export metadata to CSV")
        self.export_btn.clicked.connect(self.do_export)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        main_layout.addLayout(btn_layout)

    def paste_output_path(self):
        """Paste path from clipboard."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.output_lineedit.setText(text)

    def select_output_path(self):
        """Open folder selection dialog."""
        home_dir = os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder", home_dir)
        if path:
            self.output_lineedit.setText(path)

    def open_folder_windows(self, folder_path):
        """Open folder in Windows Explorer."""
        if sys.platform.startswith("win"):
            os.startfile(folder_path)

    def do_export(self):
        """Perform the CSV export."""
        output_path = self.output_lineedit.text().strip()
        
        if not output_path:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Output Path", "Please select an output folder.")
            return
        
        if not os.path.exists(output_path):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Path", "The selected output folder does not exist.")
            return
        
        # Get file count for progress tracking
        from database.db_operation import ImageTeaDB
        db = ImageTeaDB()
        files = db.get_all_files()
        total_files = len(files)
        
        if total_files == 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Files", "No files found to export.")
            self.accept()
            return
        
        # Create progress dialog
        progress = QProgressDialog("Exporting CSV...", "Cancel", 0, total_files, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        
        def progress_callback():
            if progress.wasCanceled():
                return
            value = progress.value() + 1
            progress.setValue(value)
        
        # Perform export
        try:
            success = export_csv(output_path, progress_callback)
            progress.setValue(total_files)
            
            if success:
                self.open_folder_windows(output_path)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Export Complete", 
                                      f"CSV file exported successfully to:\n{output_path}")
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Export Failed", 
                                  "Failed to export CSV. Please check the console for error details.")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Export Error", f"An error occurred during export:\n{str(e)}")
        
        self.accept()
