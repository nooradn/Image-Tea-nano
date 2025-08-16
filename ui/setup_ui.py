from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFrame
import datetime
from dialogs.add_api_key_dialog import AddApiKeyDialog
from ui.file_dnd_widget import DragDropWidget
import qtawesome as qta
from ui.main_table import ImageTableWidget
from ui.prompt_section import PromptSectionWidget
from ui.stats_section import StatsSectionWidget

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
        if len(entry) == 6:
            service, api_key, note, last_tested, status, model = entry
        elif len(entry) == 5:
            service, api_key, note, last_tested, status = entry
            model = ""
        else:
            service, api_key, note, last_tested = entry
            status = ""
            model = ""
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
            if len(entry) == 6:
                service, api_key, note, last_tested, status, model = entry
            elif len(entry) == 5:
                service, api_key, note, last_tested, status = entry
                model = ""
            else:
                service, api_key, note, last_tested = entry
                status = ""
                model = ""
            service_disp = service.capitalize() if service.lower() in ("openai", "gemini") else service
            if selected_model is None or service_disp == selected_model:
                label = f"{api_key} ({note})" if note else api_key
                self.api_key_combo.addItem(label, api_key)
                self.api_key_map[api_key] = {'service': service_disp, 'note': note, 'last_tested': last_tested, 'model': model}
        if self.api_key_combo.count() > 0:
            self.api_key_combo.setCurrentIndex(0)
            api_key = self.api_key_combo.currentData()
            self.api_key = api_key
            if hasattr(self, 'last_tested_label'):
                last_tested = self.api_key_map[api_key]['last_tested']
                model = self.api_key_map[api_key]['model']
                self.last_tested_label.setText(f"Last Tested: {last_tested if last_tested else '-'} | Model: {model if model else '-'}")
        else:
            self.api_key = None
            if hasattr(self, 'last_tested_label'):
                self.last_tested_label.setText("Last Tested: - | Model: -")

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
                model = self.api_key_map[api_key]['model']
                self.last_tested_label.setText(f"Last Tested: {last_tested if last_tested else '-'} | Model: {model if model else '-'}")
        else:
            self.api_key = None
            if hasattr(self, 'last_tested_label'):
                self.last_tested_label.setText("Last Tested: - | Model: -")

    self.api_key_combo.currentIndexChanged.connect(on_api_combo_changed)

    api_refresh_btn = QPushButton()
    api_refresh_btn.setIcon(qta.icon('fa5s.sync'))
    api_refresh_btn.setFixedWidth(32)
    api_refresh_btn.setToolTip("Reload API key and model list from database")
    def reload_api_keys():
        api_keys = self.db.get_all_api_keys()
        model_set = []
        for entry in api_keys:
            if len(entry) == 6:
                service, api_key, note, last_tested, status, model = entry
            elif len(entry) == 5:
                service, api_key, note, last_tested, status = entry
                model = ""
            else:
                service, api_key, note, last_tested = entry
                status = ""
                model = ""
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
    self.last_tested_label.setText(f"Last Tested: {now_str} | Model: -")
    self.last_tested_label.setToolTip("Shows the last time the selected API key was tested and its model")
    layout.addWidget(self.last_tested_label)

    self.prompt_section = PromptSectionWidget(self)
    layout.addWidget(self.prompt_section)

    # Grup tombol import/delete/clear di kiri dan write metadata di kanan atas tabel
    top_btn_layout = QHBoxLayout()
    left_btn_group = QHBoxLayout()
    right_btn_group = QHBoxLayout()

    import_btn = QPushButton(qta.icon('fa5s.folder-open'), "Import Files")
    import_btn.setToolTip("Import images or videos from your computer")
    import_btn.clicked.connect(self.import_images)

    del_btn = QPushButton(qta.icon('fa5s.trash'), "Delete Selected")
    del_btn.setToolTip("Delete the selected images from the table and database")
    del_btn.clicked.connect(self.delete_selected)

    clear_btn = QPushButton(qta.icon('fa5s.broom'), "Clear All")
    clear_btn.setToolTip("Remove all images from the table and database")
    clear_btn.clicked.connect(self.clear_all)

    write_btn = QPushButton(qta.icon('fa5s.save'), "Write Metadata to Images")
    write_btn.setToolTip("Write the generated metadata back to the image files")
    write_btn.clicked.connect(self.write_metadata_to_images)

    left_btn_group.addWidget(import_btn)
    left_btn_group.addWidget(del_btn)
    left_btn_group.addWidget(clear_btn)

    right_btn_group.addWidget(write_btn)

    top_btn_layout.addLayout(left_btn_group)
    top_btn_layout.addStretch()
    top_btn_layout.addLayout(right_btn_group)
    layout.addLayout(top_btn_layout)

    self.table = ImageTableWidget(self)
    layout.addWidget(self.table)

    self.dnd_widget = DragDropWidget(self)
    layout.addWidget(self.dnd_widget)

    # Grup generate metadata: stats_section di kiri sebaris dengan tombol generate di kanan bawah tabel
    btn_row_layout = QHBoxLayout()
    self.stats_section = StatsSectionWidget(self)
    btn_row_layout.addWidget(self.stats_section)

    btn_row_layout.addStretch()

    gen_group_layout = QVBoxLayout()
    self.gen_mode_combo = QComboBox()
    self.gen_mode_combo.addItems(["Generate All", "Selected Only", "Failed Only"])
    self.gen_mode_combo.setToolTip("Choose which files to generate metadata for")
    gen_group_layout.addWidget(self.gen_mode_combo)

    gen_btn = QPushButton(qta.icon('fa5s.magic'), "Generate Metadata")
    gen_btn.setToolTip("Generate metadata for all files in the table")
    gen_btn.clicked.connect(self.batch_generate_metadata)
    gen_btn.setMinimumWidth(260)
    gen_btn.setMinimumHeight(48)
    font = gen_btn.font()
    font.setPointSize(font.pointSize() + 4)
    font.setBold(True)
    gen_btn.setFont(font)
    gen_group_layout.addWidget(gen_btn)

    btn_row_layout.addLayout(gen_group_layout)

    layout.addLayout(btn_row_layout)
    central.setLayout(layout)
    self.setCentralWidget(central)

    if self.model_combo.count() > 0:
        refresh_api_key_combo(self.model_combo.currentText())
    else:
        refresh_api_key_combo(None)
        refresh_api_key_combo(None)
