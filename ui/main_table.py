from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QMessageBox, QAbstractItemView, QHeaderView,
    QVBoxLayout, QWidget, QProgressBar, QMenu, QLabel, QHBoxLayout, QLineEdit,
    QPushButton, QToolTip, QTabWidget, QScrollArea, QFrame, QLayout
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QRect, QSize
from PySide6.QtGui import QColor, QBrush, QAction, QGuiApplication, QPixmap
from dialogs.file_metadata_dialog import FileMetadataDialog
from dialogs.donation_dialog import DonateDialog, is_donation_optout_today
import qtawesome as qta
import os

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self._itemList = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing if spacing >= 0 else 0)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._itemList.append(item)

    def count(self):
        return len(self._itemList)

    def itemAt(self, index):
        if 0 <= index < len(self._itemList):
            return self._itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._itemList):
            return self._itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._itemList:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        right = rect.right()
        for item in self._itemList:
            widget = item.widget()
            if widget and not widget.isVisible():
                continue
            spaceX = self.spacing()
            spaceY = self.spacing()
            itemSize = item.sizeHint()
            nextX = x + itemSize.width() + spaceX
            if nextX - spaceX > right and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + itemSize.width() + spaceX
                lineHeight = 0
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), itemSize))
            x = nextX
            lineHeight = max(lineHeight, itemSize.height())
        return y + lineHeight - rect.y()

