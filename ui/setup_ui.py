from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QLineEdit, QProgressBar
import datetime
from dialogs.add_api_key_dialog import AddApiKeyDialog
from ui.file_dnd_widget import DragDropWidget
import qtawesome as qta
from ui.main_table import ImageTableWidget

def setup_ui(self):
    from database.db_operation import ImageTeaDB
    self.db = getattr(self, 'db', None) or ImageTeaDB()
    central = QWidget()
    layout = QVBoxLayout()
    api_layout = QHBoxLayout()
    from PySide6.QtWidgets import QSizePolicy

    api_keys = self.db.get_all_api_keys()
    model_set = []
    for entry in api_keys:
        if len(entry) == 5:
            service, api_key, note, last_tested, status = entry
        else:
            service, api_key, note, last_tested = entry
        service_disp = service.capitalize() if service.lower() in ("openai", "gemini") else service
        if service_disp not in model_set:
            model_set.append(service_disp)

    icon_label = QLabel(" ")
    icon = qta.icon('fa5s.key')
    pixmap = icon.pixmap(16, 16)
    icon_label.setPixmap(pixmap)
    api_layout.addWidget(icon_label)

    api_key_label = QLabel("API Key:")
    api_key_label.setToolTip("API Key management area")
    api_layout.addWidget(api_key_label)

    self.model_combo = QComboBox()
    self.model_combo.setEditable(False)
    self.model_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    self.model_combo.setFixedWidth(120)
    self.model_combo.setToolTip("Select the model/service to filter API keys")
    for model in model_set:
        self.model_combo.addItem(model)
    api_layout.addWidget(self.model_combo)

    self.api_key_combo = QComboBox()
    self.api_key_combo.setEditable(False)
    self.api_key_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    self.api_key_combo.setToolTip("Select the API key to use for the selected model")
    self.api_key_map = {}

    def refresh_api_key_combo(selected_model=None):
        self.api_key_combo.clear()
        self.api_key_map.clear()
        api_keys = self.db.get_all_api_keys()
        for entry in api_keys:
            if len(entry) == 5:
                service, api_key, note, last_tested, status = entry
            else:
                service, api_key, note, last_tested = entry
            service_disp = service.capitalize() if service.lower() in ("openai", "gemini") else service
            if selected_model is None or service_disp == selected_model:
                label = f"{api_key} ({note})" if note else api_key
                self.api_key_combo.addItem(label, api_key)
                self.api_key_map[api_key] = {'service': service_disp, 'note': note, 'last_tested': last_tested}
        if self.api_key_combo.count() > 0:
            self.api_key_combo.setCurrentIndex(0)
            api_key = self.api_key_combo.currentData()
            self.api_key = api_key
            if hasattr(self, 'last_tested_label'):
                last_tested = self.api_key_map[api_key]['last_tested']
                self.last_tested_label.setText(f"Last Tested: {last_tested}" if last_tested else "Last Tested: -")
        else:
            self.api_key = None
            if hasattr(self, 'last_tested_label'):
                self.last_tested_label.setText("Last Tested: -")

    def on_model_combo_changed(idx):
        selected_model = self.model_combo.currentText()
        refresh_api_key_combo(selected_model)

    self.model_combo.currentIndexChanged.connect(on_model_combo_changed)

    def on_api_combo_changed(idx):
        api_key = self.api_key_combo.itemData(idx)
        if api_key and api_key in self.api_key_map:
            self.api_key = api_key
            if hasattr(self, 'last_tested_label'):
                last_tested = self.api_key_map[api_key]['last_tested']
                self.last_tested_label.setText(f"Last Tested: {last_tested}" if last_tested else "Last Tested: -")
        else:
            self.api_key = None
            if hasattr(self, 'last_tested_label'):
                self.last_tested_label.setText("Last Tested: -")

    self.api_key_combo.currentIndexChanged.connect(on_api_combo_changed)

    api_refresh_btn = QPushButton()
    api_refresh_btn.setIcon(qta.icon('fa5s.sync'))
    api_refresh_btn.setFixedWidth(32)
    api_refresh_btn.setToolTip("Reload API key and model list from database")
    def reload_api_keys():
        api_keys = self.db.get_all_api_keys()
        model_set = []
        for entry in api_keys:
            if len(entry) == 5:
                service, api_key, note, last_tested, status = entry
            else:
                service, api_key, note, last_tested = entry
            service_disp = service.capitalize() if service.lower() in ("openai", "gemini") else service
            if service_disp not in model_set:
                model_set.append(service_disp)
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for model in model_set:
            self.model_combo.addItem(model)
        self.model_combo.blockSignals(False)
        if self.model_combo.count() > 0:
            self.model_combo.setCurrentIndex(0)
            selected_model = self.model_combo.currentText()
        else:
            selected_model = None
        refresh_api_key_combo(selected_model)
        if self.api_key_combo.count() > 0:
            self.api_key_combo.setCurrentIndex(0)
            self.api_key = self.api_key_combo.currentData()
        else:
            self.api_key = None
    api_refresh_btn.clicked.connect(reload_api_keys)

    api_save_btn = QPushButton(qta.icon('fa5s.save'), "Add API Key")
    api_save_btn.setToolTip("Add a new API key for the selected model")
    def show_add_api_key_dialog():
        dlg = AddApiKeyDialog(self)
        dlg.exec()
        reload_api_keys()
    api_save_btn.clicked.connect(show_add_api_key_dialog)

    api_layout.addWidget(self.api_key_combo)
    api_layout.addWidget(api_refresh_btn)
    api_layout.addWidget(api_save_btn)
    layout.addLayout(api_layout)

    self.last_tested_label = QLabel()
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    self.last_tested_label.setText(f"Last Tested: {now_str}")
    self.last_tested_label.setToolTip("Shows the last time the selected API key was tested")
    layout.addWidget(self.last_tested_label)
    self.progress_bar = QProgressBar()
    self.progress_bar.setMinimum(0)
    self.progress_bar.setMaximum(100)
    self.progress_bar.setValue(0)
    self.progress_bar.setTextVisible(True)
    self.progress_bar.setFormat('')
    self.progress_bar.setVisible(False)
    self.progress_bar.setToolTip("Shows progress for batch operations")
    layout.addWidget(self.progress_bar)
    self.dnd_widget = DragDropWidget(self)
    layout.addWidget(self.dnd_widget)
    self.table = ImageTableWidget(self)
    layout.addWidget(self.table)
    btn_layout = QHBoxLayout()
    import_btn = QPushButton(qta.icon('fa5s.folder-open'), "Import Files")
    import_btn.setToolTip("Import images or videos from your computer")
    import_btn.clicked.connect(self.import_images)
    gen_btn = QPushButton(qta.icon('fa5s.magic'), "Generate Metadata (Batch)")
    gen_btn.setToolTip("Generate metadata for all images in the table")
    gen_btn.clicked.connect(self.batch_generate_metadata)
    write_btn = QPushButton(qta.icon('fa5s.save'), "Write Metadata to Images")
    write_btn.setToolTip("Write the generated metadata back to the image files")
    write_btn.clicked.connect(self.write_metadata_to_images)
    del_btn = QPushButton(qta.icon('fa5s.trash'), "Delete Selected")
    del_btn.setToolTip("Delete the selected images from the table and database")
    del_btn.clicked.connect(self.delete_selected)
    clear_btn = QPushButton(qta.icon('fa5s.broom'), "Clear All")
    clear_btn.setToolTip("Remove all images from the table and database")
    clear_btn.clicked.connect(self.clear_all)
    btn_layout.addWidget(import_btn)
    btn_layout.addWidget(gen_btn)
    btn_layout.addWidget(write_btn)
    btn_layout.addWidget(del_btn)
    btn_layout.addWidget(clear_btn)
    layout.addLayout(btn_layout)
    central.setLayout(layout)
    self.setCentralWidget(central)

    # Initial population
    if self.model_combo.count() > 0:
        refresh_api_key_combo(self.model_combo.currentText())
    else:
        refresh_api_key_combo(None)
