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
from helpers.metadata_helper.metadata_operation import write_metadata_to_images, read_metadata_pyexiv2
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

def _extract_xmp_value(val):
    if isinstance(val, dict):
        return val.get('value', '') if 'value' in val else ''
    return val if isinstance(val, str) else ''

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
                t, d, tg = read_metadata_pyexiv2(path)
                title = _extract_xmp_value(t)
                description = _extract_xmp_value(d)
                tags = tg if tg else None
                title = title if title else None
                description = description if description else None
                self.db.add_file(path, fname, title, description, tags, status="draft")
                added += 1
        if added:
            refresh_table(self)

    def import_images(self):
        if import_files(self, self.db, None, None):
            rows = self.db.get_all_files()
            for row in rows:
                id_, filepath, filename, title, description, tags, status = row
                if status is None or status != "draft":
                    t, d, tg = read_metadata_pyexiv2(filepath)
                    t_val = _extract_xmp_value(t)
                    d_val = _extract_xmp_value(d)
                    t_val = t_val if t_val else None
                    d_val = d_val if d_val else None
                    self.db.update_metadata(filepath, t_val if t_val is not None else title, d_val if d_val is not None else description, tg if tg else tags, status="draft")
            refresh_table(self)

    def batch_generate_metadata(self):
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

        mode = "all"
        selected_ids = []
        if hasattr(self, "generate_mode_combo"):
            mode_idx = self.generate_mode_combo.currentIndex()
            mode = self.generate_mode_combo.currentData() if mode_idx >= 0 else "all"
        if mode == "selected":
            if hasattr(self.table, "selectedItems"):
                selected_rows = self.table.selectedItems()
                selected_ids = []
                for item in selected_rows:
                    row = item.row()
                    id_item = self.table.item(row, 0)
                    if id_item:
                        selected_ids.append(int(id_item.text()))
        rows = []
        all_rows = self.db.get_all_files()
        if mode == "all":
            rows = all_rows
        elif mode == "selected":
            rows = [row for row in all_rows if row[0] in selected_ids]
        elif mode == "failed":
            rows = [row for row in all_rows if row[6] == "failed"]
        if not rows:
            QMessageBox.information(self, "No Files", "No files to process.")
            return
        self.table.progress_bar.setVisible(True)
        self.table.progress_bar.setMinimum(0)
        self.table.progress_bar.setMaximum(len(rows))
        self.table.progress_bar.setValue(0)
        self.table.progress_bar.setFormat('Generating metadata...')
        QApplication.processEvents()
        thread = ImageTeaGeneratorThread(api_key, model, rows, DB_PATH)
        thread.progress.connect(self._on_progress_update)
        thread.finished.connect(self._on_generation_finished)
        thread.row_status.connect(self._on_row_status_update)
        thread.start()
        self.thread = thread

    def _on_progress_update(self, current, total):
        self.table.progress_bar.setMaximum(total)
        self.table.progress_bar.setValue(current)
        QApplication.processEvents()

    def _on_row_status_update(self, row_idx, status):
        if hasattr(self.table, "set_row_status_color"):
            self.table.set_row_status_color(row_idx, status)
        if status == "success":
            # Update row data in real-time after success
            table_widget = self.table.table
            id_item = table_widget.item(row_idx, 0)
            if id_item:
                filepath = id_item.text()
                # Find latest row data from DB
                row_data = None
                for row in self.db.get_all_files():
                    if str(row[1]) == filepath:
                        row_data = row
                        break
                if row_data and hasattr(self.table, "update_row_data"):
                    self.table.update_row_data(row_idx, row_data)
        QApplication.processEvents()

    def _on_generation_finished(self, errors):
        self.table.progress_bar.setFormat('Done')
        self.table.progress_bar.setMaximum(1)
        self.table.progress_bar.setValue(1)
        QApplication.processEvents()
        refresh_table(self)
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