from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox, QAbstractItemView, QHeaderView, QVBoxLayout, QWidget, QProgressBar, QMenu, QLabel, QHBoxLayout, QLineEdit, QPushButton, QToolTip
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QColor, QBrush, QAction, QGuiApplication
from dialogs.file_metadata_dialog import FileMetadataDialog
from dialogs.donation_dialog import DonateDialog, is_donation_optout_today
import qtawesome as qta
import os

class ImageTableWidget(QWidget):
    stats_changed = Signal(int, int, int, int, int)  # total, selected, failed, success, draft

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Search bar layout
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.setClearButtonEnabled(False)
        self.search_edit.textChanged.connect(self._on_search_text_changed)

        search_icon_btn = QPushButton(self)
        search_icon_btn.setIcon(qta.icon("fa5s.search"))
        search_icon_btn.setFlat(True)
        search_icon_btn.setFocusPolicy(Qt.NoFocus)
        search_icon_btn.setEnabled(False)
        search_icon_btn.setFixedWidth(28)

        paste_btn = QPushButton(self)
        paste_btn.setIcon(qta.icon("fa5s.clipboard"))
        paste_btn.setFlat(True)
        paste_btn.setFocusPolicy(Qt.NoFocus)
        paste_btn.setFixedWidth(28)
        paste_btn.setToolTip("Paste text from clipboard ke kolom pencarian")
        paste_btn.clicked.connect(self._on_paste_clicked)

        clear_btn = QPushButton(self)
        clear_btn.setIcon(qta.icon("fa5s.times"))
        clear_btn.setFlat(True)
        clear_btn.setFocusPolicy(Qt.NoFocus)
        clear_btn.setFixedWidth(28)
        clear_btn.setToolTip("Bersihkan kolom pencarian")
        clear_btn.clicked.connect(self._on_clear_search)

        search_layout.addWidget(search_icon_btn)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(paste_btn)
        search_layout.addWidget(clear_btn)
        self.layout.addLayout(search_layout)

        self.table = QTableWidget(0, 9, self)
        self.table.setHorizontalHeaderLabels([
            "", "Filepath", "Filename", "Title", "Description", "Tags", "Title Length", "Tag Count", "Status"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for col in range(0, 9):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.layout.addWidget(self.table)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('')
        self.progress_bar.setVisible(True)
        self.progress_bar.setToolTip("Shows progress for batch operations")
        self.layout.addWidget(self.progress_bar)

        self._donation_dialog_shown = False

        # Connect selection change to stats update
        self.table.selectionModel().selectionChanged.connect(self._emit_stats)
        self.table.itemChanged.connect(self._on_item_changed)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        self._all_rows_cache = []

        self.refresh_table()

    def _on_paste_clicked(self):
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text()
        self.search_edit.setText(text)

    def _on_clear_search(self):
        self.search_edit.clear()

    def _on_search_text_changed(self, text):
        self._filter_table(text)

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
        edit_icon = qta.icon("fa5s.edit")
        edit_action = QAction(edit_icon, "Edit metadata", self)
        edit_action.triggered.connect(lambda: self._open_metadata_dialog(index.row()))
        menu.addAction(edit_action)

        row_idx = index.row()
        filename_item = self.table.item(row_idx, 2)
        title_item = self.table.item(row_idx, 3)
        desc_item = self.table.item(row_idx, 4)
        tags_item = self.table.item(row_idx, 5)

        copy_filename_action = QAction(qta.icon("fa5s.copy"), "Copy Filename", self)
        copy_filename_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(filename_item.text() if filename_item else "", "Filename", pos))
        menu.addAction(copy_filename_action)

        copy_title_action = QAction(qta.icon("fa5s.copy"), "Copy Title", self)
        copy_title_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(title_item.text() if title_item else "", "Title", pos))
        menu.addAction(copy_title_action)

        copy_desc_action = QAction(qta.icon("fa5s.copy"), "Copy Description", self)
        copy_desc_action.triggered.connect(lambda: self._copy_to_clipboard_with_tooltip(desc_item.text() if desc_item else "", "Description", pos))
        menu.addAction(copy_desc_action)

        copy_tags_action = QAction(qta.icon("fa5s.copy"), "Copy Keyword", self)
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
        dialog = FileMetadataDialog(filepath, parent=self)
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
