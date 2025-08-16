from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout

class StatsSectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)

        file_stats_layout = QVBoxLayout()
        file_stats_layout.setContentsMargins(0, 0, 0, 0)
        self.label_total = QLabel("Total Images: 0")
        self.label_selected = QLabel("Selected: 0")
        self.label_failed = QLabel("Failed: 0")
        self.label_success = QLabel("Success: 0")
        self.label_draft = QLabel("Draft: 0")
        file_stats_layout.addWidget(self.label_total)
        file_stats_layout.addWidget(self.label_selected)
        file_stats_layout.addWidget(self.label_failed)
        file_stats_layout.addWidget(self.label_success)
        file_stats_layout.addWidget(self.label_draft)

        token_stats_layout = QVBoxLayout()
        token_stats_layout.setContentsMargins(0, 0, 0, 0)
        self.label_token_input = QLabel("Token Input: 0")
        self.label_token_output = QLabel("Token Output: 0")
        self.label_token_total = QLabel("Token Total: 0")
        token_stats_layout.addWidget(self.label_token_input)
        token_stats_layout.addWidget(self.label_token_output)
        token_stats_layout.addWidget(self.label_token_total)

        hbox.addLayout(file_stats_layout)
        hbox.addStretch(1)
        hbox.addLayout(token_stats_layout)

    def update_stats(self, total, selected, failed, success=0, draft=0):
        self.label_total.setText(f"Total Images: {total}")
        self.label_selected.setText(f"Selected: {selected}")
        self.label_failed.setText(f"Failed: {failed}")
        self.label_success.setText(f"Success: {success}")
        self.label_draft.setText(f"Draft: {draft}")

    def update_token_stats(self, token_input, token_output, token_total):
        self.label_token_input.setText(f"Token Input: {token_input}")
        self.label_token_output.setText(f"Token Output: {token_output}")
        self.label_token_total.setText(f"Token Total: {token_total}")
