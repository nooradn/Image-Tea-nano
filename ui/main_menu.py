from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox
from PySide6.QtGui import QAction
import qtawesome as qta
import webbrowser
from helpers.file_importer import import_files
from helpers.metadata_helper.metadata_operation import write_metadata_to_images
from dialogs.csv_exporter_dialog import CSVExporterDialog
from dialogs.edit_prompt_dialog import EditPromptDialog
from dialogs.custom_prompt_dialog import CustomPromptDialog

def setup_main_menu(window):
    menubar = QMenuBar(window)
    file_menu = QMenu("File", menubar)

    import_action = QAction(qta.icon('fa5s.folder-open'), "Import Files", window)
    def do_import():
        if import_files(window, window.db, None, None):
            window.table.refresh_table()
    import_action.triggered.connect(do_import)
    file_menu.addAction(import_action)

    edit_menu = QMenu("Edit", menubar)

    delete_action = QAction(qta.icon('fa5s.trash'), "Delete Selected", window)
    delete_action.triggered.connect(lambda: window.table.delete_selected())
    edit_menu.addAction(delete_action)

    clear_action = QAction(qta.icon('fa5s.broom'), "Clear All", window)
    clear_action.triggered.connect(lambda: window.table.clear_all())
    edit_menu.addAction(clear_action)

    metadata_menu = QMenu("Metadata", menubar)

    write_metadata_action = QAction(qta.icon('fa5s.save'), "Write Metadata to Images", window)
    def do_write_metadata():
        write_metadata_to_images(window.db, None, None)
    write_metadata_action.triggered.connect(do_write_metadata)
    metadata_menu.addAction(write_metadata_action)

    export_metadata_action = QAction(qta.icon('fa5s.file-csv'), "Export Metadata to CSV", window)
    def show_export_dialog():
        dialog = CSVExporterDialog(window)
        dialog.exec()
    export_metadata_action.triggered.connect(show_export_dialog)
    metadata_menu.addAction(export_metadata_action)

    exit_action = QAction(qta.icon('fa5s.sign-out-alt'), "Exit", window)
    exit_action.triggered.connect(window.close)
    file_menu.addAction(exit_action)

    prompt_menu = QMenu("Prompt", menubar)
    edit_prompt_action = QAction(qta.icon('fa5s.edit'), "Edit Prompt", window)
    def open_edit_prompt():
        dialog = EditPromptDialog(window)
        dialog.exec()
    edit_prompt_action.triggered.connect(open_edit_prompt)
    prompt_menu.addAction(edit_prompt_action)

    custom_prompt_action = QAction(qta.icon('fa5s.comment-alt'), "Custom Prompt", window)
    def open_custom_prompt():
        dialog = CustomPromptDialog(window)
        dialog.exec()
    custom_prompt_action.triggered.connect(open_custom_prompt)
    prompt_menu.addAction(custom_prompt_action)

    help_menu = QMenu("Help", menubar)

    about_action = QAction(qta.icon('fa5s.info-circle'), "About", window)
    def show_about():
        QMessageBox.about(window, "About", "Image Tea (nano)\nMetadata Generator\n© 2025")
    about_action.triggered.connect(show_about)
    help_menu.addAction(about_action)

    wa_action = QAction(qta.icon('fa5b.whatsapp'), "WhatsApp Group", window)
    def open_wa():
        webbrowser.open("https://chat.whatsapp.com/CMQvDxpCfP647kBBA6dRn3")
    wa_action.triggered.connect(open_wa)
    help_menu.addAction(wa_action)

    repo_action = QAction(qta.icon('fa5b.github'), "Repository", window)
    def open_repo():
        webbrowser.open("https://github.com/mudrikam/Image-Tea-nano")
    repo_action.triggered.connect(open_repo)
    help_menu.addAction(repo_action)

    menubar.addMenu(file_menu)
    menubar.addMenu(edit_menu)
    menubar.addMenu(metadata_menu)
    menubar.addMenu(prompt_menu)
    menubar.addMenu(help_menu)
    window.setMenuBar(menubar)
