from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QDialog, QSpacerItem, QSizePolicy
import datetime
from dialogs.add_api_key_dialog import AddApiKeyDialog
from ui.file_dnd_widget import DragDropWidget
import qtawesome as qta
from ui.main_table import ImageTableWidget
from ui.prompt_section import PromptSectionWidget
from ui.stats_section import StatsSectionWidget
from ui.main_menu import setup_main_menu
from ui.main_toolbar import setup_main_toolbar
from helpers.batch_processing_helper import batch_generate_metadata
from dialogs.api_call_warning_dialog import ApiCallWarningDialog
from ui.properties_widget import PropertiesWidget

def setup_ui(self):
    setup_main_menu(self)
    setup_main_toolbar(self)
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

    self.tested_label = QLabel()
    self.tested_label.setText(" - | -")
    self.tested_label.setToolTip("Menampilkan waktu terakhir API key ini dites dan modelnya")
    api_layout.addWidget(self.api_key_combo)
    api_layout.addWidget(self.tested_label)
    api_layout.addItem(QSpacerItem(24, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
    layout.addLayout(api_layout)

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
            if hasattr(self, 'tested_label'):
                last_tested = self.api_key_map[api_key]['last_tested']
                model = self.api_key_map[api_key]['model']
                self.tested_label.setText(f"{last_tested if last_tested else '-'} | {model if model else '-'}")
        else:
            self.api_key = None
            if hasattr(self, 'tested_label'):
                self.tested_label.setText(" - | -")

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
            if hasattr(self, 'tested_label'):
                last_tested = self.api_key_map[api_key]['last_tested']
                model = self.api_key_map[api_key]['model']
                self.tested_label.setText(f"{last_tested if last_tested else '-'} | {model if model else '-'}")
        else:
            self.api_key = None
            self.selected_service = None
            self.selected_model_name = None
            if hasattr(self, 'tested_label'):
                self.tested_label.setText("- | -")

    self.api_key_combo.currentIndexChanged.connect(on_api_combo_changed)

    self.prompt_section = PromptSectionWidget(self)
    layout.addWidget(self.prompt_section)

    self.dnd_widget = DragDropWidget(self)
    layout.addWidget(self.dnd_widget)

    main_content_layout = QHBoxLayout()
    self.table = ImageTableWidget(self, db=self.db)
    self.properties_widget = PropertiesWidget(self)
    self.table._properties_widget = self.properties_widget
    self.properties_widget.db = self.db

    def on_table_selection_changed():
        selected_row = self.table.get_selected_row_data() if hasattr(self.table, "get_selected_row_data") else None
        self.properties_widget.set_properties(selected_row)

    if hasattr(self.table, "selectionModel"):
        self.table.selectionModel().selectionChanged.connect(lambda *_: on_table_selection_changed())

    if hasattr(self.table, "data_refreshed"):
        self.table.data_refreshed.connect(lambda: on_table_selection_changed())

    main_content_layout.addWidget(self.table, stretch=3)
    main_content_layout.addWidget(self.properties_widget, stretch=1)
    layout.addLayout(main_content_layout)

    btn_row_layout = QHBoxLayout()
    self.stats_section = StatsSectionWidget(self)
    btn_row_layout.addWidget(self.stats_section)

    self.table.stats_changed.connect(self.stats_section.update_stats)

    btn_row_layout.addStretch()

    gen_group_layout = QVBoxLayout()
    self.gen_mode_combo = QComboBox()
    self.gen_mode_combo.addItems(["Generate All", "Selected Only", "Failed Only"])
    self.gen_mode_combo.setToolTip("Choose which files to generate metadata for")
    gen_group_layout.addWidget(self.gen_mode_combo)

    self.gen_btn = QPushButton(qta.icon('fa5s.magic'), "Generate Metadata")
    self.gen_btn.setStyleSheet("background-color: rgba(132, 225, 7, 0.3);")

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

    def on_generate_clicked():
        mode = self.gen_mode_combo.currentText()
        total_files = self.table.table.rowCount()
        if mode == "Generate All" and total_files >= 1000:
            dialog = ApiCallWarningDialog(self)
            result = dialog.exec()
            if result != QDialog.Accepted:
                return
        batch_generate_metadata(self)
        on_table_selection_changed()

    self.gen_btn.clicked.connect(on_generate_clicked)
    gen_group_layout.addWidget(self.gen_btn)

    btn_row_layout.addLayout(gen_group_layout)

    layout.addLayout(btn_row_layout)
    central.setLayout(layout)
    self.setCentralWidget(central)

    if self.model_combo.count() > 0:
        on_model_combo_changed(self.model_combo.currentIndex())
    else:
        refresh_api_key_combo(None)
    on_table_selection_changed()