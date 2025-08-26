from PySide6.QtCore import QThread, Signal, Qt, QPoint, QTimer
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QProgressBar, QSizePolicy, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QApplication, QWidget, QFileDialog
from PySide6.QtGui import QColor, QBrush, QAction
from database.db_operation import ImageTeaDB
import datetime
import qtawesome as qta
import json
import os
import csv

class ApiKeyTestThread(QThread):
    result = Signal(str, str, object)  # (status, service, text/error)
    def __init__(self, api_key, service=None, model=None):
        super().__init__()
        self.api_key = api_key
        self.service = service
        self.model = model
    def run(self):
        if self.service == 'gemini' or self.service is None:
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                if not self.model:
                    raise RuntimeError("No model selected for Gemini API key test.")
                response = client.models.generate_content(
                    model=self.model,
                    contents="Just say OK."
                )
                if hasattr(response, 'text') and response.text:
                    self.result.emit('success', 'gemini', 'OK')
                    return
            except Exception as e:
                print(f"Gemini API Key test error: {e}")
                if self.service == 'gemini':
                    self.result.emit('fail', 'gemini', None)
                    return
        if self.service == 'openai' or self.service is None:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key)
                if not self.model:
                    raise RuntimeError("No model selected for OpenAI API key test.")
                response = client.responses.create(
                    model=self.model,
                    input="Just say OK."
                )
                if response:
                    self.result.emit('success', 'openai', 'OK')
                    return
            except Exception as e:
                print(f"OpenAI API Key test error: {e}")
                self.result.emit('fail', 'openai', None)
                return
        self.result.emit('fail', None, None)

class AddApiKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add API Key")
        self.setFixedWidth(500)
        self.db = ImageTeaDB()
        layout = QVBoxLayout()
        label_width = 80
        self.model_list = {}
        ai_prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "ai_config.json")
        try:
            with open(ai_prompt_path, "r", encoding="utf-8") as f:
                ai_prompt = json.load(f)
                self.model_list = ai_prompt["model_list"]
        except Exception as e:
            print(f"Failed to load model list: {e}")
            self.model_list = {}
        service_layout = QHBoxLayout()
        service_label = QLabel("Service:")
        service_label.setFixedWidth(label_width)
        service_label.setToolTip("Select the service/model for this API key")
        self.service_combo = QComboBox()
        self.service_combo.addItem("Gemini")
        self.service_combo.addItem("OpenAI")
        self.service_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.service_combo.setToolTip("Select the service/model for this API key")
        service_layout.addWidget(service_label)
        service_layout.addWidget(self.service_combo)
        layout.addLayout(service_layout)
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setFixedWidth(label_width)
        model_label.setToolTip("Select the model for this API key")
        self.model_combo = QComboBox()
        self.model_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.model_combo.setToolTip("Select the model for this API key")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        self._refresh_model_combo()
        key_layout = QHBoxLayout()
        self.key_label = QLabel("API Key:")
        self.key_label.setFixedWidth(label_width)
        self.key_label.setToolTip("Enter your API key here")
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Enter API Key")
        self.key_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.key_edit.setToolTip("Enter your API key here")
        self.paste_btn = QPushButton()
        self.paste_btn.setIcon(qta.icon('fa6s.paste'))
        self.paste_btn.setFixedWidth(32)
        self.paste_btn.setToolTip("Paste from clipboard")
        self.paste_btn.setFocusPolicy(Qt.NoFocus)
        self.paste_btn.clicked.connect(self._on_paste_clicked)
        key_layout.addWidget(self.key_label)
        key_layout.addWidget(self.key_edit)
        key_layout.addWidget(self.paste_btn)
        layout.addLayout(key_layout)
        note_layout = QHBoxLayout()
        note_label = QLabel("Note:")
        note_label.setFixedWidth(label_width)
        note_label.setToolTip("Optional note for this API key")
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Optional note")
        self.note_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.note_edit.setToolTip("Optional note for this API key")
        note_layout.addWidget(note_label)
        note_layout.addWidget(self.note_edit)
        layout.addLayout(note_layout)

        # Tombol Export/Import CSV di atas tabel
        csv_btn_layout = QHBoxLayout()
        self.test_all_btn = QPushButton()
        self.test_all_btn.setText("Test All")
        self.test_all_btn.setIcon(qta.icon('fa6s.list-check'))
        self.test_all_btn.setIconSize(self.test_all_btn.iconSize())
        self.test_all_btn.setToolTip("Test all API keys sequentially")
        self.export_csv_btn = QPushButton()
        self.export_csv_btn.setText("Export CSV")
        self.export_csv_btn.setIcon(qta.icon('fa6s.file-csv'))
        self.export_csv_btn.setIconSize(self.export_csv_btn.iconSize())
        self.export_csv_btn.setToolTip("Export API key list to CSV")
        self.import_csv_btn = QPushButton()
        self.import_csv_btn.setText("Import CSV")
        self.import_csv_btn.setIcon(qta.icon('fa6s.file-import'))
        self.import_csv_btn.setIconSize(self.import_csv_btn.iconSize())
        self.import_csv_btn.setToolTip("Import API key list from CSV")
        csv_btn_layout.addWidget(self.test_all_btn)
        csv_btn_layout.addWidget(self.export_csv_btn)
        csv_btn_layout.addWidget(self.import_csv_btn)
        csv_btn_layout.addStretch()
        layout.addLayout(csv_btn_layout)

        self.api_table = QTableWidget()
        self.api_table.setColumnCount(5)
        self.api_table.setHorizontalHeaderLabels(["Service", "API", "Last Tested", "Note", ""])
        self.api_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.api_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.api_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.api_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.api_table.setMinimumHeight(100)
        self.api_table.setToolTip("List of all API keys you have added")
        layout.addWidget(self.api_table)
        self._row_testing = None
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink_row)
        self._blink_state = False
        self._refresh_api_table()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress_bar.setToolTip("Shows progress when testing API key")
        layout.addWidget(self.progress_bar)
        btn_layout = QHBoxLayout()
        self.test_and_save_btn = QPushButton()
        self.test_and_save_btn.setText("Test and Save")
        self.test_and_save_btn.setIcon(qta.icon('fa6s.play'))
        self.test_and_save_btn.setIconSize(self.test_and_save_btn.iconSize())
        self.test_and_save_btn.setToolTip("Test the API key and save it if valid")
        self.close_btn = QPushButton()
        self.close_btn.setText("Close")
        self.close_btn.setIcon(qta.icon('fa6s.xmark'))
        self.close_btn.setIconSize(self.close_btn.iconSize())
        self.close_btn.setToolTip("Close this dialog")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.test_and_save_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.test_and_save_btn.clicked.connect(self.test_and_save_api_key)
        self.export_csv_btn.clicked.connect(self.export_api_keys_csv)
        self.import_csv_btn.clicked.connect(self.import_api_keys_csv)
        self.test_all_btn.clicked.connect(self.test_all_api_keys)
        self.key_edit.textChanged.connect(self._on_key_edit_changed)
        self.service_combo.currentIndexChanged.connect(self._on_service_combo_changed)
        self.api_table.cellClicked.connect(self._on_api_table_row_clicked)
        self.api_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.api_table.customContextMenuRequested.connect(self._show_context_menu)
        self.model_combo.currentIndexChanged.connect(self._on_model_combo_changed)
        self._detected_service = None
        self._api_key_valid = False
        self._testing = False
        self._test_all_running = False
        self._test_all_results = []
        self._test_all_row_blinking = False

    def _on_paste_clicked(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        self.key_edit.setText(text)

    def _refresh_model_combo(self):
        service = self.service_combo.currentText().lower()
        self.model_combo.clear()
        if service == "gemini":
            models = self.model_list["gemini"]
        elif service == "openai":
            models = self.model_list["openai"]
        else:
            models = []
        for m in models:
            self.model_combo.addItem(m)
        if self.model_combo.count() > 0:
            self.model_combo.setCurrentIndex(0)

    def _refresh_api_table(self):
        try:
            rows = self.db.get_all_api_keys()
        except Exception:
            rows = []
        self.api_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            if isinstance(row, dict):
                service = row["service"]
                api = row["api"]
                note = row["note"]
                last_tested = row["last_tested"]
                status = row["status"]
            else:
                if len(row) == 6:
                    service, api, note, last_tested, status, model = row
                elif len(row) == 5:
                    service, api, note, last_tested, status = row
                    model = ""
                else:
                    service, api, note, last_tested = row
                    status = ""
                    model = ""
            if isinstance(last_tested, (tuple, list)):
                last_tested = " ".join(str(x) for x in last_tested)
            self.api_table.setItem(row_idx, 0, QTableWidgetItem(str(service.capitalize() if str(service).lower() in ("openai", "gemini") else str(service))))
            self.api_table.setItem(row_idx, 1, QTableWidgetItem(str(api)))
            self.api_table.setItem(row_idx, 2, QTableWidgetItem(str(last_tested)))
            self.api_table.setItem(row_idx, 3, QTableWidgetItem(str(note)))
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            test_btn = QPushButton()
            test_btn.setIcon(qta.icon('fa6s.play'))
            test_btn.setToolTip("Test this API Key")
            test_btn.setFixedWidth(28)
            test_btn.setProperty("row", row_idx)
            test_btn.clicked.connect(lambda _, r=row_idx: self._test_api_key_row(r))
            delete_btn = QPushButton()
            delete_btn.setIcon(qta.icon('fa6s.trash'))
            delete_btn.setToolTip("Delete this API Key")
            delete_btn.setFixedWidth(28)
            delete_btn.setProperty("row", row_idx)
            delete_btn.clicked.connect(lambda _, r=row_idx: self._delete_api_key_row(r))
            action_layout.addWidget(test_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addStretch()
            self.api_table.setCellWidget(row_idx, 4, action_widget)
            if status == "active":
                brush = QBrush(QColor(91, 184, 16, int(0.4 * 255)))
            elif status == "invalid":
                brush = QBrush(QColor(255, 41, 41, int(0.4 * 255)))
            else:
                brush = None
            if brush:
                for col in range(4):
                    item = self.api_table.item(row_idx, col)
                    if item:
                        item.setBackground(brush)
        self._stop_blinking()

    def _test_api_key_row(self, row):
        if self._row_testing is not None:
            return
        service_item = self.api_table.item(row, 0)
        api_item = self.api_table.item(row, 1)
        if not service_item or not api_item:
            return
        service = service_item.text().lower()
        api_key = api_item.text().strip()
        model = None
        try:
            rows = self.db.get_all_api_keys()
            if row < len(rows):
                if isinstance(rows[row], dict):
                    model = rows[row].get("model")
                elif len(rows[row]) == 6:
                    model = rows[row][5]
        except Exception:
            pass
        test_btn = self._get_action_btn(row, 0)
        if test_btn:
            test_btn.setIcon(qta.icon('fa6s.stop'))
            test_btn.setToolTip("Stop testing")
        self._row_testing = row
        self._blink_state = False
        self._blink_timer.start(300)
        self._test_thread_row = ApiKeyTestThread(api_key, service, model)
        self._test_thread_row.result.connect(lambda status, service, text: self._on_test_row_result(row, status, service, text))
        self._test_thread_row.finished.connect(lambda: self._stop_blinking())
        self._test_thread_row.start()

    def _on_test_row_result(self, row, status, service, text):
        self._stop_blinking()
        self._refresh_api_table()
        if status == 'success':
            QMessageBox.information(self, "API Key Test", "API Key is valid and active.")
        else:
            QMessageBox.critical(self, "API Key Test", "API Key invalid or not supported.")

    def _get_action_btn(self, row, btn_idx):
        widget = self.api_table.cellWidget(row, 4)
        if widget:
            layout = widget.layout()
            if layout and layout.count() > btn_idx:
                return layout.itemAt(btn_idx).widget()
        return None

    def _blink_row(self):
        if self._row_testing is None:
            return
        color1 = QColor(255, 255, 128, 180)
        color2 = QColor(255, 255, 255, 0)
        color = color1 if self._blink_state else color2
        for col in range(4):
            item = self.api_table.item(self._row_testing, col)
            if item:
                item.setBackground(QBrush(color))
        self._blink_state = not self._blink_state

    def _stop_blinking(self):
        if self._row_testing is not None:
            test_btn = self._get_action_btn(self._row_testing, 0)
            if test_btn:
                test_btn.setIcon(qta.icon('fa6s.play'))
                test_btn.setToolTip("Test this API Key")
        self._blink_timer.stop()
        if self._row_testing is not None:
            for col in range(4):
                item = self.api_table.item(self._row_testing, col)
                if item:
                    item.setBackground(QBrush())
        self._row_testing = None
        self._blink_state = False

    def _delete_api_key_row(self, row):
        if self._row_testing == row:
            self._stop_blinking()
        service_item = self.api_table.item(row, 0)
        api_item = self.api_table.item(row, 1)
        if not service_item or not api_item:
            return
        service = service_item.text().lower()
        api_key = api_item.text().strip()
        if not api_key or not service:
            QMessageBox.warning(self, "Delete API Key", "No API Key selected to delete.")
            return
        confirm = QMessageBox.question(self, "Delete API Key", f"Delete API Key for '{service}'?\nThis cannot be undone.", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.db.delete_api_key(service, api_key)
            self._refresh_api_table()
            self.key_edit.clear()
            self.note_edit.clear()

    def _on_api_table_row_clicked(self, row, column):
        if column == 4:
            return
        service_item = self.api_table.item(row, 0)
        api_item = self.api_table.item(row, 1)
        note_item = self.api_table.item(row, 3)
        if service_item and api_item:
            service_text = service_item.text()
            api_text = api_item.text()
            note_text = note_item.text() if note_item else ""
            self.key_edit.setText(api_text)
            self.note_edit.setText(note_text)
            self.service_combo.setCurrentText(service_text.capitalize())
            self._refresh_model_combo()
            if self.model_combo.count() > 0:
                self.model_combo.setCurrentIndex(0)
            if service_text.lower() == "openai":
                self._detected_service = "openai"
            elif service_text.lower() == "gemini":
                self._detected_service = "gemini"
            else:
                self._detected_service = None

    def _on_key_edit_changed(self, text):
        api_key = text.strip()
        service = None
        if api_key.startswith('sk-') and len(api_key) > 40:
            service = 'openai'
        elif len(api_key) > 30 and 'AIza' in api_key:
            service = 'gemini'
        else:
            service = None
        if service == 'openai':
            self.service_combo.setCurrentText("OpenAI")
        elif service == 'gemini':
            self.service_combo.setCurrentText("Gemini")
        self._detected_service = service
        self._api_key_valid = False
        self.progress_bar.setVisible(False)

    def _on_service_combo_changed(self, idx):
        if self.service_combo.currentText() == "OpenAI":
            self._detected_service = 'openai'
        elif self.service_combo.currentText() == "Gemini":
            self._detected_service = 'gemini'
        else:
            self._detected_service = None
        self._refresh_model_combo()
        self._api_key_valid = False

    def _on_model_combo_changed(self, idx):
        pass

    def _start_test_thread(self, api_key, service):
        if self._testing:
            return
        self._testing = True
        self.progress_bar.setVisible(True)
        self.test_and_save_btn.setEnabled(False)
        model = self.model_combo.currentText() if self.model_combo.count() > 0 else None
        self._test_thread = ApiKeyTestThread(api_key, service, model)
        self._test_thread.result.connect(self._on_test_result_auto)
        self._test_thread.finished.connect(lambda: self._set_testing(False))
        self._test_thread.finished.connect(lambda: self.test_and_save_btn.setEnabled(True))
        self._test_thread.finished.connect(lambda: self.progress_bar.setVisible(False))
        self._test_thread.start()

    def _set_testing(self, val):
        self._testing = val

    def _on_test_result_auto(self, status, service, text):
        if status == 'success':
            self._detected_service = service
            self._api_key_valid = True
        else:
            self._api_key_valid = False

    def test_and_save_api_key(self):
        api_key = self.key_edit.text().strip()
        note = self.note_edit.text().strip()
        service = self._detected_service
        model = self.model_combo.currentText() if self.model_combo.count() > 0 else None
        if not api_key:
            QMessageBox.warning(self, "Input Error", "API Key cannot be empty.")
            return
        if not service:
            QMessageBox.warning(self, "Input Error", "API Key format not recognized as Gemini or OpenAI.")
            return
        if not model:
            QMessageBox.warning(self, "Input Error", "Model must be selected.")
            return
        self.progress_bar.setVisible(True)
        self.test_and_save_btn.setEnabled(False)
        self._test_thread = ApiKeyTestThread(api_key, service, model)
        self._test_thread.result.connect(lambda status, service, text: self._on_test_and_save_result(status, service, text, note, model))
        self._test_thread.finished.connect(lambda: self.test_and_save_btn.setEnabled(True))
        self._test_thread.finished.connect(lambda: self.progress_bar.setVisible(False))
        self._test_thread.start()

    def _on_test_and_save_result(self, status, service, text, note, model):
        if status == 'success':
            self._detected_service = service
            self._api_key_valid = True
            last_tested = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.set_api_key(service, self.key_edit.text().strip(), note, last_tested, status="active", model=model)
            self._refresh_api_table()
            self.key_edit.clear()
            self.note_edit.clear()
            api_exists = False
            try:
                rows = self.db.get_all_api_keys()
                for row in rows:
                    if isinstance(row, dict):
                        if row["service"] == service and row["api"] == self.key_edit.text().strip():
                            api_exists = True
                            break
                    else:
                        if len(row) == 5:
                            s, a, n, lt, st = row
                        else:
                            s, a, n, lt = row
                            st = ""
                        if s == service and a == self.key_edit.text().strip():
                            api_exists = True
                            break
            except Exception:
                pass
            if api_exists:
                QMessageBox.information(self, "Saved", f"API Key for '{service}' is valid and active, ready to use.")
            else:
                QMessageBox.information(self, "Saved", f"API Key for '{service}' saved.")
        else:
            self._api_key_valid = False
            last_tested = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.set_api_key(service, self.key_edit.text().strip(), note, last_tested, status="invalid", model=model)
            self._refresh_api_table()
            QMessageBox.critical(self, "Test API Key", "API Key invalid or not supported.")

    def delete_api_key(self):
        service = self.service_combo.currentText().lower()
        api_key = self.key_edit.text().strip()
        if not api_key or not service:
            QMessageBox.warning(self, "Delete API Key", "No API Key selected to delete.")
            return
        confirm = QMessageBox.question(self, "Delete API Key", f"Delete API Key for '{service}'?\nThis cannot be undone.", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.db.delete_api_key(service, api_key)
            self._refresh_api_table()
            self.key_edit.clear()
            self.note_edit.clear()

    def _show_context_menu(self, pos: QPoint):
        index = self.api_table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        self.api_table.selectRow(row)
        service_item = self.api_table.item(row, 0)
        api_item = self.api_table.item(row, 1)
        note_item = self.api_table.item(row, 3)
        if not service_item or not api_item:
            return
        service_text = service_item.text()
        api_text = api_item.text()
        note_text = note_item.text() if note_item else ""
        self.key_edit.setText(api_text)
        self.note_edit.setText(note_text)
        self.service_combo.setCurrentText(service_text.capitalize())
        self._refresh_model_combo()
        if self.model_combo.count() > 0:
            self.model_combo.setCurrentIndex(0)
        if service_text.lower() == "openai":
            self._detected_service = "openai"
        elif service_text.lower() == "gemini":
            self._detected_service = "gemini"
        else:
            self._detected_service = None
        menu = QMenu(self)
        action_test = QAction(qta.icon('fa6s.play'), "Test and Save", self)
        action_test.triggered.connect(self.test_and_save_api_key)
        menu.addAction(action_test)
        menu.exec(self.api_table.viewport().mapToGlobal(pos))

    def export_api_keys_csv(self):
        try:
            rows = self.db.get_all_api_keys()
        except Exception as e:
            print(f"Error fetching API keys for export: {e}")
            QMessageBox.critical(self, "Export CSV", "Failed to fetch API Key data.")
            return
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        home_dir = os.path.expanduser("~")
        default_filename = f"Image_Tea_API_Keys_Backup_{now}.csv"
        default_path = os.path.join(home_dir, default_filename)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export API Keys to CSV",
            default_path,
            "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
        headers = ["Service", "API", "Last Tested", "Note", "Status", "Model"]
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                writer.writerow(headers)
                for row in rows:
                    if isinstance(row, dict):
                        service = row.get("service")
                        api = row.get("api")
                        last_tested = row.get("last_tested")
                        note = row.get("note")
                        status = row.get("status")
                        model = row.get("model")
                    else:
                        if len(row) == 6:
                            service, api, note, last_tested, status, model = row
                        elif len(row) == 5:
                            service, api, note, last_tested, status = row
                            model = ""
                        else:
                            service, api, note, last_tested = row
                            status = ""
                            model = ""
                    if isinstance(last_tested, (tuple, list)):
                        last_tested = " ".join(str(x) for x in last_tested)
                    writer.writerow([service, api, last_tested, note, status, model])
            QMessageBox.information(self, "Export CSV", f"API Keys exported successfully to:\n{file_path}")
        except Exception as e:
            print(f"Error exporting API keys to CSV: {e}")
            QMessageBox.critical(self, "Export CSV", "Failed to write CSV file.")

    def import_api_keys_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import API Keys from CSV",
            os.path.expanduser("~"),
            "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
        imported = 0
        skipped = 0
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    service = row.get("Service")
                    api = row.get("API")
                    last_tested = row.get("Last Tested")
                    note = row.get("Note")
                    status = row.get("Status")
                    model = row.get("Model")
                    if not service or not api:
                        continue
                    # Cek apakah sudah ada di DB
                    exists = False
                    try:
                        db_rows = self.db.get_all_api_keys()
                        for db_row in db_rows:
                            if isinstance(db_row, dict):
                                if db_row.get("service") == service and db_row.get("api") == api:
                                    exists = True
                                    break
                            else:
                                if len(db_row) >= 2 and db_row[0] == service and db_row[1] == api:
                                    exists = True
                                    break
                    except Exception as e:
                        print(f"Error checking existing API key: {e}")
                    if exists:
                        skipped += 1
                        continue
                    # Simpan ke DB
                    try:
                        self.db.set_api_key(service, api, note, last_tested, status, model)
                        imported += 1
                    except Exception as e:
                        print(f"Error saving API key: {e}")
            self._refresh_api_table()
            QMessageBox.information(self, "Import CSV", f"Import finished.\nImported: {imported}\nSkipped (already exists): {skipped}")
        except Exception as e:
            print(f"Error importing API keys from CSV: {e}")
            QMessageBox.critical(self, "Import CSV", "Failed to import API keys from CSV.")

    def test_all_api_keys(self):
        if self._test_all_running:
            return
        self._test_all_running = True
        self._test_all_results = []
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.test_all_btn.setEnabled(False)
        self._test_all_index = 0
        try:
            self._test_all_rows = self.db.get_all_api_keys()
        except Exception as e:
            print(f"Error fetching API keys for test all: {e}")
            self._test_all_rows = []
        self._test_all_next()

    def _test_all_next(self):
        if self._test_all_index >= len(self._test_all_rows):
            self._stop_blinking()
            self.progress_bar.setVisible(False)
            self.test_all_btn.setEnabled(True)
            self._test_all_running = False
            self._refresh_api_table()
            total = len(self._test_all_rows)
            ok = sum(1 for r in self._test_all_results if r[1] == "success")
            fail = total - ok
            QMessageBox.information(self, "Test All API Keys", f"Tested {total} API keys.\nSuccess: {ok}\nFailed: {fail}")
            return
        row = self._test_all_rows[self._test_all_index]
        if isinstance(row, dict):
            service = row["service"]
            api = row["api"]
            note = row.get("note")
            model = row.get("model")
        else:
            if len(row) == 6:
                service, api, note, last_tested, status, model = row
            elif len(row) == 5:
                service, api, note, last_tested, status = row
                model = ""
            else:
                service, api, note, last_tested = row
                status = ""
                model = ""
        if not model:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.set_api_key(service, api, note, now, "invalid", model)
            self._test_all_results.append((api, "fail"))
            self._set_row_status_color(self._test_all_index, "invalid")
            self._test_all_index += 1
            self._test_all_next()
            return
        self._row_testing = self._test_all_index
        self._blink_state = False
        self._blink_timer.start(300)
        self._test_all_thread = ApiKeyTestThread(api, service, model)
        self._test_all_thread.result.connect(lambda status, svc, text, idx=self._test_all_index: self._on_test_all_result(idx, status, svc, text))
        self._test_all_thread.finished.connect(self._test_all_blink_stop_and_next)
        self._test_all_thread.start()

    def _test_all_blink_stop_and_next(self):
        self._stop_blinking()
        # Set warna baris sesuai hasil tes terakhir
        if self._test_all_index < len(self._test_all_results):
            status = self._test_all_results[self._test_all_index][1]
            self._set_row_status_color(self._test_all_index, status)
        self._test_all_index += 1
        self._test_all_next()

    def _set_row_status_color(self, row_idx, status):
        if status == "success":
            brush = QBrush(QColor(91, 184, 16, int(0.4 * 255)))
        elif status == "invalid" or status == "fail":
            brush = QBrush(QColor(255, 41, 41, int(0.4 * 255)))
        else:
            brush = None
        if brush:
            for col in range(4):
                item = self.api_table.item(row_idx, col)
                if item:
                    item.setBackground(brush)
        else:
            for col in range(4):
                item = self.api_table.item(row_idx, col)
                if item:
                    item.setBackground(QBrush())

    def _on_test_all_result(self, idx, status, service, text):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row = self._test_all_rows[idx]
        if isinstance(row, dict):
            api = row["api"]
            note = row.get("note")
            model = row.get("model")
        else:
            if len(row) == 6:
                service, api, note, last_tested, st, model = row
            elif len(row) == 5:
                service, api, note, last_tested, st = row
                model = ""
            else:
                service, api, note, last_tested = row
                st = ""
                model = ""
        self.db.set_api_key(service, api, note, now, "active" if status == "success" else "invalid", model)
        self._test_all_results.append((api, status))
