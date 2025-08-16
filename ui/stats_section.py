from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class StatsSectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label_total = QLabel("Total Images: 0")
        self.label_selected = QLabel("Selected: 0")
        self.label_failed = QLabel("Failed: 0")
        self.label_success = QLabel("Success: 0")
        self.label_draft = QLabel("Draft: 0")
        layout.addWidget(self.label_total)
        layout.addWidget(self.label_selected)
        layout.addWidget(self.label_failed)
        layout.addWidget(self.label_success)
        layout.addWidget(self.label_draft)

    def update_stats(self, total, selected, failed, success=0, draft=0):
        self.label_total.setText(f"Total Images: {total}")
        self.label_selected.setText(f"Selected: {selected}")
        self.label_failed.setText(f"Failed: {failed}")
        self.label_success.setText(f"Success: {success}")
        self.label_draft.setText(f"Draft: {draft}")
