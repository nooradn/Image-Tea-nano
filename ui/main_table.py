from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox, QAbstractItemView, QHeaderView, QVBoxLayout, QWidget, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush

class ImageTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(0, 9, self)
        self.table.setHorizontalHeaderLabels([
            "", "Filepath", "Filename", "Title", "Description", "Tags", "Title Length", "Tag Count", "Status"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for col in range(1, 9):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 32)
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

    def set_row_status_color(self, row_idx, status):
        color = QColor(255, 255, 255, 0)
        if status == "processing":
            color = QColor(243, 200, 24, int(0.3 * 255))
        elif status == "success":
            color = QColor(113, 204, 0, int(0.3 * 255))
        elif status == "failed" or status == "stopped":
            color = QColor(255, 0, 0, int(0.15 * 255))
        for col in range(self.table.columnCount()):
            item = self.table.item(row_idx, col)
            if item:
                item.setBackground(QBrush(color))
        status_col = 8
        status_item = self.table.item(row_idx, status_col)
        if status_item:
            status_item.setText(status.capitalize())

    def update_row_data(self, row_idx, row_data):
        # row_data: (id, filepath, filename, title, description, tags, status)
        display_values = row_data[1:7]
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
    self.table.table.setRowCount(0)
    for row in self.db.get_all_files():
        row_idx = self.table.table.rowCount()
        self.table.table.insertRow(row_idx)
        # Checkbox with id as data
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checkbox_item.setCheckState(Qt.Unchecked)
        checkbox_item.setData(Qt.UserRole, row[0])
        self.table.table.setItem(row_idx, 0, checkbox_item)
        display_values = row[1:7]
        for col, val in enumerate(display_values):
            item = QTableWidgetItem(str(val) if val is not None else "")
            if col == 0:
                item.setTextAlignment(Qt.AlignCenter)
            self.table.table.setItem(row_idx, col + 1, item)
        title_val = row[3] if len(row) > 3 and row[3] is not None else ""
        title_len = len(title_val)
        title_len_item = QTableWidgetItem(str(title_len))
        title_len_item.setTextAlignment(Qt.AlignCenter)
        self.table.table.setItem(row_idx, 6, title_len_item)
        tags_val = row[5] if len(row) > 5 and row[5] is not None else ""
        tag_count = len([t for t in tags_val.split(",") if t.strip()]) if tags_val else 0
        tag_count_item = QTableWidgetItem(str(tag_count))
        tag_count_item.setTextAlignment(Qt.AlignCenter)
        self.table.table.setItem(row_idx, 7, tag_count_item)
        status_val = row[6] if len(row) > 6 and row[6] is not None else ""
        status_item = QTableWidgetItem(str(status_val))
        status_item.setTextAlignment(Qt.AlignCenter)
        self.table.table.setItem(row_idx, 8, status_item)
        color = QColor(255, 255, 255, 0)
        if status_val == "success":
            color = QColor(113, 204, 0, int(0.3 * 255))
        elif status_val == "failed" or status_val == "stopped":
            color = QColor(255, 0, 0, int(0.15 * 255))
        elif status_val == "processing":
            color = QColor(243, 200, 24, int(0.3 * 255))
        for col in range(self.table.table.columnCount()):
            item = self.table.table.item(row_idx, col)
            if item:
                item.setBackground(QBrush(color))

def delete_selected(self):
    selected = self.table.table.selectionModel().selectedRows()
    if not selected:
        QMessageBox.information(self, "Delete", "No rows selected.")
        return
    for idx in selected:
        filepath = self.table.table.item(idx.row(), 1).text()
        self.db.delete_file(filepath)
    refresh_table(self)

def clear_all(self):
    if QMessageBox.question(self, "Clear All", "Are you sure you want to clear all files?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
        self.db.clear_files()
        refresh_table(self)
