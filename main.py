import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BASE_PATH
sys.path.insert(0, BASE_PATH)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon
import qtawesome as qta
from helpers.metadata_helper.metadata_operation import ImageTeaGeneratorThread
from database.db_operation import ImageTeaDB, DB_PATH
from ui.setup_ui import setup_ui
from dialogs.ai_unsuported_dialog import AIUnsuportedDialog

class ImageTeaMainWindow(QMainWindow):
    show_ai_unsupported_dialog = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Tea (nano) Metadata Generator")
        icon_path = os.path.join(BASE_PATH, "res", "image_tea.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.db = ImageTeaDB()
        self.api_key = self.db.get_api_key('gemini')
        setup_ui(self)
        self.table.refresh_table()
        self.generator_thread = None
        self.is_generating = False
        self.show_ai_unsupported_dialog.connect(self._show_ai_unsupported_dialog_slot)

        if hasattr(self, "gen_btn"):
            self.gen_btn.clicked.disconnect()
            self.gen_btn.clicked.connect(self._on_gen_btn_clicked)

        self.update_token_stats_ui()

    def _show_ai_unsupported_dialog_slot(self, message):
        dialog = AIUnsuportedDialog(message, parent=self)
        dialog.exec()

    def _on_gen_btn_clicked(self):
        if self.is_generating:
            self.stop_generate_metadata()
        else:
            self.batch_generate_metadata()

    def batch_generate_metadata(self):
        if self.is_generating:
            return

        api_key = None
        model = None
        service = None
        if hasattr(self, "api_key_combo") and hasattr(self, "api_key_map"):
            idx = self.api_key_combo.currentIndex()
            api_key = self.api_key_combo.currentData() if idx >= 0 else None
            if api_key and api_key in self.api_key_map:
                model = self.api_key_map[api_key].get("model")
                service = self.api_key_map[api_key].get("service")
                if service:
                    service = service.lower()
        if not api_key or not model or not service:
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

        print(f"[DEBUG] Using service: {service}")
        if service == "gemini":
            from helpers.ai_helper.gemini_helper import generate_metadata_gemini, track_gemini_generation_time
            def metadata_func(api_key, model, image_path, prompt=None):
                import time
                t0 = time.perf_counter()
                title, description, tags, token_input, token_output, token_total = generate_metadata_gemini(api_key, model, image_path, prompt)
                t1 = time.perf_counter()
                duration_ms = int((t1 - t0) * 1000)
                gen_time, avg_time, longest_time, last_time = track_gemini_generation_time(duration_ms)
                if hasattr(self, "stats_section"):
                    self.stats_section.update_generation_times(gen_time, avg_time, longest_time, last_time)
                self.db.insert_api_token_stats(image_path, service, model, token_input, token_output, token_total)
                self.update_token_stats_ui()
                return title, description, tags
        elif service == "openai":
            from helpers.ai_helper.openai_helper import generate_metadata_openai, track_openai_generation_time
            def metadata_func(api_key, model, image_path, prompt=None):
                import time
                t0 = time.perf_counter()
                title, description, tags, error_message, token_input, token_output, token_total = generate_metadata_openai(api_key, model, image_path, prompt)
                t1 = time.perf_counter()
                duration_ms = int((t1 - t0) * 1000)
                gen_time, avg_time, longest_time, last_time = track_openai_generation_time(duration_ms)
                if hasattr(self, "stats_section"):
                    self.stats_section.update_generation_times(gen_time, avg_time, longest_time, last_time)
                self.db.insert_api_token_stats(image_path, service, model, token_input, token_output, token_total)
                self.update_token_stats_ui()
                if error_message:
                    self.show_ai_unsupported_dialog.emit(error_message)
                    return '', '', ''
                return title, description, tags
        else:
            print(f"[DEBUG] Unknown service: {service}")
            QMessageBox.warning(self, "API Service", f"Unknown service: {service}")
            self.table.progress_bar.setVisible(False)
            self.table.progress_bar.setValue(0)
            self.table.progress_bar.setFormat('')
            return

        self.generator_thread = ImageTeaGeneratorThread(
            api_key, model, rows, DB_PATH, row_map=row_map
        )
        self.generator_thread.generate_metadata_func = metadata_func
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
                status_item = table_widget.item(row, 8)
                if status_item and status_item.text().lower() == "processing":
                    filepath_item = table_widget.item(row, 1)
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
        self.table.refresh_table()
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
        self.table.refresh_table()

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
        self.update_token_stats_ui()
        QApplication.processEvents()

    def _on_generation_finished(self, errors):
        self.is_generating = False
        self._set_gen_btn_stop_state(False)
        self.table.progress_bar.setFormat('Done')
        self.table.progress_bar.setMaximum(1)
        self.table.progress_bar.setValue(1)
        QApplication.processEvents()
        self.table.refresh_table()
        self.update_token_stats_ui()
        if errors:
            print("[Gemini Errors]")
            for err in errors:
                print(err)
        else:
            print("[Gemini] Metadata generated for all files.")

    def update_token_stats_ui(self):
        if hasattr(self, "stats_section") and hasattr(self.stats_section, "update_token_stats"):
            token_input, token_output, token_total = self.db.get_token_stats_sum()
            self.stats_section.update_token_stats(token_input, token_output, token_total)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageTeaMainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())