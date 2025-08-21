from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QScrollArea, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import os

class PropertiesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.setMinimumWidth(260)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.setAlignment(Qt.AlignTop)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("<b>Properties</b>")
        self.content_layout.addWidget(self.title_label)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.preview_label.setMinimumHeight(160)
        self.preview_label.setMaximumHeight(220)
        self.preview_label.setWordWrap(True)
        self.content_layout.addWidget(self.preview_label)

        self.fields = []
        self.labels = []
        self.label_widgets = []
        field_names = [
            "Filepath", "Filename", "Title", "Description", "Tags", "Status", "Original Filename",
            "Shutterstock Category", "Adobe Stock Category"
        ]
        for idx, label_text in enumerate(field_names):
            label = QLabel(f"<b>{label_text}:</b>")
            label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            value_label = QLabel("")
            value_label.setWordWrap(True)
            value_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_label.setStyleSheet("font-size: 8pt;")
            self.content_layout.addWidget(label)
            self.content_layout.addWidget(value_label)
            self._add_separator()
            self.fields.append(value_label)
            self.labels.append(label_text)
            self.label_widgets.append(label)
            setattr(self, f"{label_text.lower().replace(' ', '_')}_val", value_label)

        content.setLayout(self.content_layout)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        self.setLayout(outer_layout)

    def _add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedHeight(8)
        self.content_layout.addWidget(sep)

    def set_properties(self, row_data):
        if not row_data:
            self.preview_label.clear()
            for value_label in self.fields:
                value_label.setText("")
            if self.db:
                files = self.db.get_all_files()
                if files:
                    first_row = files[0]
                    title = first_row[3] if len(first_row) > 3 and first_row[3] is not None else ""
                    tags = first_row[5] if len(first_row) > 5 and first_row[5] is not None else ""
                    description = first_row[4] if len(first_row) > 4 and first_row[4] is not None else ""
                    title_length = len(title)
                    tag_count = len([t for t in tags.split(",") if t.strip()]) if tags else 0
                    desc_length = len(description)
                    row_data = [first_row[0]] + list(first_row[1:7]) + [first_row[7] if len(first_row) > 7 else ""] + [str(title_length), str(tag_count), str(desc_length)]
                    self.set_properties(row_data)
            return

        title = str(row_data[3]) if len(row_data) > 3 else ""
        tags = str(row_data[5]) if len(row_data) > 5 else ""
        description = str(row_data[4]) if len(row_data) > 4 else ""
        title_length = int(row_data[8]) if len(row_data) > 8 and str(row_data[8]).isdigit() else len(title)
        tag_count = int(row_data[9]) if len(row_data) > 9 and str(row_data[9]).isdigit() else len([t for t in tags.split(",") if t.strip()]) if tags else 0
        desc_length = len(description)

        label_texts = [
            "Filepath",
            "Filename",
            f"Title ({title_length})",
            f"Description ({desc_length})",
            f"Tags ({tag_count})",
            "Status",
            "Original Filename",
            "Shutterstock Category",
            "Adobe Stock Category"
        ]

        values = [
            str(row_data[1]) if len(row_data) > 1 else "",
            str(row_data[2]) if len(row_data) > 2 else "",
            title,
            description,
            tags,
            str(row_data[6]) if len(row_data) > 6 else "",
            str(row_data[7]) if len(row_data) > 7 else "",
            "",
            ""
        ]

        shutterstock_cat_text = ""
        adobe_cat_text = ""

        db = self.db
        file_id = row_data[0]
        if db is not None:
            try:
                category_mapping = db.get_category_mapping_for_file(file_id)
                shutterstock_map, adobe_map = db.get_category_maps()
                primary = None
                secondary = None
                for mapping in category_mapping:
                    if mapping['platform'] == 'shutterstock':
                        cat_name = str(mapping['category_name']).lower()
                        if cat_name.endswith('(primary)'):
                            primary = mapping['category_id']
                        elif cat_name.endswith('(secondary)'):
                            secondary = mapping['category_id']
                if primary and secondary:
                    shutterstock_cat_text = f"{shutterstock_map.get(str(primary), str(primary))}, {shutterstock_map.get(str(secondary), str(secondary))}"
                elif primary:
                    shutterstock_cat_text = shutterstock_map.get(str(primary), str(primary))
                elif secondary:
                    shutterstock_cat_text = shutterstock_map.get(str(secondary), str(secondary))
                adobe_cat_id = None
                for mapping in category_mapping:
                    if mapping['platform'] == 'adobe_stock':
                        adobe_cat_id = mapping['category_id']
                        break
                if adobe_cat_id:
                    adobe_cat_text = adobe_map.get(str(adobe_cat_id), str(adobe_cat_id))
            except Exception as e:
                print(f"Error loading category mapping: {e}")

        values[7] = shutterstock_cat_text
        values[8] = adobe_cat_text

        for label_widget, label_text in zip(self.label_widgets, label_texts):
            label_widget.setText(f"<b>{label_text}:</b>")

        for value_label, val in zip(self.fields, values):
            value_label.setText(val)

        filepath = values[0]
        self.preview_label.clear()
        if filepath and os.path.exists(filepath):
            ext = os.path.splitext(filepath)[1].lower()
            video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
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
                        preview_width = self.preview_label.width() if self.preview_label.width() > 0 else 220
                        pixmap = pixmap.scaled(preview_width, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.preview_label.setPixmap(pixmap)
                    else:
                        self.preview_label.setText("Cannot preview video")
                except Exception as e:
                    print(f"Video preview error: {e}")
                    self.preview_label.setText("Cannot preview video")
            else:
                pixmap = QPixmap(filepath)
                if not pixmap.isNull():
                    preview_width = self.preview_label.width() if self.preview_label.width() > 0 else 220
                    pixmap = pixmap.scaled(preview_width, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.preview_label.setPixmap(pixmap)
                else:
                    self.preview_label.setText("Cannot preview image")
        else:
            self.preview_label.setText("No preview")