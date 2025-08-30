from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QMessageBox, QAbstractItemView, QHeaderView,
    QVBoxLayout, QWidget, QProgressBar, QMenu, QLabel, QHBoxLayout, QLineEdit,
    QPushButton, QToolTip, QTabWidget, QScrollArea, QFrame, QLayout
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QRect, QSize, QPoint as QtQPoint, QEvent
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
        right = rect.x() + rect.width()
        for item in self._itemList:
            widget = item.widget()
            if widget and not widget.isVisible():
                continue
            spaceX = self.spacing()
            spaceY = self.spacing()
            itemSize = item.sizeHint()
            nextX = x + itemSize.width() + spaceX
            if nextX - spaceX > right and x > rect.x():
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + itemSize.width() + spaceX
                lineHeight = 0
            if not testOnly:
                item.setGeometry(QRect(QtQPoint(x, y), itemSize))
            x = nextX
            lineHeight = max(lineHeight, itemSize.height())
        return y + lineHeight - rect.y()

class GridManager:
    def __init__(self):
        self.image_items = []
        self.image_size = 150
        self.grid_spacing = 10
        self.active_image = None
        self._widget_cache = {}
        self._pixmap_cache = {}
        self._status_color_func = None
        self._checked_filepaths = set()

    def set_status_color_func(self, func):
        self._status_color_func = func

    def set_checked_filepaths(self, checked_filepaths):
        self._checked_filepaths = set(checked_filepaths)
        self._update_checked_thumbnail_styles()

    def _update_checked_thumbnail_styles(self):
        for filepath, widget in self._widget_cache.items():
            file_info = widget.property("file_info")
            status = file_info.get('status', '') if file_info else ''
            label = None
            for child in widget.children():
                if isinstance(child, QLabel):
                    label = child
                    break
            if label:
                if filepath in self._checked_filepaths:
                    label.setStyleSheet(
                        "QLabel {"
                        "border: 2.5px solid rgba(0, 120, 255, 0.85);"
                        "border-radius: 4px;"
                        "padding: 2px;"
                        "background-color: rgba(0, 120, 255, 0.10);"
                        "}"
                        "QLabel:hover {"
                        "border: 2.5px solid rgba(0, 120, 255, 1.0);"
                        "background-color: rgba(0, 120, 255, 0.18);"
                        "}"
                    )
                else:
                    self._set_image(label, filepath, status)

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
        status = file_info.get('status', '')
        cache_key = filepath

        if cache_key in self._widget_cache:
            widget = self._widget_cache[cache_key]
            # Update border color if status changed
            self._set_image(widget.findChild(QLabel), filepath, status)
            widget.setProperty("file_info", file_info)
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
        image_label.setAttribute(Qt.WA_Hover, True)
        image_label.setCursor(Qt.PointingHandCursor)
        self._set_image(image_label, filepath, status)
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
        container.setContextMenuPolicy(Qt.CustomContextMenu)
        container.mousePressEvent = lambda event: self._handle_image_click(container, event)
        image_label.mousePressEvent = lambda event: self._handle_image_click(container, event)
        container.mouseDoubleClickEvent = lambda event: self._handle_image_double_click(container)
        image_label.mouseDoubleClickEvent = lambda event: self._handle_image_double_click(container)
        container.customContextMenuEvent = lambda event: self._show_context_menu(container, event)
        image_label.customContextMenuEvent = lambda event: self._show_context_menu(container, event)
        self._widget_cache[cache_key] = container
        return container

    def _set_image(self, label, image_path, status=''):
        if image_path in self._pixmap_cache:
            pixmap = self._pixmap_cache[image_path]
            if pixmap:
                label.setPixmap(pixmap)
            else:
                label.setText("Cannot load\nimage")
        else:
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
        # Set border color according to status
        color = None
        if self._status_color_func:
            color = self._status_color_func(status)
        if color is None:
            color = QColor(0, 0, 0, int(0.1 * 255))
        border_rgba = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()/255:.2f})"
        label.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {border_rgba};
                border-radius: 4px;
                padding: 2px;
                background-color: transparent;
            }}
            QLabel:hover {{
                border: 2.5px solid rgba(88, 165, 0, 0.7);
                background-color: rgba(88, 165, 0, 0.05);
            }}
        """)

    def update_thumbnail_status(self, filepath, status):
        widget = self._widget_cache.get(filepath)
        if widget:
            file_info = widget.property("file_info")
            if file_info is not None:
                file_info['status'] = status
                widget.setProperty("file_info", file_info)
            label = None
            for child in widget.children():
                if isinstance(child, QLabel):
                    label = child
                    break
            if label:
                self._set_image(label, filepath, status)

    def _update_active_image(self, new_active_widget):
        try:
            if self.active_image:
                for child in self.active_image.children():
                    if isinstance(child, QLabel) and child.objectName() != "filename_label":
                        file_info = self.active_image.property("file_info")
                        status = file_info.get('status', '') if file_info else ''
                        color = None
                        if self._status_color_func:
                            color = self._status_color_func(status)
                        if color is None:
                            color = QColor(0, 0, 0, int(0.1 * 255))
                        border_rgba = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()/255:.2f})"
                        child.setStyleSheet(f"""
                            QLabel {{
                                border: 2px solid {border_rgba};
                                border-radius: 4px;
                                padding: 2px;
                                background-color: transparent;
                            }}
                            QLabel:hover {{
                                border: 2.5px solid rgba(88, 165, 0, 0.7);
                                background-color: rgba(88, 165, 0, 0.05);
                            }}
                        """)
                        break
            self.active_image = new_active_widget
            if self.active_image:
                for child in self.active_image.children():
                    if isinstance(child, QLabel) and child.objectName() != "filename_label":
                        child.setStyleSheet("""
                            QLabel {
                                border: 2px solid rgba(88, 165, 0, 0.7);
                                border-radius: 4px;
                                padding: 2px;
                                background-color: rgba(88, 165, 0, 0.20);
                            }
                            QLabel:hover {
                                border: 2.5px solid rgba(88, 165, 0, 1.0);
                                background-color: rgba(88, 165, 0, 0.25);
                            }
                        """)
                        break
        except Exception as e:
            print(f"Error updating active image styling: {e}")

    def _handle_image_click(self, widget, event):
        try:
            if event.button() == Qt.RightButton:
                self._show_context_menu(widget, event)
                return
            if event.type() == QEvent.MouseButtonDblClick:
                self._handle_image_double_click(widget)
                return
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

    def _handle_image_double_click(self, widget):
        try:
            file_info = widget.property("file_info")
            if not file_info:
                return
            parent_widget = widget.parent()
            while parent_widget and not hasattr(parent_widget, '_open_metadata_dialog'):
                parent_widget = parent_widget.parent()
            if parent_widget and hasattr(parent_widget, '_open_metadata_dialog'):
                parent_widget._open_metadata_dialog_by_filepath(file_info['filepath'])
        except Exception as e:
            print(f"Error handling grid image double click: {e}")

    def _show_context_menu(self, widget, event):
        try:
            file_info = widget.property("file_info")
            if not file_info:
                return
            backend_row = None
            parent_widget = widget.parent()
            while parent_widget and not hasattr(parent_widget, '_all_rows_cache'):
                parent_widget = parent_widget.parent()
            if parent_widget and hasattr(parent_widget, '_all_rows_cache'):
                for row in parent_widget._all_rows_cache:
                    if row[1] == file_info['filepath']:
                        backend_row = row
                        break
            if backend_row is None:
                print(f"Error: backend_row not found for filepath {file_info['filepath']}")
                return
            menu = QMenu(widget)
            edit_icon = qta.icon("fa6s.pen-to-square")
            edit_action = QAction(edit_icon, "Edit metadata", widget)
            edit_action.triggered.connect(lambda: self._open_metadata_dialog_from_grid(widget))
            menu.addAction(edit_action)
            filename = backend_row[2]
            title = backend_row[3]
            description = backend_row[4]
            tags = backend_row[5]
            copy_filename_action = QAction(qta.icon("fa6s.copy"), "Copy Filename", widget)
            copy_filename_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(filename, "Filename", event))
            menu.addAction(copy_filename_action)
            copy_title_action = QAction(qta.icon("fa6s.copy"), "Copy Title", widget)
            copy_title_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(title, "Title", event))
            menu.addAction(copy_title_action)
            copy_desc_action = QAction(qta.icon("fa6s.copy"), "Copy Description", widget)
            copy_desc_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(description, "Description", event))
            menu.addAction(copy_desc_action)
            copy_tags_action = QAction(qta.icon("fa6s.copy"), "Copy Keyword", widget)
            copy_tags_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(tags, "Keyword", event))
            menu.addAction(copy_tags_action)
            menu.exec(event.globalPos() if hasattr(event, "globalPos") else widget.mapToGlobal(event.pos()))
        except Exception as e:
            print(f"Error showing context menu in grid: {e}")

    def _copy_to_clipboard_with_tooltip(self, text, label, event):
        QGuiApplication.clipboard().setText("" if text is None else text)
        def shorten(val, maxlen=60):
            if val is None:
                return ""
            val = val.strip()
            if len(val) > maxlen:
                return val[:maxlen-3] + "..."
            return val
        value = shorten(text)
        tooltip = f"Copied {label}: {value}" if value else f"Copied {label}: (empty)"
        global_pos = event.globalPos() if hasattr(event, "globalPos") else None
        QToolTip.showText(global_pos, tooltip)
        QTimer.singleShot(1200, QToolTip.hideText)

    def _open_metadata_dialog_from_grid(self, widget):
        try:
            file_info = widget.property("file_info")
            if not file_info:
                return
            parent_widget = widget.parent()
            while parent_widget and not hasattr(parent_widget, '_open_metadata_dialog'):
                parent_widget = parent_widget.parent()
            if parent_widget and hasattr(parent_widget, '_open_metadata_dialog'):
                parent_widget._open_metadata_dialog_by_filepath(file_info['filepath'])
        except Exception as e:
            print(f"Error opening metadata dialog from grid: {e}")

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
        reload_btn = QPushButton(self)
        reload_btn.setIcon(qta.icon("fa6s.rotate-right"))
        reload_btn.setFlat(True)
        reload_btn.setFocusPolicy(Qt.NoFocus)
        reload_btn.setFixedWidth(28)
        reload_btn.setToolTip("Reload/refresh data from database")
        reload_btn.clicked.connect(self._on_reload_clicked)
        search_layout.addWidget(search_icon_btn)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(paste_btn)
        search_layout.addWidget(clear_btn)
        search_layout.addWidget(reload_btn)
        self.layout.addLayout(search_layout)
        self.tab_widget = QTabWidget(self)
        self.layout.addWidget(self.tab_widget)
        self.table_tab = QWidget()
        self.table_tab_layout = QVBoxLayout(self.table_tab)
        self.table_tab_layout.setContentsMargins(0, 0, 0, 0)
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
        self.details_tab = QWidget()
        self.details_tab_layout = QVBoxLayout(self.details_tab)
        self.details_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.details_scroll = QScrollArea(self.details_tab)
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameShape(QFrame.NoFrame)
        self.details_tab_layout.addWidget(self.details_scroll)
        self.details_content = QWidget()
        self.details_scroll.setWidget(self.details_content)
        self.details_vbox = QVBoxLayout(self.details_content)
        self.details_vbox.setContentsMargins(10, 10, 10, 10)
        self.details_vbox.setSpacing(10)
        self.tab_widget.addTab(self.details_tab, "Details")
        self.details_card_cache = {}  # cache for details cards
        self._donation_dialog_shown = False
        self.table.selectionModel().selectionChanged.connect(self._emit_stats)
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._all_rows_cache = []
        self.grid_manager = GridManager()
        self.grid_manager.set_status_color_func(self._status_color)
        self.grid_manager.setup_grid_click_handler(self.thumbnail_content, self._on_thumbnail_clicked)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self._inject_open_metadata_dialog_for_grid()
        self.refresh_table()

    def _inject_open_metadata_dialog_for_grid(self):
        def _open_metadata_dialog_by_filepath(filepath):
            if not filepath:
                return
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 1)
                if item and (item.data(Qt.UserRole) == filepath or item.text() == filepath):
                    self._open_metadata_dialog(row)
                    break
        self._open_metadata_dialog_by_filepath = _open_metadata_dialog_by_filepath

    def _on_reload_clicked(self):
        self.refresh_table()

    def _on_tab_changed(self, idx):
        if self.tab_widget.tabText(idx) == "Thumbnail":
            self.refresh_thumbnail_grid()
            self._sync_thumbnail_selection_with_table()
        elif self.tab_widget.tabText(idx) == "Details":
            self._refresh_details_cards()

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
            self._sync_thumbnail_selection_with_table()
        if self.tab_widget.currentIndex() == 2:
            self._refresh_details_cards()

    def _filter_table(self, text):
        text = text.strip().lower()
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
        global_pos = pos.globalPos() if hasattr(pos, "globalPos") else self.table.viewport().mapToGlobal(pos)
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
        filepath = None
        item = self.table.item(row_idx, 1)
        if item:
            filepath = item.data(Qt.UserRole)
            if not filepath:
                filepath = item.text()
        if filepath:
            self.grid_manager.update_thumbnail_status(filepath, status)
            # Update status in _all_rows_cache for realtime sync (convert tuple to list, update, then back to tuple)
            for i, row in enumerate(self._all_rows_cache):
                if row[1] == filepath:
                    row_list = list(row)
                    if len(row_list) > 6:
                        row_list[6] = status
                        self._all_rows_cache[i] = tuple(row_list)
                    break

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
        elif status == "draft":
            return QColor(120, 120, 120, int(0.18 * 255))
        return QColor(0, 0, 0, int(0.1 * 255))

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
            self._sync_thumbnail_selection_with_table()
        if self.tab_widget.currentIndex() == 2:
            self._refresh_details_cards()

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
                'extension': os.path.splitext(row[2])[1],
                'status': row[6] if len(row) > 6 else ""
            }
            files_data.append(file_info)
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
        # Setelah thumbnail grid di-refresh, update checklist style
        self._update_thumbnail_checklist_style()

    def _sync_thumbnail_selection_with_table(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.grid_manager._update_active_image(None)
            return
        idx = selected_rows[0].row()
        filepath = None
        item = self.table.item(idx, 1)
        if item:
            filepath = item.data(Qt.UserRole)
            if not filepath:
                filepath = item.text()
        if not filepath:
            self.grid_manager._update_active_image(None)
            return
        for i in range(self.thumbnail_flow.count()):
            widget = self.thumbnail_flow.itemAt(i).widget()
            if widget and widget.property("file_info"):
                file_info = widget.property("file_info")
                if file_info.get("filepath") == filepath:
                    self.grid_manager._update_active_image(widget)
                    return
        self.grid_manager._update_active_image(None)

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
            self._update_thumbnail_checklist_style()
        if self.tab_widget.currentIndex() == 2:
            self._refresh_details_cards()

    def _on_selection_changed(self, selected, deselected):
        if self._properties_widget is None:
            self._properties_widget = getattr(self.parent(), "properties_widget", None)
        if self._properties_widget is None:
            return
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            idx = selected_rows[0].row()
            if 0 <= idx < len(self._all_rows_cache):
                row = self._all_rows_cache[idx]
                title = row[3] if len(row) > 3 and row[3] is not None else ""
                tags = row[5] if len(row) > 5 and row[5] is not None else ""
                title_length = len(title)
                tag_count = len([t for t in tags.split(",") if t.strip()]) if tags else 0
                row_data = [row[0]] + list(row[1:7]) + [row[7] if len(row) > 7 else ""] + [str(title_length), str(tag_count)]
                self._properties_widget.set_properties(row_data)
            else:
                self._properties_widget.set_properties(None)
        else:
            self._properties_widget.set_properties(None)
        if self.tab_widget.currentIndex() == 1:
            self._sync_thumbnail_selection_with_table()
        if self.tab_widget.currentIndex() == 2:
            self._refresh_details_cards()
        # Highlight selected row with green background
        self._highlight_selected_row()

    def _highlight_selected_row(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            self.table.setStyleSheet(
                "QTableWidget::item:selected {"
                "background-color: rgba(88, 165, 0, 51);"
                "}"
            )
        else:
            self.table.setStyleSheet("")
        for row in range(self.table.rowCount()):
            if not (selected_rows and row == selected_rows[0].row()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        status_val = self.table.item(row, 8).text() if self.table.item(row, 8) else ""
                        item.setBackground(QBrush(self._status_color(status_val)))

    def _on_thumbnail_clicked(self, row, col, file_info):
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
        if self.tab_widget.currentIndex() == 2:
            self._refresh_details_cards()

    def _update_thumbnail_checklist_style(self):
        checked_filepaths = []
        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            filepath_item = self.table.item(row, 1)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked and filepath_item:
                filepath = filepath_item.data(Qt.UserRole)
                if not filepath:
                    filepath = filepath_item.text()
                checked_filepaths.append(filepath)
        self.grid_manager.set_checked_filepaths(checked_filepaths)

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

    def _refresh_details_cards(self):
        # Remove all widgets from layout, but keep cache
        for i in reversed(range(self.details_vbox.count())):
            item = self.details_vbox.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        rows = []
        text = self.search_edit.text().strip().lower()
        if not text:
            rows = list(self.db.get_all_files())
        else:
            rows = [row for row in self._all_rows_cache if self._row_matches_search(row, text)]
        # Remove cache for files not in rows
        current_filepaths = set(row[1] for row in rows)
        for filepath in list(self.details_card_cache.keys()):
            if filepath not in current_filepaths:
                widget = self.details_card_cache.pop(filepath)
                if widget:
                    widget.setParent(None)
                # Hapus juga pixmap cache jika ingin sinkron
                if filepath in self.grid_manager._pixmap_cache:
                    del self.grid_manager._pixmap_cache[filepath]
        if not rows:
            label = QLabel("No data found")
            label.setAlignment(Qt.AlignCenter)
            self.details_vbox.addWidget(label)
            return
        for row in rows:
            filepath = row[1]
            if filepath in self.details_card_cache:
                card = self.details_card_cache[filepath]
                self._update_details_card(card, row, self.grid_manager)
            else:
                card = self._create_details_card(row, self.grid_manager)
                self.details_card_cache[filepath] = card
            self.details_vbox.addWidget(card)

    def _create_details_card(self, row, grid_manager):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        card_hbox = QHBoxLayout(frame)
        card_hbox.setContentsMargins(8, 8, 8, 8)
        card_hbox.setSpacing(12)
        thumb = QLabel()
        thumb.setFixedSize(150, 150)
        thumb.setAlignment(Qt.AlignCenter)
        filepath = row[1]
        pixmap = None
        if filepath in grid_manager._pixmap_cache:
            pixmap = grid_manager._pixmap_cache[filepath]
        else:
            pixmap_raw = QPixmap(filepath)
            if not pixmap_raw.isNull():
                pixmap = pixmap_raw.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                grid_manager._pixmap_cache[filepath] = pixmap
        if pixmap and not pixmap.isNull():
            thumb.setPixmap(pixmap)
        else:
            thumb.setText("No\nImage")
        card_hbox.addWidget(thumb)
        vbox = QVBoxLayout()
        vbox.setSpacing(2)
        filename = row[2]
        title = row[3] if len(row) > 3 and row[3] is not None else ""
        desc = row[4] if len(row) > 4 and row[4] is not None else ""
        tags = row[5] if len(row) > 5 and row[5] is not None else ""
        status = row[6] if len(row) > 6 and row[6] is not None else ""
        db = self.db
        shutterstock_map = {}
        adobe_map = {}
        primary_val = "-"
        secondary_val = "-"
        adobe_val = "-"
        if db:
            shutterstock_map, adobe_map = db.get_category_maps()
            file_id = row[0]
            if file_id is not None:
                mapping = db.get_category_mapping_for_file(file_id)
                for m in mapping:
                    if m["platform"] == "shutterstock":
                        cat_name = str(m["category_name"])
                        if cat_name.lower().endswith("(primary)"):
                            primary_val = shutterstock_map.get(str(m["category_id"]), "-")
                        elif cat_name.lower().endswith("(secondary)"):
                            secondary_val = shutterstock_map.get(str(m["category_id"]), "-")
                    elif m["platform"] == "adobe_stock":
                        adobe_val = adobe_map.get(str(m["category_id"]), "-")
        label_filename = QLabel(f"Filename: {filename}")
        label_filename.setWordWrap(True)
        label_title = QLabel(f"Title: {title}")
        label_title.setWordWrap(True)
        label_desc = QLabel(f"Description: {desc}")
        label_desc.setWordWrap(True)
        label_tags = QLabel(f"Tags: {tags}")
        label_tags.setWordWrap(True)
        label_status = QLabel(f"Status: {status}")
        label_status.setWordWrap(True)
        label_cat_primary = QLabel(f"Shutterstock Primary: {primary_val}")
        label_cat_primary.setWordWrap(True)
        label_cat_secondary = QLabel(f"Shutterstock Secondary: {secondary_val}")
        label_cat_secondary.setWordWrap(True)
        label_cat_adobe = QLabel(f"Adobe Stock Category: {adobe_val}")
        label_cat_adobe.setWordWrap(True)
        vbox.addWidget(label_filename)
        vbox.addWidget(label_title)
        vbox.addWidget(label_desc)
        vbox.addWidget(label_tags)
        vbox.addWidget(label_status)
        vbox.addWidget(label_cat_primary)
        vbox.addWidget(label_cat_secondary)
        vbox.addWidget(label_cat_adobe)
        card_hbox.addLayout(vbox)
        frame._details_thumb = thumb
        frame._details_label_filename = label_filename
        frame._details_label_title = label_title
        frame._details_label_desc = label_desc
        frame._details_label_tags = label_tags
        frame._details_label_status = label_status
        frame._details_label_cat_primary = label_cat_primary
        frame._details_label_cat_secondary = label_cat_secondary
        frame._details_label_cat_adobe = label_cat_adobe
        frame._details_filepath = filepath
        return frame

    def _update_details_card(self, card, row, grid_manager):
        filepath = row[1]
        pixmap = None
        if filepath in grid_manager._pixmap_cache:
            pixmap = grid_manager._pixmap_cache[filepath]
        else:
            pixmap_raw = QPixmap(filepath)
            if not pixmap_raw.isNull():
                pixmap = pixmap_raw.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                grid_manager._pixmap_cache[filepath] = pixmap
        if pixmap and not pixmap.isNull():
            card._details_thumb.setPixmap(pixmap)
            card._details_thumb.setText("")
        else:
            card._details_thumb.setPixmap(QPixmap())
            card._details_thumb.setText("No\nImage")
        filename = row[2]
        title = row[3] if len(row) > 3 and row[3] is not None else ""
        desc = row[4] if len(row) > 4 and row[4] is not None else ""
        tags = row[5] if len(row) > 5 and row[5] is not None else ""
        status = row[6] if len(row) > 6 and row[6] is not None else ""
        db = self.db
        shutterstock_map = {}
        adobe_map = {}
        primary_val = "-"
        secondary_val = "-"
        adobe_val = "-"
        if db:
            shutterstock_map, adobe_map = db.get_category_maps()
            file_id = row[0]
            if file_id is not None:
                mapping = db.get_category_mapping_for_file(file_id)
                for m in mapping:
                    if m["platform"] == "shutterstock":
                        cat_name = str(m["category_name"])
                        if cat_name.lower().endswith("(primary)"):
                            primary_val = shutterstock_map.get(str(m["category_id"]), "-")
                        elif cat_name.lower().endswith("(secondary)"):
                            secondary_val = shutterstock_map.get(str(m["category_id"]), "-")
                    elif m["platform"] == "adobe_stock":
                        adobe_val = adobe_map.get(str(m["category_id"]), "-")
        card._details_label_filename.setText(f"Filename: {filename}")
        card._details_label_filename.setWordWrap(True)
        card._details_label_title.setText(f"Title: {title}")
        card._details_label_title.setWordWrap(True)
        card._details_label_desc.setText(f"Description: {desc}")
        card._details_label_desc.setWordWrap(True)
        card._details_label_tags.setText(f"Tags: {tags}")
        card._details_label_tags.setWordWrap(True)
        card._details_label_status.setText(f"Status: {status}")
        card._details_label_status.setWordWrap(True)
        card._details_label_cat_primary.setText(f"Shutterstock Primary: {primary_val}")
        card._details_label_cat_primary.setWordWrap(True)
        card._details_label_cat_secondary.setText(f"Shutterstock Secondary: {secondary_val}")
        card._details_label_cat_secondary.setWordWrap(True)
        card._details_label_cat_adobe.setText(f"Adobe Stock Category: {adobe_val}")
        card._details_label_cat_adobe.setWordWrap(True)