class GridManager:
    def __init__(self):
        self.image_items = []
        self.image_size = 150
        self.grid_spacing = 10
        self.active_image = None
        self._widget_cache = {}  # key: filepath, value: widget
        self._pixmap_cache = {}  # key: filepath, value: QPixmap

    def _clear_grid(self, grid_widget):
        for item in self.image_items:
            if item:
                try:
                    item.deleteLater()
                except Exception as e:
                    print(f"Error deleting widget: {e}")
        self.image_items.clear()

    def _create_image_widget(self, file_info):
        filepath = file_info['filepath']
        filename = file_info['filename']
        extension = file_info['extension']
        cache_key = filepath

        if cache_key in self._widget_cache:
            widget = self._widget_cache[cache_key]
            return widget

        container = QWidget()
        item_width = self.image_size + 10
        container.setFixedWidth(item_width)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setFixedSize(self.image_size, self.image_size)
        image_label.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                padding: 2px;
            }
            QLabel:hover {
                border: 2px solid rgba(88, 165, 0, 0.3);
                background-color: rgba(88, 165, 0, 0.05);
            }
        """)
        image_label.setAttribute(Qt.WA_Hover, True)
        image_label.setCursor(Qt.PointingHandCursor)
        self._set_image(image_label, filepath)
        MAX_NAME_LENGTH = 18
        if len(filename) > MAX_NAME_LENGTH:
            display_name = f"{filename[:MAX_NAME_LENGTH-3]}...{extension}"
        else:
            display_name = f"{filename}{extension}"
        text_label = QLabel(display_name)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(False)
        text_label.setFixedWidth(self.image_size)
        text_label.setStyleSheet("font-size: 9pt;")
        text_label.setToolTip(f"{filename}{extension}")
        layout.addWidget(image_label)
        layout.addWidget(text_label)
        container.setProperty("file_info", file_info)
        container.mousePressEvent = lambda event: self._handle_image_click(container, event)
        image_label.mousePressEvent = lambda event: self._handle_image_click(container, event)
        self._widget_cache[cache_key] = container
        return container

    def _set_image(self, label, image_path):
        if image_path in self._pixmap_cache:
            pixmap = self._pixmap_cache[image_path]
            if pixmap:
                label.setPixmap(pixmap)
            else:
                label.setText("Cannot load\nimage")
            return
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.image_size, self.image_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self._pixmap_cache[image_path] = pixmap
                label.setPixmap(pixmap)
            else:
                self._pixmap_cache[image_path] = None
                label.setText("Cannot load\nimage")
                print(f"Failed to load image: {image_path}")
        except Exception as e:
            self._pixmap_cache[image_path] = None
            label.setText("Error")
            print(f"Error loading image: {image_path} - {e}")

    def _update_active_image(self, new_active_widget):
        try:
            if self.active_image:
                for child in self.active_image.children():
                    if isinstance(child, QLabel) and child.objectName() != "filename_label":
                        child.setStyleSheet("""
                            QLabel {
                                border: 2px solid rgba(0, 0, 0, 0.1);
                                border-radius: 4px;
                                padding: 2px;
                            }
                            QLabel:hover {
                                border: 2px solid rgba(88, 165, 0, 0.3);
                                background-color: rgba(88, 165, 0, 0.05);
                            }
                        """)
                        break
            self.active_image = new_active_widget
            if self.active_image:
                for child in self.active_image.children():
                    if isinstance(child, QLabel) and child.objectName() != "filename_label":
                        child.setStyleSheet("""
                            QLabel {
                                border: 2px solid rgba(88, 165, 0, 0.3);
                                border-radius: 4px;
                                padding: 2px;
                                background-color: rgba(88, 165, 0, 0.20);
                            }
                            QLabel:hover {
                                border: 2px solid rgba(88, 165, 0, 0.5);
                                background-color: rgba(88, 165, 0, 0.25);
                            }
                        """)
                        break
        except Exception as e:
            print(f"Error updating active image styling: {e}")

    def _handle_image_click(self, widget, event):
        try:
            file_info = widget.property("file_info")
            if not file_info:
                return
            self._update_active_image(widget)
            parent_widget = widget.parent()
            while parent_widget and not hasattr(parent_widget, '_callback_function'):
                parent_widget = parent_widget.parent()
            if parent_widget and hasattr(parent_widget, '_callback_function'):
                callback_function = parent_widget._callback_function
                if callback_function:
                    callback_function(0, 0, file_info)
        except Exception as e:
            print(f"Error handling grid image click: {e}")

    def setup_grid_click_handler(self, grid_widget, callback_function):
        if not grid_widget:
            print("Grid widget not provided, can't set up click handler")
            return
        grid_widget._callback_function = callback_function

class ImageTableWidget(QWidget):
    stats_changed = Signal(int, int, int, int, int)
    data_refreshed = Signal()

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self._properties_widget = getattr(parent, "properties_widget", None)
        self._main_window = parent
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget(self)
        self.layout.addWidget(self.tab_widget)
        self.table_tab = QWidget()
        self.table_tab_layout = QVBoxLayout(self.table_tab)
        self.table_tab_layout.setContentsMargins(0, 0, 0, 0)
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.setClearButtonEnabled(False)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_icon_btn = QPushButton(self)
        search_icon_btn.setIcon(qta.icon("fa6s.magnifying-glass"))
        search_icon_btn.setFlat(True)
        search_icon_btn.setFocusPolicy(Qt.NoFocus)
        search_icon_btn.setEnabled(False)
        search_icon_btn.setFixedWidth(28)
        paste_btn = QPushButton(self)
        paste_btn.setIcon(qta.icon("fa6s.clipboard"))
        paste_btn.setFlat(True)
        paste_btn.setFocusPolicy(Qt.NoFocus)
        paste_btn.setFixedWidth(28)
        paste_btn.setToolTip("Paste text from clipboard to search field")
        paste_btn.clicked.connect(self._on_paste_clicked)
        clear_btn = QPushButton(self)
        clear_btn.setIcon(qta.icon("fa6s.xmark"))
        clear_btn.setFlat(True)
        clear_btn.setFocusPolicy(Qt.NoFocus)
        clear_btn.setFixedWidth(28)
        clear_btn.setToolTip("Clear the search field")
        clear_btn.clicked.connect(self._on_clear_search)
        search_layout.addWidget(search_icon_btn)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(paste_btn)
        search_layout.addWidget(clear_btn)
        self.table_tab_layout.addLayout(search_layout)
        self.table = QTableWidget(0, 9, self)
        self.table.setHorizontalHeaderLabels([
            "", "Filepath", "Filename", "Title", "Description", "Tags", "Title Length", "Tag Count", "Status"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for col in range(0, 9):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table_tab_layout.addWidget(self.table)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('')
        self.progress_bar.setVisible(True)
        self.progress_bar.setToolTip("Shows progress for batch operations")
        self.table_tab_layout.addWidget(self.progress_bar)
        self.tab_widget.addTab(self.table_tab, "Table")
        self.thumbnail_tab = QWidget()
        self.thumbnail_tab_layout = QVBoxLayout(self.thumbnail_tab)
        self.thumbnail_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.thumbnail_scroll = QScrollArea(self.thumbnail_tab)
        self.thumbnail_scroll.setWidgetResizable(True)
        self.thumbnail_scroll.setFrameShape(QFrame.NoFrame)
        self.thumbnail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.thumbnail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.thumbnail_tab_layout.addWidget(self.thumbnail_scroll)
        self.thumbnail_content = QWidget()
        self.thumbnail_scroll.setWidget(self.thumbnail_content)
        self.thumbnail_flow = FlowLayout(margin=10, spacing=10)
        self.thumbnail_content.setLayout(self.thumbnail_flow)
        self.tab_widget.addTab(self.thumbnail_tab, "Thumbnail")
        self._donation_dialog_shown = False
        self.table.selectionModel().selectionChanged.connect(self._emit_stats)
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._all_rows_cache = []
        self.grid_manager = GridManager()
        self.grid_manager.setup_grid_click_handler(self.thumbnail_content, self._on_thumbnail_clicked)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.refresh_table()

    def _on_tab_changed(self, idx):
        if self.tab_widget.tabText(idx) == "Thumbnail":
            self.refresh_thumbnail_grid()

    def _on_paste_clicked(self):
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text()
        self.search_edit.setText(text)

    def _on_clear_search(self):
        self.search_edit.clear()

    def _on_search_text_changed(self, text):
        self._filter_table(text)
        if self.tab_widget.currentIndex() == 1:
            self.refresh_thumbnail_grid()

    def _filter_table(self, text):
        text = text.strip().lower()
        # Always refresh cache if search is empty, so cache is always up-to-date
        if not text:
            self._all_rows_cache = list(self.db.get_all_files())
        if not self._all_rows_cache:
            self._all_rows_cache = list(self.db.get_all_files())
        self.table.setRowCount(0)
        for row in self._all_rows_cache:
            if not text or self._row_matches_search(row, text):
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Unchecked)
                checkbox_item.setData(Qt.UserRole, row[0])
                self.table.setItem(row_idx, 0, checkbox_item)
                display_values = list(row[1:7])
                if len(display_values) > 0:
                    short_fp = self._shorten_filepath(display_values[0])
                    fp_item = QTableWidgetItem(short_fp)
                    fp_item.setData(Qt.UserRole, display_values[0])
                    self.table.setItem(row_idx, 1, fp_item)
                    for col, val in enumerate(display_values[1:], start=2):
                        item = QTableWidgetItem(str(val) if val is not None else "")
                        if col == 2:
                            item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row_idx, col, item)
                title_val = row[3] if len(row) > 3 and row[3] is not None else ""
                title_len = len(title_val)
                title_len_item = QTableWidgetItem(str(title_len))
                title_len_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 6, title_len_item)
                tags_val = row[5] if len(row) > 5 and row[5] is not None else ""
                tag_count = len([t for t in tags_val.split(",") if t.strip()]) if tags_val else 0
                tag_count_item = QTableWidgetItem(str(tag_count))
                tag_count_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 7, tag_count_item)
                status_val = row[6] if len(row) > 6 and row[6] is not None else ""
                status_item = QTableWidgetItem(str(status_val))
                status_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 8, status_item)
                color = self._status_color(status_val)
                for col in range(self.table.columnCount()):
                    item = self.table.item(row_idx, col)
                    if item:
                        item.setBackground(QBrush(color))
        self._emit_stats()

    def _row_matches_search(self, row, text):
        for value in row[1:6]:
            if value and text in str(value).lower():
                return True
        return False

    def _shorten_filepath(self, path):
        if not path:
            return ""
        norm_path = os.path.normpath(path)
        parts = norm_path.split(os.sep)
        if len(parts) >= 2:
            drive = parts[0]
            last_dir = parts[-2]
            filename = parts[-1]
            last10 = filename[-10:] if len(filename) > 10 else filename
            return f"{drive}{os.sep}...{os.sep}{last_dir}{os.sep}...{last10}"
        elif len(parts) == 1:
            filename = parts[0]
            last10 = filename[-10:] if len(filename) > 10 else filename
            return f"...{os.sep}{last10}"
        return path

    def _show_context_menu(self, pos: QPoint):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self)
        edit_icon = qta.icon("fa6s.pen-to-square")
        edit_action = QAction(edit_icon, "Edit metadata", self)
        edit_action.triggered.connect(lambda: self._open_metadata_dialog(index.row()))
        menu.addAction(edit_action)

        row_idx = index.row()
        filename_item = self.table.item(row_idx, 2)
        title_item = self.table.item(row_idx, 3)
        desc_item = self.table.item(row_idx, 4)
        tags_item = self.table.item(row_idx, 5)

        copy_filename_action = QAction(qta.icon("fa6s.copy"), "Copy Filename", self)
        copy_filename_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(filename_item.text() if filename_item else "", "Filename", pos))
        menu.addAction(copy_filename_action)

        copy_title_action = QAction(qta.icon("fa6s.copy"), "Copy Title", self)
        copy_title_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(title_item.text() if title_item else "", "Title", pos))
        menu.addAction(copy_title_action)

        copy_desc_action = QAction(qta.icon("fa6s.copy"), "Copy Description", self)
        copy_desc_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(desc_item.text() if desc_item else "", "Description", pos))
        menu.addAction(copy_desc_action)

        copy_tags_action = QAction(qta.icon("fa6s.copy"), "Copy Keyword", self)
        copy_tags_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(tags_item.text() if tags_item else "", "Keyword", pos))
        menu.addAction(copy_tags_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _copy_to_clipboard_with_tooltip(self, text, label, pos):
        QGuiApplication.clipboard().setText(text)
        def shorten(val, maxlen=60):
            val = val.strip()
            if len(val) > maxlen:
                return val[:maxlen-3] + "..."
            return val
        value = shorten(text)
        tooltip = f"Copied {label}: {value}" if value else f"Copied {label}: (empty)"
        global_pos = self.table.viewport().mapToGlobal(pos)
        QToolTip.showText(global_pos, tooltip, self.table.viewport())
        QTimer.singleShot(1200, QToolTip.hideText)

    def _copy_to_clipboard(self, text):
        QGuiApplication.clipboard().setText(text)

    def _on_cell_double_clicked(self, row, column):
        self._open_metadata_dialog(row)

    def _open_metadata_dialog(self, row):
        filepath_item = self.table.item(row, 1)
        if not filepath_item:
            return
        filepath = filepath_item.data(Qt.UserRole)
        if not filepath:
            filepath = filepath_item.text()
        parent_for_dialog = self._main_window if self._main_window is not None else self
        dialog = FileMetadataDialog(filepath, parent=parent_for_dialog)
        dialog.exec()

    def _status_color(self, status):
        if status == "processing":
            return QColor(243, 200, 24, int(0.3 * 255))
        elif status == "success":
            return QColor(113, 204, 0, int(0.3 * 255))
        elif status == "failed":
            return QColor(255, 0, 0, int(0.15 * 255))
        elif status == "stopping":
            return QColor(255, 140, 0, int(0.18 * 255))
        elif status == "stopped":
            return QColor(200, 40, 40, int(0.18 * 255))
        return QColor(255, 255, 255, 0)

    def set_row_status_color(self, row_idx, status):
        color = self._status_color(status)
        for col in range(self.table.columnCount()):
            item = self.table.item(row_idx, col)
            if item:
                item.setBackground(QBrush(color))
        status_col = 8
        status_item = self.table.item(row_idx, status_col)
        if status_item:
            status_item.setText(status.capitalize())

    def update_row_data(self, row_idx, row_data):
        display_values = list(row_data[1:7])
        if len(display_values) > 0:
            display_values[0] = self._shorten_filepath(display_values[0])
        for col, val in enumerate(display_values):
            item = self.table.item(row_idx, col + 1)
            if item:
                item.setText(str(val) if val is not None else "")
        title_val = row_data[3] if len(row_data) > 3 and row_data[3] is not None else ""
        title_len = len(title_val)
        title_len_item = self.table.item(row_idx, 6)
        if title_len_item:
            title_len_item.setText(str(title_len))
        tags_val = row_data[5] if len(row_data) > 5 and row_data[5] is not None else ""
        tag_count = len([t for t in tags_val.split(",") if t.strip()]) if tags_val else 0
        tag_count_item = self.table.item(row_idx, 7)
        if tag_count_item:
            tag_count_item.setText(str(tag_count))
        status_val = row_data[6] if len(row_data) > 6 and row_data[6] is not None else ""
        status_item = self.table.item(row_idx, 8)
        if status_item:
            status_item.setText(str(status_val))

    def refresh_table(self):
        self._all_rows_cache = list(self.db.get_all_files())
        self._filter_table(self.search_edit.text())

        total_files = self.table.rowCount()
        if total_files >= 100:
            if not self._donation_dialog_shown and not is_donation_optout_today():
                self._donation_dialog_shown = True
                dialog = DonateDialog(self, show_not_today=True)
                dialog.setWindowTitle("Support the Development")
                label = dialog.findChild(QLabel)
                if label:
                    label.setText(
                        "Thank you for trusting Image Tea for your metadata needs!\n\n"
                        "You're awesome!\n\n"
                        "Image Tea is possible thanks to the support of users like you.\n"
                        "If you really love using Image Tea to generate metadata,\nconsider supporting its development!"
                    )
                dialog.exec()
        else:
            self._donation_dialog_shown = False
        self.data_refreshed.emit()
        if self.tab_widget.currentIndex() == 1:
            self.refresh_thumbnail_grid()

    def refresh_thumbnail_grid(self):
        files = []
        text = self.search_edit.text().strip().lower()
        if not text:
            files = list(self.db.get_all_files())
        else:
            files = [row for row in self._all_rows_cache if self._row_matches_search(row, text)]
        files_data = []
        for row in files:
            file_info = {
                'filepath': row[1],
                'filename': row[2],
                'extension': os.path.splitext(row[2])[1]
            }
            files_data.append(file_info)
        # Only clear widgets that are not in the new files_data
        current_keys = set(self.grid_manager._widget_cache.keys())
        new_keys = set(f['filepath'] for f in files_data)
        for key in current_keys - new_keys:
            widget = self.grid_manager._widget_cache.pop(key, None)
            if widget:
                widget.deleteLater()
        while self.thumbnail_flow.count():
            item = self.thumbnail_flow.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        if files_data:
            for file_info in files_data:
                widget = self.grid_manager._create_image_widget(file_info)
                self.thumbnail_flow.addWidget(widget)
        else:
            no_data_label = QLabel("No images found")
            no_data_label.setAlignment(Qt.AlignCenter)
            self.thumbnail_flow.addWidget(no_data_label)

    def get_selected_row_data(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            return [self.table.item(row, col).data(Qt.DisplayRole) if self.table.item(row, col) else "" for col in range(self.table.columnCount())]
        return None

    def _emit_stats(self):
        total = self.table.rowCount()
        checked = 0
        failed = 0
        success = 0
        draft = 0
        status_col = 8
        for row in range(total):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                checked += 1
            status_item = self.table.item(row, status_col)
            if status_item:
                status_text = status_item.text().strip().lower()
                if status_text == "failed":
                    failed += 1
                elif status_text == "success":
                    success += 1
                elif status_text == "draft":
                    draft += 1
        self.stats_changed.emit(total, checked, failed, success, draft)

    def _on_item_changed(self, item):
        if item.column() == 0:
            self._emit_stats()

    def _on_selection_changed(self, selected, deselected):
        if self._properties_widget is None:
            self._properties_widget = getattr(self.parent(), "properties_widget", None)
        if self._properties_widget is None:
            return
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            idx = selected_rows[0].row()
            # Ambil data asli dari cache, bukan dari tabel (agar mapping sinkron)
            if 0 <= idx < len(self._all_rows_cache):
                row = self._all_rows_cache[idx]
                title = row[3] if len(row) > 3 and row[3] is not None else ""
                tags = row[5] if len(row) > 5 and row[5] is not None else ""
                title_length = len(title)
                tag_count = len([t for t in tags.split(",") if t.strip()]) if tags else 0
                # Sertakan file_id di row_data[0]
                row_data = [row[0]] + list(row[1:7]) + [row[7] if len(row) > 7 else ""] + [str(title_length), str(tag_count)]
                self._properties_widget.set_properties(row_data)
            else:
                self._properties_widget.set_properties(None)
        else:
            self._properties_widget.set_properties(None)

    def _on_thumbnail_clicked(self, row, col, file_info):
        # Sinkronkan seleksi di tabel dan update properties_widget
        filepath = file_info.get('filepath', '')
        if not filepath:
            return
        for row_idx in range(self.table.rowCount()):
            item = self.table.item(row_idx, 1)
            if item and (item.data(Qt.UserRole) == filepath or item.text() == filepath):
                self.table.selectRow(row_idx)
                break
        if self._properties_widget:
            for row in self._all_rows_cache:
                if row[1] == filepath:
                    title = row[3] if len(row) > 3 and row[3] is not None else ""
                    tags = row[5] if len(row) > 5 and row[5] is not None else ""
                    title_length = len(title)
                    tag_count = len([t for t in tags.split(",") if t.strip()]) if tags else 0
                    row_data = [row[0]] + list(row[1:7]) + [row[7] if len(row) > 7 else ""] + [str(title_length), str(tag_count)]
                    self._properties_widget.set_properties(row_data)
                    break

    def delete_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Delete", "No rows selected.")
            return
        for idx in selected:
            filepath = self.table.item(idx.row(), 1).data(Qt.UserRole)
            if not filepath:
                filepath = self.table.item(idx.row(), 1).text()
            self.db.delete_file(filepath)
        self.refresh_table()

    def clear_all(self):
        if QMessageBox.question(self, "Clear All", "Are you sure you want to clear all files?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.clear_files()
            self.refresh_table()
