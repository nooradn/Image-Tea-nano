from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout

class StatsSectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)

        hbox = QHBoxLayout()
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

        time_stats_layout = QVBoxLayout()
        time_stats_layout.setContentsMargins(0, 0, 0, 0)
        self.label_gen_time = QLabel("Generation Time: 0 ms")
        self.label_avg_time = QLabel("Average Time: 0 ms")
        self.label_longest_time = QLabel("Longest Time: 0 ms")
        self.label_last_time = QLabel("Last Time: 0 ms")
        self.label_total_time = QLabel("Total Time: 0 ms")
        time_stats_layout.addWidget(self.label_gen_time)
        time_stats_layout.addWidget(self.label_avg_time)
        time_stats_layout.addWidget(self.label_longest_time)
        time_stats_layout.addWidget(self.label_last_time)
        time_stats_layout.addWidget(self.label_total_time)

        hbox.addLayout(file_stats_layout)
        hbox.addSpacing(24)
        hbox.addLayout(token_stats_layout)
        hbox.addSpacing(24)
        hbox.addLayout(time_stats_layout)
        hbox.addStretch(1)

        main_vbox.addLayout(hbox)

        # Cache for timing stats
        self._last_gen_time = 0
        self._avg_time = 0
        self._longest_time = 0
        self._last_time = 0
        self._total_time = 0

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

    def _format_time(self, ms):
        if ms >= 60000:
            return f"{ms/60000:.1f} m"
        elif ms >= 1000:
            return f"{ms/1000:.1f} s"
        else:
            return f"{ms} ms"

    def update_generation_times(self, gen_time_ms, avg_time_ms, longest_time_ms, last_time_ms):
        self.label_gen_time.setText(f"Generation Time: {self._format_time(gen_time_ms)}")
        self.label_avg_time.setText(f"Average Time: {self._format_time(avg_time_ms)}")
        self.label_longest_time.setText(f"Longest Time: {self._format_time(longest_time_ms)}")
        self.label_last_time.setText(f"Last Time: {self._format_time(last_time_ms)}")
        self._last_gen_time = gen_time_ms
        self._avg_time = avg_time_ms
        self._longest_time = longest_time_ms
        self._last_time = last_time_ms

    def update_total_time(self, total_time_ms):
        self.label_total_time.setText(f"Total Time: {self._format_time(total_time_ms)}")
        self._total_time = total_time_ms

    def get_last_generation_times(self):
        return {
            "generation_time": self._last_gen_time,
            "average_time": self._avg_time,
            "longest_time": self._longest_time,
            "last_time": self._last_time,
            "total_time": self._total_time
        }
