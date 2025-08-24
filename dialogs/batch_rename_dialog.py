import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QComboBox, QRadioButton, QButtonGroup, QGroupBox,
    QFormLayout, QLineEdit, QCheckBox, QLabel, QHBoxLayout, QSpinBox, QPushButton, QWidget, QMessageBox
)
from PySide6.QtCore import Qt
from datetime import datetime
import re
import qtawesome as qta

class BatchRenameDialog(QDialog):
    VAR_COLORS = {
        "prefix": "#1976d2",
        "original": "#ff891a",
        "number": "#fbc02d",
        "suffix": "#388e3c",
        "timestamp": "#00A6C4",
        "date": "#d32f2f",
        "title": "#9508d1",
    }

    def __init__(self, parent=None, table_widget=None, db=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Rename")
        self.setFixedWidth(400)
        self.table_widget = table_widget
        self.db = db

        layout = QVBoxLayout(self)

        self.combo_mode = QComboBox(self)
        self.combo_mode.addItem("Rename All")
        self.combo_mode.addItem("Selected Only")
        self.combo_mode.setCurrentIndex(0)
        layout.addWidget(self.combo_mode)

        self.radio_same_as_title = QRadioButton("Same as Title", self)
        self.radio_custom = QRadioButton("Custom", self)

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.radio_same_as_title)
        self.button_group.addButton(self.radio_custom)
        self.radio_same_as_title.setChecked(True)

        layout.addWidget(self.radio_same_as_title)
        layout.addWidget(self.radio_custom)

        self.rename_group = QGroupBox("Custom Name", self)
        self.rename_group.setEnabled(False)
        group_layout = QFormLayout(self.rename_group)

        self.prefix_edit = QLineEdit(self.rename_group)
        group_layout.addRow("Prefix", self.prefix_edit)

        self.suffix_edit = QLineEdit(self.rename_group)
        group_layout.addRow("Suffix", self.suffix_edit)

        numbering_layout = QHBoxLayout()
        self.numbering_checkbox = QCheckBox("Add Numbering", self.rename_group)
        self.numbering_spin = QSpinBox(self.rename_group)
        self.numbering_spin.setMinimum(1)
        self.numbering_spin.setMaximum(10)
        self.numbering_spin.setValue(3)
        self.numbering_spin.setEnabled(False)
        numbering_layout.addWidget(self.numbering_checkbox)
        numbering_layout.addWidget(QLabel("Digits:", self.rename_group))
        numbering_layout.addWidget(self.numbering_spin)
        group_layout.addRow(numbering_layout)
        self.numbering_checkbox.toggled.connect(self.numbering_spin.setEnabled)

        self.timestamp_combo = QComboBox(self.rename_group)
        self.timestamp_combo.addItem("None")
        self.timestamp_combo.addItem("Timestamp")
        self.timestamp_combo.addItem("Date")
        group_layout.addRow("Timestamp/Date", self.timestamp_combo)

        self.remove_special_checkbox = QCheckBox("Remove Special Characters", self.rename_group)
        group_layout.addRow(self.remove_special_checkbox)

        self.replace_space_checkbox = QCheckBox("Replace space with underscore", self.rename_group)
        group_layout.addRow(self.replace_space_checkbox)

        self.radio_default_pattern = QRadioButton("Default Pattern", self.rename_group)
        self.radio_custom_pattern = QRadioButton("Custom Pattern", self.rename_group)
        self.pattern_mode_group = QButtonGroup(self.rename_group)
        self.pattern_mode_group.addButton(self.radio_default_pattern)
        self.pattern_mode_group.addButton(self.radio_custom_pattern)
        self.radio_default_pattern.setChecked(True)
        pattern_mode_layout = QHBoxLayout()
        pattern_mode_layout.addWidget(self.radio_default_pattern)
        pattern_mode_layout.addWidget(self.radio_custom_pattern)
        group_layout.addRow("Pattern Mode", pattern_mode_layout)

        self.pattern_edit = QLineEdit(self.rename_group)
        self.pattern_edit.setText("{prefix}_{title}_{suffix}")
        self.pattern_edit.setReadOnly(True)
        group_layout.addRow("Pattern", self.pattern_edit)

        variable_names = [
            "prefix", "original", "number", "suffix", "timestamp", "date", "title"
        ]
        self.checklist_widget = QWidget(self.rename_group)
        self.checklist_layout = QVBoxLayout(self.checklist_widget)
        self.checklist_layout.setContentsMargins(0, 0, 0, 0)
        self.check_vars = []
        self.pattern_order = [var for var in ["prefix", "title", "suffix"]]
        for i, var in enumerate(variable_names):
            h = QHBoxLayout()
            cb = QCheckBox(self.checklist_widget)
            cb.setChecked(var in self.pattern_order)
            color_label = QLabel(f"{{{var}}}", self.checklist_widget)
            color_label.setStyleSheet(f"color: {self.VAR_COLORS[var]}; font-weight: bold;")
            left_btn = QPushButton(self.checklist_widget)
            left_btn.setIcon(qta.icon('fa6s.angle-left'))
            left_btn.setFixedWidth(28)
            right_btn = QPushButton(self.checklist_widget)
            right_btn.setIcon(qta.icon('fa6s.angle-right'))
            right_btn.setFixedWidth(28)
            h.addWidget(cb)
            h.addWidget(color_label)
            h.addWidget(left_btn)
            h.addWidget(right_btn)
            self.checklist_layout.addLayout(h)
            self.check_vars.append((cb, left_btn, right_btn, var, color_label))
            cb.stateChanged.connect(self.update_checklist_pattern)
            left_btn.clicked.connect(lambda checked, v=var: self.move_pattern_var(v, -1))
            right_btn.clicked.connect(lambda checked, v=var: self.move_pattern_var(v, 1))
        group_layout.addRow("Checklist Variables", self.checklist_widget)

        self.preview_label = QLabel("Preview: ", self.rename_group)
        self.preview_label.setTextFormat(Qt.RichText)
        self.preview_label.setWordWrap(True)
        group_layout.addRow(self.preview_label)

        layout.addWidget(self.rename_group)

        self.info_label = QLabel(
            "<b>Info:</b> After renaming, you can restore the previous filename using Undo Rename if needed.",
            self
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        btn_layout = QHBoxLayout()
        self.undo_btn = QPushButton("Undo Rename", self)
        self.undo_btn.setIcon(qta.icon('fa6s.rotate-left'))
        btn_layout.addWidget(self.undo_btn)
        self.rename_btn = QPushButton("Rename", self)
        self.rename_btn.setIcon(qta.icon('fa6s.pen-to-square'))
        btn_layout.addWidget(self.rename_btn)

        layout.addLayout(btn_layout)
        self.rename_btn.clicked.connect(self.do_rename)
        self.undo_btn.clicked.connect(self.do_undo_rename)

        self.radio_same_as_title.toggled.connect(self._on_radio_toggle)
        self.radio_custom.toggled.connect(self._on_radio_toggle)
        self.radio_default_pattern.toggled.connect(self._on_pattern_mode_toggle)
        self.radio_custom_pattern.toggled.connect(self._on_pattern_mode_toggle)

        self.prefix_edit.textChanged.connect(self.update_preview)
        self.suffix_edit.textChanged.connect(self.update_preview)
        self.pattern_edit.textChanged.connect(self.update_preview)
        self.numbering_checkbox.toggled.connect(self.update_preview)
        self.numbering_spin.valueChanged.connect(self.update_preview)
        self.timestamp_combo.currentIndexChanged.connect(self.update_preview)
        self.remove_special_checkbox.toggled.connect(self.update_preview)
        self.replace_space_checkbox.toggled.connect(self.update_preview)

        self.setLayout(layout)
        self.update_preview()
        self._on_pattern_mode_toggle()

    def _on_radio_toggle(self):
        self.rename_group.setEnabled(self.radio_custom.isChecked())

    def _on_pattern_mode_toggle(self):
        custom_enabled = self.radio_custom_pattern.isChecked()
        self.pattern_edit.setReadOnly(True)
        self.checklist_widget.setEnabled(custom_enabled)
        if self.radio_default_pattern.isChecked():
            self.pattern_order = ["prefix", "title", "suffix"]
            self.pattern_edit.setText("{prefix}_{title}_{suffix}")
            # Set checklist to match default pattern
            for cb, _, _, var, _ in self.check_vars:
                cb.blockSignals(True)
                cb.setChecked(var in self.pattern_order)
                cb.blockSignals(False)
        elif self.radio_custom_pattern.isChecked():
            # Restore checklist to match current pattern_order (custom)
            for cb, _, _, var, _ in self.check_vars:
                cb.blockSignals(True)
                cb.setChecked(var in self.pattern_order)
                cb.blockSignals(False)
            self.update_checklist_pattern()
        self.update_preview()

    def update_checklist_pattern(self):
        checked_vars = []
        for cb, _, _, var, _ in self.check_vars:
            if cb.isChecked():
                checked_vars.append(var)
        self.pattern_order = [v for v in self.pattern_order if v in checked_vars]
        for v in checked_vars:
            if v not in self.pattern_order:
                self.pattern_order.append(v)
        pattern = "_".join(f"{{{v}}}" for v in self.pattern_order)
        self.pattern_edit.setText(pattern)
        self.update_preview()

    def move_pattern_var(self, var, direction):
        if var not in self.pattern_order:
            return
        idx = self.pattern_order.index(var)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.pattern_order):
            return
        self.pattern_order[idx], self.pattern_order[new_idx] = self.pattern_order[new_idx], self.pattern_order[idx]
        self.update_checklist_pattern()

    def update_preview(self):
        prefix = self.prefix_edit.text()
        suffix = self.suffix_edit.text()
        numbering = self.numbering_checkbox.isChecked()
        digits = self.numbering_spin.value()
        timestamp_mode = self.timestamp_combo.currentText()
        remove_special = self.remove_special_checkbox.isChecked()
        replace_space = self.replace_space_checkbox.isChecked()
        if self.radio_default_pattern.isChecked():
            pattern = "{prefix}_{title}_{suffix}"
        else:
            pattern = self.pattern_edit.text()

        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        today_timestamp = now.strftime("%Y%m%d_%H%M%S")
        timestamp_val = today_timestamp if (timestamp_mode == "Timestamp" or "{timestamp}" in pattern) else ""
        date_val = today_date if (timestamp_mode == "Date" or "{date}" in pattern) else ""

        example_title = "Title Example"
        # Remove ., ,, - from title for preview
        example_title = re.sub(r'[.,\-]', '', example_title)
        example_vars = {
            "prefix": prefix,
            "original": "original_name",
            "number": f"{1:0{digits}d}" if numbering else "",
            "suffix": suffix,
            "timestamp": timestamp_val,
            "date": date_val,
            "title": example_title
        }

        try:
            preview_raw = pattern.format(**example_vars)
        except Exception:
            preview_raw = "Invalid pattern"

        preview_raw = re.sub(r'_{2,}', '_', preview_raw)
        preview_raw = re.sub(r'_+\.', '.', preview_raw)
        preview_raw = re.sub(r'\._+', '.', preview_raw)
        preview_raw = re.sub(r'^_+|_+$', '', preview_raw)

        preview_html = preview_raw
        var_spans = []
        for var, color in self.VAR_COLORS.items():
            val = example_vars[var]
            if val:
                marker = f"__VAR_{var.upper()}__"
                preview_html = re.sub(
                    re.escape(val),
                    marker,
                    preview_html,
                    count=1
                )
                var_spans.append((marker, f'<span style="color:{color};font-weight:bold;">{val}</span>'))

        def process_outside_tags(html, func):
            parts = re.split(r'(<[^>]+>)', html)
            for i, part in enumerate(parts):
                if not part.startswith('<'):
                    parts[i] = func(part)
            return ''.join(parts)

        def remove_special_func(s):
            return re.sub(r'[^A-Za-z0-9_-]', '', s)

        def replace_space_func(s):
            return s.replace(' ', '_')

        if remove_special:
            preview_html = process_outside_tags(preview_html, remove_special_func)
        if replace_space:
            preview_html = process_outside_tags(preview_html, replace_space_func)

        for marker, span in var_spans:
            preview_html = preview_html.replace(marker, span, 1)

        self.preview_label.setText(f"Preview: {preview_html}")

    def _sanitize_windows_filename(self, name):
        # Windows forbidden chars: <>:"/\|?* and non-printable
        return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', name)

    def do_rename(self):
        mode = self.combo_mode.currentText()
        if mode == "Rename All":
            file_rows = [row for row in range(self.table_widget.table.rowCount())]
        else:
            file_rows = []
            for row in range(self.table_widget.table.rowCount()):
                checkbox_item = self.table_widget.table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    file_rows.append(row)
            if not file_rows:
                QMessageBox.information(self, "No Selection", "No rows checked for renaming.")
                return

        files = []
        for row in file_rows:
            filepath_item = self.table_widget.table.item(row, 1)
            filepath = filepath_item.data(Qt.UserRole) if filepath_item else None
            filename = self.table_widget.table.item(row, 2).text()
            title = self.table_widget.table.item(row, 3).text()
            description = self.table_widget.table.item(row, 4).text()
            tags = self.table_widget.table.item(row, 5).text()
            status = self.table_widget.table.item(row, 8).text()
            files.append({
                "filepath": filepath,
                "filename": filename,
                "title": title,
                "description": description,
                "tags": tags,
                "status": status,
                "row": row
            })

        def sanitize_title(title):
            if not title:
                return title
            return re.sub(r'[.,\-]', '', title)

        def sanitize_windows_filename(name):
            return self._sanitize_windows_filename(name)

        if self.radio_same_as_title.isChecked():
            def pattern_func(file_info, idx):
                base, ext = os.path.splitext(file_info['filename'])
                title = file_info['title'] or base
                title = sanitize_title(title)
                remove_special = self.remove_special_checkbox.isChecked()
                replace_space = self.replace_space_checkbox.isChecked()
                if remove_special:
                    title = re.sub(r'[^A-Za-z0-9_-]', '', title)
                if replace_space:
                    title = title.replace(' ', '_')
                safe_title = sanitize_windows_filename(title)
                return f"{safe_title}{ext}"
        else:
            def pattern_func(file_info, idx):
                pattern = self.pattern_edit.text()
                prefix = self.prefix_edit.text()
                suffix = self.suffix_edit.text()
                numbering = self.numbering_checkbox.isChecked()
                digits = self.numbering_spin.value()
                timestamp_mode = self.timestamp_combo.currentText()
                remove_special = self.remove_special_checkbox.isChecked()
                replace_space = self.replace_space_checkbox.isChecked()
                now = datetime.now()
                today_date = now.strftime("%Y-%m-%d")
                today_timestamp = now.strftime("%Y%m%d_%H%M%S")
                if "{original}" in pattern:
                    base, ext = os.path.splitext(file_info['filename'])
                else:
                    base, ext = "", os.path.splitext(file_info['filename'])[1]
                timestamp_val = today_timestamp if (timestamp_mode == "Timestamp" or "{timestamp}" in pattern) else ""
                date_val = today_date if (timestamp_mode == "Date" or "{date}" in pattern) else ""
                number_val = f"{idx+1:0{digits}d}" if numbering else ""
                sanitized_title = sanitize_title(file_info['title'] or base)
                vars_dict = {
                    "prefix": prefix,
                    "original": base,
                    "number": number_val,
                    "suffix": suffix,
                    "timestamp": timestamp_val,
                    "date": date_val,
                    "title": sanitized_title
                }
                try:
                    new_base = pattern.format(**vars_dict)
                except Exception:
                    new_base = base
                new_base = re.sub(r'_{2,}', '_', new_base)
                new_base = re.sub(r'_+\.', '.', new_base)
                new_base = re.sub(r'\._+', '.', new_base)
                new_base = re.sub(r'^_+|_+$', '', new_base)
                if remove_special:
                    new_base = re.sub(r'[^A-Za-z0-9_-]', '', new_base)
                if replace_space:
                    new_base = new_base.replace(' ', '_')
                safe_base = sanitize_windows_filename(new_base)
                return f"{safe_base}{ext}"

        confirm = QMessageBox.question(
            self,
            "Confirm Rename",
            "Are you sure you want to rename the selected files? After renaming, you can restore the previous filename using Undo Rename if needed.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        from helpers.file_renaming_helper import batch_rename_files

        try:
            results = batch_rename_files(files, pattern_func)
            self.db.batch_update_file_paths(results)
            self.table_widget.refresh_table()

            success_count = sum(1 for r in results if r[4])
            fail_count = len(results) - success_count
            msg = f"Renaming completed.\nSuccess: {success_count}\nFailed: {fail_count}"
            if fail_count > 0:
                msg += "\nSome files could not be renamed. See console for details."
                for r in results:
                    if not r[4]:
                        print(f"Failed to rename: {r[0]} -> {r[2]} | Error: {r[5]}")
            QMessageBox.information(self, "Batch Rename", msg)
        except Exception as e:
            print("Batch rename error:", e)
            raise

    def do_undo_rename(self):
        mode = self.combo_mode.currentText()
        if mode == "Rename All":
            file_rows = [row for row in range(self.table_widget.table.rowCount())]
        else:
            file_rows = []
            for row in range(self.table_widget.table.rowCount()):
                checkbox_item = self.table_widget.table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    file_rows.append(row)
            if not file_rows:
                QMessageBox.information(self, "No Selection", "No rows checked for undo rename.")
                return

        files = []
        for row in file_rows:
            filepath_item = self.table_widget.table.item(row, 1)
            filepath = filepath_item.data(Qt.UserRole) if filepath_item else None
            files.append(filepath)

        confirm = QMessageBox.question(
            self,
            "Confirm Undo Rename",
            "Are you sure you want to undo rename for the selected files? This will restore their original filenames if possible.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            self.db.undo_rename(files)
            self.table_widget.refresh_table()
            QMessageBox.information(self, "Undo Rename", "Undo rename completed. Filenames restored to their original names.")
        except Exception as e:
            print("Undo rename error:", e)
            raise