import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BASE_PATH
sys.path.insert(0, BASE_PATH)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import qtawesome as qta
from helpers.metadata_helper.metadata_operation import ImageTeaGeneratorThread
from helpers.metadata_helper.metadata_operation import write_metadata_to_images
from database.db_operation import ImageTeaDB, DB_PATH
from ui.setup_ui import setup_ui
from ui.main_table import (
    refresh_table,
    delete_selected,
    clear_all,
    ImageTableWidget
)
from ui.file_dnd_widget import DragDropWidget
from helpers.file_importer import import_files

class ImageTeaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Tea (nano) Metadata Generator")
        self.setWindowIcon(qta.icon('fa5s.magic'))
        self.db = ImageTeaDB()
        self.api_key = self.db.get_api_key('gemini')
        setup_ui(self)
        refresh_table(self)

    def handle_dropped_files(self, paths):
        added = 0
        for path in paths:
            if os.path.isfile(path):
                fname = os.path.basename(path)
                self.db.add_file(path, fname)
                added += 1
        if added:
            refresh_table(self)

    def import_images(self):
        if import_files(self, self.db, None, None):
            refresh_table(self)

    def batch_generate_metadata(self):
        # Get api_key and model from current combo selection in setup_ui (api_key_combo and model from api_key_map)
        api_key = None
        model = None
        if hasattr(self, "api_key_combo") and hasattr(self, "api_key_map"):
            idx = self.api_key_combo.currentIndex()
            api_key = self.api_key_combo.currentData() if idx >= 0 else None
            if api_key and api_key in self.api_key_map:
                model = self.api_key_map[api_key].get("model")
        if not api_key or not model:
            QMessageBox.warning(self, "API Key", "Please select both API Key and Model first.")
            return
        rows = self.db.get_all_files()
        if not rows:
            QMessageBox.information(self, "No Files", "No files to process.")
            return
        self.table.progress_bar.setVisible(True)
        self.table.progress_bar.setMinimum(0)
        self.table.progress_bar.setMaximum(0)
        self.table.progress_bar.setFormat('Generating metadata...')
        QApplication.processEvents()
        thread = ImageTeaGeneratorThread(api_key, model, rows, DB_PATH)
        thread.progress.connect(self._on_progress_update)
        thread.finished.connect(self._on_generation_finished)
        thread.start()
        self.thread = thread

    def _on_progress_update(self, current, total):
        pass

    def _on_generation_finished(self, errors):
        self.table.progress_bar.setFormat('Done')
        self.table.progress_bar.setMaximum(1)
        self.table.progress_bar.setValue(1)
        QApplication.processEvents()
        refresh_table(self)
        self.table.progress_bar.setVisible(False)
        if errors:
            print("[Gemini Errors]")
            for err in errors:
                print(err)
        else:
            print("[Gemini] Metadata generated for all files.")

    def write_metadata_to_images(self):
        write_metadata_to_images(self.db, None, None)

    def delete_selected(self):
        delete_selected(self)

    def clear_all(self):
        clear_all(self)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageTeaMainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())