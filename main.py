import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BASE_PATH
sys.path.insert(0, BASE_PATH)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QLabel
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
                if self.is_image_file(path) or self.is_video_file(path):
                    self.db.add_image(path, fname)
                    added += 1
        if added:
            refresh_table(self)

    def import_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images or Videos", "", "Images/Videos (*.jpg *.jpeg *.png *.bmp *.gif *.mp4 *.mpeg *.mov *.avi *.flv *.mpg *.webm *.wmv *.3gp *.3gpp)")
        for path in files:
            fname = os.path.basename(path)
            if self.is_image_file(path) or self.is_video_file(path):
                self.db.add_image(path, fname)
        if files:
            refresh_table(self)

    def batch_generate_metadata(self):
        if not self.api_key:
            QMessageBox.warning(self, "API Key", "Please set your Gemini API key first.")
            return
        rows = self.db.get_all_images()
        if not rows:
            QMessageBox.information(self, "No Images", "No images to process.")
            return
        self.table.progress_bar.setVisible(True)
        self.table.progress_bar.setMinimum(0)
        self.table.progress_bar.setMaximum(0)
        self.table.progress_bar.setFormat('Generating metadata...')
        QApplication.processEvents()
        thread = ImageTeaGeneratorThread(self.api_key, rows, DB_PATH)
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
            print("[Gemini] Metadata generated for all images.")

    def write_metadata_to_images(self):
        write_metadata_to_images(self.db, self.is_image_file, self.is_video_file)

    def delete_selected(self):
        delete_selected(self)

    def clear_all(self):
        clear_all(self)

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
