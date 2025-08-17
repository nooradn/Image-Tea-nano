from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
import datetime
from dialogs.add_api_key_dialog import AddApiKeyDialog
from ui.file_dnd_widget import DragDropWidget
import qtawesome as qta
from ui.main_table import ImageTableWidget
from ui.prompt_section import PromptSectionWidget
from ui.stats_section import StatsSectionWidget
from ui.main_menu import setup_main_menu

def setup_ui(self):
    setup_main_menu(self)
    from database.db_operation import ImageTeaDB
    self.db = getattr(self, 'db', None) or ImageTeaDB()
    central = QWidget()
    layout = QVBoxLayout()
    api_layout = QHBoxLayout()
    from PySide6.QtWidgets import QSizePolicy

    api_keys = self.db.get_all_api_keys()
    model_set = []
    for entry in api_keys:
        service, api_key, note, last_tested, status, model = entry
        service_disp = service.lower() if service.lower() in ("openai", "gemini") else service
        if service_disp.capitalize() not in model_set:
            model_set.append(service_disp.capitalize())

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
    self.api_key_combo.setMaximumWidth(550)
    self.api_key_map = {}

    def refresh_api_key_combo(selected_model=None):
        self.api_key_combo.clear()
        self.api_key_map.clear()
        api_keys = self.db.get_all_api_keys()
        for entry in api_keys:
            service, api_key, note, last_tested, status, model = entry
            service_disp = service.lower() if service.lower() in ("openai", "gemini") else service
            if selected_model is None or service_disp.capitalize() == selected_model:
                if api_key and len(api_key) > 5:
                    masked_key = '*' * (len(api_key) - 5) + api_key[-5:]
                else:
                    masked_key = api_key
                label = f"{masked_key} ({note})" if note else masked_key
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
        self.selected_model = selected_model

    self.model_combo.currentIndexChanged.connect(on_model_combo_changed)

    def on_api_combo_changed(idx):
        api_key = self.api_key_combo.itemData(idx)
        if api_key and api_key in self.api_key_map:
            self.api_key = api_key
            self.selected_service = self.api_key_map[api_key]['service']
            self.selected_model_name = self.api_key_map[api_key]['model']
            if hasattr(self, 'last_tested_label'):
                last_tested = self.api_key_map[api_key]['last_tested']
                model = self.api_key_map[api_key]['model']
                self.last_tested_label.setText(f"Last Tested: {last_tested if last_tested else '-'} | Model: {model if model else '-'}")
        else:
            self.api_key = None
            self.selected_service = None
            self.selected_model_name = None
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
            service, api_key, note, last_tested, status, model = entry
            service_disp = service.lower() if service.lower() in ("openai", "gemini") else service
            if service_disp.capitalize() not in model_set:
                model_set.append(service_disp.capitalize())
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

    # Tombol Write Metadata dihapus karena sudah di menu Metadata
    top_btn_layout.addLayout(left_btn_group)
    top_btn_layout.addStretch()
    top_btn_layout.addLayout(right_btn_group)
    layout.addLayout(top_btn_layout)

    self.table = ImageTableWidget(self, db=self.db)
    layout.addWidget(self.table)

    self.dnd_widget = DragDropWidget(self)
    layout.addWidget(self.dnd_widget)

    # Grup generate metadata: stats_section di kiri sebaris dengan tombol generate di kanan bawah tabel
    btn_row_layout = QHBoxLayout()
    self.stats_section = StatsSectionWidget(self)
    btn_row_layout.addWidget(self.stats_section)

    # Connect table stats signal to stats section (now with 5 args)
    self.table.stats_changed.connect(self.stats_section.update_stats)

    btn_row_layout.addStretch()

    gen_group_layout = QVBoxLayout()
    self.gen_mode_combo = QComboBox()
    self.gen_mode_combo.addItems(["Generate All", "Selected Only", "Failed Only"])
    self.gen_mode_combo.setToolTip("Choose which files to generate metadata for")
    gen_group_layout.addWidget(self.gen_mode_combo)

    self.gen_btn = QPushButton(qta.icon('fa5s.magic'), "Generate Metadata")

    def update_gen_btn_tooltip(idx):
        mode = self.gen_mode_combo.currentText()
        if mode == "Generate All":
            self.gen_btn.setToolTip("Generate metadata for all files in the table")
        elif mode == "Selected Only":
            self.gen_btn.setToolTip("Generate metadata only for selected files")
        elif mode == "Failed Only":
            self.gen_btn.setToolTip("Generate metadata only for files that previously failed")
        else:
            self.gen_btn.setToolTip("Generate metadata")

    self.gen_mode_combo.currentIndexChanged.connect(update_gen_btn_tooltip)
    update_gen_btn_tooltip(self.gen_mode_combo.currentIndex())

    self.gen_btn.setMinimumWidth(260)
    self.gen_btn.setMinimumHeight(48)
    font = self.gen_btn.font()
    font.setPointSize(font.pointSize() + 4)
    font.setBold(True)
    self.gen_btn.setFont(font)
    self.gen_btn.clicked.connect(self.batch_generate_metadata)
    gen_group_layout.addWidget(self.gen_btn)

    btn_row_layout.addLayout(gen_group_layout)

    layout.addLayout(btn_row_layout)
    central.setLayout(layout)
    self.setCentralWidget(central)

    if self.model_combo.count() > 0:
        on_model_combo_changed(self.model_combo.currentIndex())
    else:
        refresh_api_key_combo(None)
