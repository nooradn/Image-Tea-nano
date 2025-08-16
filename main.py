import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BASE_PATH
sys.path.insert(0, BASE_PATH)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QColor
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
        self.generator_thread = None
        self.is_generating = False

        if hasattr(self, "gen_btn"):
            self.gen_btn.clicked.disconnect()
            self.gen_btn.clicked.connect(self._on_gen_btn_clicked)

    def _on_gen_btn_clicked(self):
        if self.is_generating:
            self.stop_generate_metadata()
        else:
            self.batch_generate_metadata()

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
        if self.is_generating:
            return
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
        row_map = {}
        if hasattr(self, "gen_mode_combo"):
            mode_idx = self.gen_mode_combo.currentIndex()
            mode_text = self.gen_mode_combo.currentText().lower()
            if "selected" in mode_text:
                mode = "selected"
            elif "failed" in mode_text:
                mode = "failed"
            else:
                mode = "all"
        rows = []
        all_rows = self.db.get_all_files()
        if mode == "all":
            rows = all_rows
        elif mode == "selected":
            table_widget = self.table.table
            selected_ids = []
            for row_idx in range(table_widget.rowCount()):
                checkbox_item = table_widget.item(row_idx, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    id_data = checkbox_item.data(Qt.UserRole)
                    if id_data is not None:
                        try:
                            selected_ids.append(int(id_data))
                            row_map[int(id_data)] = row_idx
                        except Exception:
                            print(f"[DEBUG] Failed to parse id from checkbox row {row_idx}: {id_data}")
            print(f"[DEBUG] Selected IDs for generate: {selected_ids}")
            rows = [row for row in all_rows if row[0] in selected_ids]
        elif mode == "failed":
            rows = [row for row in all_rows if row[6] == "failed"]
        if mode == "selected" and not selected_ids:
            print("[DEBUG] No rows checked for Selected Only mode.")
            QMessageBox.information(self, "No Files", "No files selected (checkbox) to process.")
            return
        if not rows:
            print("[DEBUG] No rows to process after filtering.")
            QMessageBox.information(self, "No Files", "No files to process.")
            return
        self.table.progress_bar.setVisible(True)
        self.table.progress_bar.setMinimum(0)
        self.table.progress_bar.setMaximum(len(rows))
        self.table.progress_bar.setValue(0)
        self.table.progress_bar.setFormat('Generating metadata...')
        QApplication.processEvents()
        self.generator_thread = ImageTeaGeneratorThread(api_key, model, rows, DB_PATH, row_map=row_map)
        self.generator_thread.progress.connect(self._on_progress_update)
        self.generator_thread.finished.connect(self._on_generation_finished)
        self.generator_thread.row_status.connect(self._on_row_status_update)
        self.generator_thread.start()
        self.is_generating = True
        self._set_gen_btn_stop_state(True)

    def stop_generate_metadata(self):
        if self.generator_thread and self.generator_thread.isRunning():
            print("[STOP] Stopping metadata generation process...")
            table_widget = self.table.table
            for row in range(table_widget.rowCount()):
                status_item = table_widget.item(row, 7)
                if status_item and status_item.text().lower() == "processing":
                    filepath_item = table_widget.item(row, 0)
                    if filepath_item:
                        filepath = filepath_item.text()
                        self.db.update_file_status(filepath, "stopped")
                    status_item.setText("Stopped")
                    for col in range(table_widget.columnCount()):
                        item = table_widget.item(row, col)
                        if item:
                            item.setBackground(QColor(255, 0, 0, int(0.15 * 255)))
            self.generator_thread.terminate()
            self.generator_thread.wait()
            self.generator_thread = None
        self.is_generating = False
        self._set_gen_btn_stop_state(False)
        self.table.progress_bar.setVisible(False)
        self.table.progress_bar.setValue(0)
        self.table.progress_bar.setFormat('')
        refresh_table(self)
        print("[STOP] Metadata generation stopped and UI reset.")

    def _set_gen_btn_stop_state(self, is_stop):
        if hasattr(self, "gen_btn"):
            if is_stop:
                self.gen_btn.setText("Stop Processes")
                self.gen_btn.setIcon(qta.icon('fa5s.stop'))
                self.gen_btn.setStyleSheet("background-color: rgba(204, 0, 0, 0.3);")
            else:
                self.gen_btn.setText("Generate Metadata")
                self.gen_btn.setIcon(qta.icon('fa5s.magic'))
                self.gen_btn.setStyleSheet("")

    def _reset_progress_and_table(self):
        self.table.progress_bar.setVisible(False)
        self.table.progress_bar.setValue(0)
        self.table.progress_bar.setFormat('')
        refresh_table(self)

    def _on_progress_update(self, current, total):
        self.table.progress_bar.setMaximum(total)
        self.table.progress_bar.setValue(current)
        QApplication.processEvents()

    def _on_row_status_update(self, row_idx, status):
        if hasattr(self.table, "set_row_status_color"):
            self.table.set_row_status_color(row_idx, status)
        if status == "success":
            table_widget = self.table.table
            id_item = table_widget.item(row_idx, 1)
            if id_item:
                filepath = id_item.text()
                row_data = None
                for row in self.db.get_all_files():
                    if str(row[1]) == filepath:
                        row_data = row
                        break
                if row_data and hasattr(self.table, "update_row_data"):
                    self.table.update_row_data(row_idx, row_data)
        QApplication.processEvents()

    def _on_generation_finished(self, errors):
        self.is_generating = False
        self._set_gen_btn_stop_state(False)
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