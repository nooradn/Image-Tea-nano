from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox, QAbstractItemView, QHeaderView, QVBoxLayout, QWidget, QProgressBar
from PySide6.QtCore import Qt

class ImageTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(0, 8, self)
        self.table.setHorizontalHeaderLabels([
            "Filepath", "Filename", "Title", "Description", "Tags", "Title Length", "Tag Count", "Status"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

def refresh_table(self):
    self.table.table.setRowCount(0)
    for row in self.db.get_all_files():
        row_idx = self.table.table.rowCount()
        self.table.table.insertRow(row_idx)
        display_values = row[1:7]
        for col, val in enumerate(display_values):
            item = QTableWidgetItem(str(val) if val is not None else "")
            if col == 0:
                item.setTextAlignment(Qt.AlignCenter)
            self.table.table.setItem(row_idx, col, item)
        title_val = row[3] if len(row) > 3 and row[3] is not None else ""
        title_len = len(title_val)
        title_len_item = QTableWidgetItem(str(title_len))
        title_len_item.setTextAlignment(Qt.AlignCenter)
        self.table.table.setItem(row_idx, 5, title_len_item)
        tags_val = row[5] if len(row) > 5 and row[5] is not None else ""
        tag_count = len([t for t in tags_val.split(",") if t.strip()]) if tags_val else 0
        tag_count_item = QTableWidgetItem(str(tag_count))
        tag_count_item.setTextAlignment(Qt.AlignCenter)
        self.table.table.setItem(row_idx, 6, tag_count_item)
        status_val = row[6] if len(row) > 6 and row[6] is not None else ""
        status_item = QTableWidgetItem(str(status_val))
        status_item.setTextAlignment(Qt.AlignCenter)
        self.table.table.setItem(row_idx, 7, status_item)

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
