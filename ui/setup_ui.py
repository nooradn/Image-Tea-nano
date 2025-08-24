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
from ui.api_key_section import ApiKeySectionWidget
from ui.main_statusbar import MainStatusBar

def setup_ui(self):
    setup_main_menu(self)
    setup_main_toolbar(self)
    from database.db_operation import ImageTeaDB
    self.db = getattr(self, 'db', None) or ImageTeaDB()
    central = QWidget()
    layout = QVBoxLayout()
    api_layout = QHBoxLayout()

    self.api_key_section = ApiKeySectionWidget(self.db, self)
    api_layout.addWidget(self.api_key_section)
    layout.addLayout(api_layout)

    def on_api_key_changed(api_key, service, model):
        self.api_key = api_key
        self.selected_service = service
        self.selected_model_name = model

    self.api_key_section.api_key_changed.connect(on_api_key_changed)
    # Set initial values
    self.api_key = self.api_key_section.get_current_api_key()
    self.selected_service = self.api_key_section.get_current_service()
    self.selected_model_name = self.api_key_section.get_current_model()

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

    self.gen_btn = QPushButton(qta.icon('fa6s.wand-magic-sparkles'), "Generate Metadata")
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

    self.statusbar = MainStatusBar(self)
    self.setStatusBar(self.statusbar)

    on_table_selection_changed()