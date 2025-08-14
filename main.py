import sys
import os
import sqlite3
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QLabel, QLineEdit, QAbstractItemView, QHeaderView, QInputDialog
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
import qtawesome as qta
import google.genai as genai
from google.genai import types
import pyexiv2
# --- Write metadata using pyexiv2 ---
def write_metadata_pyexiv2(file_path, title, description, tag_list):
    try:
        metadata = pyexiv2.Image(file_path)
        metadata.modify_xmp({
            'Xmp.dc.title': title,
            'Xmp.dc.description': description,
            'Xmp.dc.subject': tag_list
        })
        metadata.close()
        print(f"[pyexiv2] Metadata written to {file_path}")
    except Exception as e:
        print(f"[pyexiv2 ERROR] {file_path}: {e}")

DB_PATH = 'metagen.db'

# --- Database Layer ---
class MetaGenDB:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT UNIQUE,
            api_key TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT UNIQUE,
            filename TEXT,
            title TEXT,
            description TEXT,
            tags TEXT
        )''')
        self.conn.commit()

    def set_api_key(self, service, api_key):
        c = self.conn.cursor()
        c.execute('INSERT OR REPLACE INTO api_keys (service, api_key) VALUES (?, ?)', (service, api_key))
        self.conn.commit()

    def get_api_key(self, service):
        c = self.conn.cursor()
        c.execute('SELECT api_key FROM api_keys WHERE service=?', (service,))
        row = c.fetchone()
        return row[0] if row else None

    def add_image(self, filepath, filename, title=None, description=None, tags=None):
        c = self.conn.cursor()
        c.execute('''INSERT OR IGNORE INTO images (filepath, filename, title, description, tags) VALUES (?, ?, ?, ?, ?)''',
                  (filepath, filename, title, description, tags))
        self.conn.commit()

    def update_metadata(self, filepath, title, description, tags):
        c = self.conn.cursor()
        c.execute('''UPDATE images SET title=?, description=?, tags=? WHERE filepath=?''',
                  (title, description, tags, filepath))
        self.conn.commit()

    def delete_image(self, filepath):
        c = self.conn.cursor()
        c.execute('DELETE FROM images WHERE filepath=?', (filepath,))
        self.conn.commit()

    def clear_images(self):
        c = self.conn.cursor()
        c.execute('DELETE FROM images')
        self.conn.commit()

    def get_all_images(self):
        c = self.conn.cursor()
        c.execute('SELECT id, filepath, filename, title, description, tags FROM images')
        return c.fetchall()

# --- Gemini API Wrapper (Strict JSON Parsing) ---
def generate_metadata_gemini(api_key, image_path, prompt=None):
    try:
        client = genai.Client(api_key=api_key)
        ext = os.path.splitext(image_path)[1].lower()
        is_video = ext in ['.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp']
        if not prompt:
            prompt = (
                "Create high-quality image or video metadata following these guidelines:\n\n"
                "1. Title/Description Requirements:\n"
                "- Length: Min 8 - Max Length must be exactly 80 characters, no more than that since its CRITICAL\n"
                "- Write as a natural, descriptive sentence/phrase (not keyword list)\n"
                "- Cover Who, What, When, Where, Why aspects where relevant\n"
                "- Capture mood, emotion, and visual impact\n"
                "- Must be unique and detailed\n"
                "- Include visual style/technique if notable\n"
                "- Be factual and objective\n\n"
                "2. Description Requirements:\n"
                "- Provide a detailed description of the image or video, different from the title\n"
                "- Use a full sentence or two, not just keywords\n"
                "- Must be unique and informative\n\n"
                "3. Keywords Requirements:\n"
                "- You must provide exactly 15 keywords and not less since its CRITICAL\n"
                "- Keywords must be precise and directly relevant\n"
                "- Include both literal and conceptual terms\n"
                "- Cover key visual elements, themes, emotions, techniques\n"
                "- Avoid overly generic or irrelevant terms\n"
                "- Use industry-standard terminology\n"
                "- Separate keywords with commas\n\n"
                "4. General Guidelines:\n"
                "- Use only English language\n"
                "- Be respectful and accurate with identities\n"
                "- No personally identifiable information\n"
                "- No special characters except commas between keywords\n"
                "- Focus on commercial value and searchability\n\n"
                "5. Strict Don'ts:\n"
                "- No brand names, trademarks, or company names\n"
                "- No celebrity names or personal names\n"
                "- No specific event references or newsworthy content\n"
                "- No copyrighted elements or protected designs\n"
                "- No editorial content or journalistic references\n"
                "- No offensive, controversial, or sensitive terms\n"
                "- No location-specific landmarks unless generic\n"
                "- No date-specific references or temporal events\n"
                "- No product names or model numbers\n"
                "- No camera/tech specifications in metadata\n\n"
                "RESPONSE FORMAT (Strict JSON with ALL fields required):\n"
                "{\n"
                '  "title": "Your descriptive title here",\n'
                '  "description": "A detailed description of the image or video.",\n'
                '  "tags": ["tag1", "tag2", "tag3"]\n'
                "}\n"
                "\nVALIDATION RULES:\n"
                "1. Use DOUBLE quotes for all strings\n"
                "2. All fields (title, description, tags) are required\n"
                "3. Response must be valid JSON\n"
            )
        import time
        if is_video:
            # Official Gemini API for video: upload file, then use in generate_content
            myfile = client.files.upload(file=image_path)
            # Polling status ACTIVE
            file_id = myfile.name if hasattr(myfile, 'name') else getattr(myfile, 'id', None)
            status = None
            for _ in range(20):  # max 20x polling (sekitar 10 detik)
                fileinfo = client.files.get(name=file_id)
                status = getattr(fileinfo, 'state', None) or getattr(fileinfo, 'status', None)
                if status == 'ACTIVE':
                    break
                time.sleep(0.5)
            if status != 'ACTIVE':
                print(f"[Gemini ERROR] File {file_id} not ACTIVE after upload, status: {status}")
                return '', '', ''
            contents = [myfile, prompt]
        else:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            contents = [types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'), prompt]
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        print("[Gemini RAW JSON Result]")
        print(response)
        # Extract JSON from Gemini response
        text = None
        if hasattr(response, 'candidates') and response.candidates:
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                text = str(response)
        elif hasattr(response, 'text'):
            text = response.text
        elif isinstance(response, dict) and 'text' in response:
            text = response['text']
        else:
            text = str(response)
        # Try to parse JSON, handle code block markdown
        try:
            if text.strip().startswith('```'):
                text = text.strip().lstrip('`').lstrip('json').strip()
                if text.endswith('```'):
                    text = text[:text.rfind('```')].strip()
            meta = json.loads(text)
            title = meta.get('title', '')
            description = meta.get('description', '')
            tags = ', '.join(meta.get('tags', [])) if isinstance(meta.get('tags'), list) else str(meta.get('tags', ''))
        except Exception as e:
            print(f"[Gemini JSON PARSE ERROR] {e}")
            title = description = tags = ''
        return title, description, tags
    except Exception as e:
        print(f"[Gemini ERROR] {e}")
        return '', '', ''

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

class MetaGenMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MetaGen - Image Metadata Generator")
        self.setWindowIcon(qta.icon('fa5s.magic'))
        self.db = MetaGenDB()
        self.api_key = self.db.get_api_key('gemini')
        self._setup_ui()
        self.refresh_table()

    def _setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout()
        # API Key controls
        api_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter Gemini API Key")
        if self.api_key:
            self.api_key_edit.setText(self.api_key)
        api_save_btn = QPushButton(qta.icon('fa5s.save'), "Save API Key")
        api_save_btn.clicked.connect(self.save_api_key)
        # Icon label fix
        icon_label = QLabel(" ")
        icon = qta.icon('fa5s.key')
        pixmap = icon.pixmap(16, 16)
        icon_label.setPixmap(pixmap)
        api_layout.addWidget(icon_label)
        api_layout.addWidget(QLabel("Gemini API Key:"))
        api_layout.addWidget(self.api_key_edit)
        api_layout.addWidget(api_save_btn)
        layout.addLayout(api_layout)
        # Drag and drop
        self.dnd_widget = DragDropWidget(self)
        layout.addWidget(self.dnd_widget)
        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Filepath", "Filename", "Title", "Description", "Tags"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        # Buttons
        btn_layout = QHBoxLayout()
        import_btn = QPushButton(qta.icon('fa5s.folder-open'), "Import Images")
        import_btn.clicked.connect(self.import_images)
        gen_btn = QPushButton(qta.icon('fa5s.magic'), "Generate Metadata (Batch)")
        gen_btn.clicked.connect(self.batch_generate_metadata)
        write_btn = QPushButton(qta.icon('fa5s.save'), "Write Metadata to Images")
        write_btn.clicked.connect(self.write_metadata_to_images)
        del_btn = QPushButton(qta.icon('fa5s.trash'), "Delete Selected")
        del_btn.clicked.connect(self.delete_selected)
        clear_btn = QPushButton(qta.icon('fa5s.broom'), "Clear All")
        clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(gen_btn)
        btn_layout.addWidget(write_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
        central.setLayout(layout)
        self.setCentralWidget(central)

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
        errors = []
        for id_, filepath, filename, title, description, tags in rows:
            if not title:
                t, d, tg = generate_metadata_gemini(self.api_key, filepath)
                if not t:
                    errors.append(f"{filename}: Failed to generate metadata")
                else:
                    self.db.update_metadata(filepath, t, d, tg)
        self.refresh_table()
        if errors:
            print("[Gemini Errors]")
            for err in errors:
                print(err)
        else:
            print("[Gemini] Metadata generated for all images.")

    def write_metadata_to_images(self):
        rows = self.db.get_all_images()
        errors = []
        for id_, filepath, filename, title, description, tags in rows:
            if self.is_image_file(filepath):
                if title or description or tags:
                    try:
                        tag_list = [t.strip() for t in tags.split(',')] if tags else []
                        write_metadata_pyexiv2(filepath, title or '', description or '', tag_list)
                    except Exception as e:
                        errors.append(f"{filename}: {e}")
            elif self.is_video_file(filepath):
                # Tidak perlu menulis metadata ke video, hanya simpan di DB
                continue
        if errors:
            print("[Write Metadata Errors]")
            for err in errors:
                print(err)
        else:
            print("[Write Metadata] Metadata written to all images.")

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
    window = MetaGenMainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())
