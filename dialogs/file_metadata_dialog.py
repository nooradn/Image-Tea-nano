from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QHBoxLayout, QFormLayout, QSpacerItem, QSizePolicy, QToolTip
from PySide6.QtGui import QPixmap, QImage, QGuiApplication
from PySide6.QtCore import Qt, QTimer
import qtawesome as qta
import os

class FileMetadataDialog(QDialog):
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Metadata")
        self.setFixedWidth(400)
        self.filepath = filepath
        self.db = getattr(parent, 'db', None)
        file_data = None
        if self.db:
            for row in self.db.get_all_files():
                if row[1] == filepath:
                    file_data = row
                    break
        if not file_data:
            file_data = (None, filepath, "", "", "", "", "", "")

        _, filepath, filename, title, description, tags, status, original_filename = file_data
        title = title or ""
        description = description or ""
        tags = tags or ""
        status = status or ""
        filename = filename or ""
        original_filename = original_filename or ""

        layout = QVBoxLayout(self)

        # Image/video preview
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        ext = os.path.splitext(filepath)[1].lower()
        if os.path.exists(filepath):
            if ext in video_exts:
                try:
                    import cv2
                    cap = cv2.VideoCapture(filepath)
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = frame_rgb.shape
                        bytes_per_line = ch * w
                        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimg)
                        pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        img_label.setPixmap(pixmap)
                    else:
                        img_label.setText("Cannot preview video")
                except Exception as e:
                    print(f"Video preview error: {e}")
                    img_label.setText("Cannot preview video")
            else:
                pixmap = QPixmap(filepath)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    img_label.setPixmap(pixmap)
                else:
                    img_label.setText("Cannot preview image")
        else:
            img_label.setText("Image/Video not found")
        layout.addWidget(img_label)

        form = QFormLayout()

        # Title row with copy button
        title_row = QHBoxLayout()
        self.title_edit = QLineEdit(title)
        title_row.addWidget(self.title_edit)
        copy_title_btn = QPushButton()
        copy_title_btn.setIcon(qta.icon("fa5s.copy"))
        copy_title_btn.setToolTip("Copy Title")
        copy_title_btn.setFlat(True)
        copy_title_btn.setFixedWidth(28)
        copy_title_btn.clicked.connect(lambda: self.copy_with_tooltip(self.title_edit.text(), copy_title_btn, "Title"))
        title_row.addWidget(copy_title_btn)
        form.addRow("Title:", title_row)

        # Description row with copy button
        desc_row = QHBoxLayout()
        self.description_edit = QTextEdit(description)
        self.description_edit.setFixedHeight(60)
        self.description_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        desc_row.addWidget(self.description_edit)
        copy_desc_btn = QPushButton()
        copy_desc_btn.setIcon(qta.icon("fa5s.copy"))
        copy_desc_btn.setToolTip("Copy Description")
        copy_desc_btn.setFlat(True)
        copy_desc_btn.setFixedWidth(28)
        copy_desc_btn.clicked.connect(lambda: self.copy_with_tooltip(self.description_edit.toPlainText(), copy_desc_btn, "Description"))
        desc_row.addWidget(copy_desc_btn)
        form.addRow("Description:", desc_row)

        # Tags row with copy button
        tags_row = QHBoxLayout()
        self.tags_edit = QLineEdit(tags)
        tags_row.addWidget(self.tags_edit)
        copy_tags_btn = QPushButton()
        copy_tags_btn.setIcon(qta.icon("fa5s.copy"))
        copy_tags_btn.setToolTip("Copy Tags")
        copy_tags_btn.setFlat(True)
        copy_tags_btn.setFixedWidth(28)
        copy_tags_btn.clicked.connect(lambda: self.copy_with_tooltip(self.tags_edit.text(), copy_tags_btn, "Tags"))
        tags_row.addWidget(copy_tags_btn)
        form.addRow("Tags:", tags_row)

        title_length = len(title)
        tag_count = len([t for t in tags.split(",") if t.strip()]) if tags else 0

        title_length_label = QLabel(str(title_length))
        form.addRow("Title Length:", title_length_label)

        tag_count_label = QLabel(str(tag_count))
        form.addRow("Tag Count:", tag_count_label)

        status_label = QLabel(status)
        status_label.setWordWrap(True)
        form.addRow("Status:", status_label)

        # Filename row with copy button
        filename_row = QHBoxLayout()
        filename_label = QLabel(filename)
        filename_label.setWordWrap(True)
        filename_row.addWidget(filename_label)
        copy_filename_btn = QPushButton()
        copy_filename_btn.setIcon(qta.icon("fa5s.copy"))
        copy_filename_btn.setToolTip("Copy Filename")
        copy_filename_btn.setFlat(True)
        copy_filename_btn.setFixedWidth(28)
        copy_filename_btn.clicked.connect(lambda: self.copy_with_tooltip(filename, copy_filename_btn, "Filename"))
        filename_row.addWidget(copy_filename_btn)
        form.addRow("Filename:", filename_row)

        orig_filename_label = QLabel(original_filename)
        orig_filename_label.setWordWrap(True)
        form.addRow("Original Filename:", orig_filename_label)

        layout.addLayout(form)

        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        close_btn = QPushButton("Close")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        close_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.save_metadata)

    def copy_with_tooltip(self, text, btn, label):
        QGuiApplication.clipboard().setText(text)
        def shorten(val, maxlen=60):
            val = val.strip()
            if len(val) > maxlen:
                return val[:maxlen-3] + "..."
            return val
        if label == "Tags":
            value = shorten(text)
            tooltip = f"Copied: {value}" if value else "Copied: (empty)"
        elif label == "Filename":
            tooltip = f"Copied: {shorten(text)}" if text else "Copied: (empty)"
        elif label == "Title":
            tooltip = f"Copied: {shorten(text)}" if text else "Copied: (empty)"
        elif label == "Description":
            tooltip = f"Copied: {shorten(text)}" if text else "Copied: (empty)"
        else:
            tooltip = "Copied"
        old_tooltip = btn.toolTip()
        btn.setToolTip(tooltip)
        # Show tooltip at the button position
        pos = btn.mapToGlobal(btn.rect().center())
        QToolTip.showText(pos, tooltip, btn)
        QTimer.singleShot(1200, lambda: btn.setToolTip(old_tooltip))

    def save_metadata(self):
        if not self.db:
            print("No database connection for saving metadata.")
            return
        title = self.title_edit.text()
        description = self.description_edit.toPlainText()
        tags = self.tags_edit.text()
        self.db.update_metadata(self.filepath, title, description, tags)
        self.accept()
