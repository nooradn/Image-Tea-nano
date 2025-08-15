import sys
import os
from config import BASE_PATH
sys.path.insert(0, BASE_PATH)
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidgetItem,
    QFileDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import qtawesome as qta
from metadata_helper.metadata_operation import ImageTeaGeneratorThread
from metadata_helper.metadata_operation import write_metadata_to_images
from database.db_operation import ImageTeaDB, DB_PATH
from ui.setup_ui import setup_ui



# --- PySide6 GUI ---
class DragDropWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Drag and drop images or videos here")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px dashed #aaa; padding: 20px; font-size: 16px;")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls()]
            mainwin = self.window()
            if hasattr(mainwin, 'handle_dropped_files'):
                mainwin.handle_dropped_files(paths)

class ImageTeaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Tea (nano) Metadata Generator")
        self.setWindowIcon(qta.icon('fa5s.magic'))
        self.db = ImageTeaDB()
        self.api_key = self.db.get_api_key('gemini')
        setup_ui(self)
        self.refresh_table()

    def save_api_key(self):
        key = self.api_key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "API Key", "API key cannot be empty.")
            return
        self.db.set_api_key('gemini', key)
        self.api_key = key
        QMessageBox.information(self, "API Key", "API key saved.")

    def handle_dropped_files(self, paths):
        added = 0
        for path in paths:
            if os.path.isfile(path):
                fname = os.path.basename(path)
                if self.is_image_file(path) or self.is_video_file(path):
                    self.db.add_image(path, fname)
                    added += 1
        if added:
            self.refresh_table()

    def import_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images or Videos", "", "Images/Videos (*.jpg *.jpeg *.png *.bmp *.gif *.mp4 *.mpeg *.mov *.avi *.flv *.mpg *.webm *.wmv *.3gp *.3gpp)")
        for path in files:
            fname = os.path.basename(path)
            if self.is_image_file(path) or self.is_video_file(path):
                self.db.add_image(path, fname)
        if files:
            self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        for row in self.db.get_all_images():
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val is not None else "")
                if col == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col, item)

    def batch_generate_metadata(self):
        if not self.api_key:
            QMessageBox.warning(self, "API Key", "Please set your Gemini API key first.")
            return
        rows = self.db.get_all_images()
        if not rows:
            QMessageBox.information(self, "No Images", "No images to process.")
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate mode (marquee)
        self.progress_bar.setFormat('Generating metadata...')
        QApplication.processEvents()
        thread = ImageTeaGeneratorThread(self.api_key, rows, DB_PATH)
        thread.progress.connect(self._on_progress_update)
        thread.finished.connect(self._on_generation_finished)
        thread.start()
        self.thread = thread

    def _on_progress_update(self, current, total):
        # Optionally, could show percent if desired
        pass

    def _on_generation_finished(self, errors):
        self.progress_bar.setFormat('Done')
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(1)
        QApplication.processEvents()
        self.refresh_table()
        self.progress_bar.setVisible(False)
        if errors:
            print("[Gemini Errors]")
            for err in errors:
                print(err)
        else:
            print("[Gemini] Metadata generated for all images.")

    def write_metadata_to_images(self):
        write_metadata_to_images(self.db, self.is_image_file, self.is_video_file)

    def delete_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Delete", "No rows selected.")
            return
        for idx in selected:
            filepath = self.table.item(idx.row(), 1).text()
            self.db.delete_image(filepath)
        self.refresh_table()

    def clear_all(self):
        if QMessageBox.question(self, "Clear All", "Are you sure you want to clear all images?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.clear_images()
            self.refresh_table()

    @staticmethod
    def is_image_file(path):
        ext = os.path.splitext(path)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

    @staticmethod
    def is_video_file(path):
        ext = os.path.splitext(path)[1].lower()
        return ext in [
            '.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp'
        ]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageTeaMainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())
