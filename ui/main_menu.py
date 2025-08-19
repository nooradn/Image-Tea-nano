from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox, QDialog, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtCore import Qt
import qtawesome as qta
import webbrowser
import sys
import os
import subprocess
from helpers.file_importer import import_files
from helpers.metadata_helper.metadata_operation import write_metadata_to_images, write_metadata_to_videos
from dialogs.csv_exporter_dialog import CSVExporterDialog
from dialogs.edit_prompt_dialog import EditPromptDialog
from dialogs.custom_prompt_dialog import CustomPromptDialog
from dialogs.batch_rename_dialog import BatchRenameDialog
from dialogs.read_documentation_dialog import ReadDocumentationDialog
from dialogs.donation_dialog import DonateDialog
from dialogs.add_api_key_dialog import AddApiKeyDialog
from dialogs.about_dialog import AboutDialog
from config import BASE_PATH

def setup_main_menu(window):
    menubar = QMenuBar(window)
    file_menu = QMenu("File", menubar)

    import_action = QAction(qta.icon('fa5s.folder-open'), "Import Files", window)
    def do_import():
        if import_files(window, window.db, None, None):
            window.table.refresh_table()
    import_action.triggered.connect(do_import)
    file_menu.addAction(import_action)

    relaunch_action = QAction(qta.icon('fa5s.redo'), "Relaunch", window)
    def relaunch_app():
        python_exe = sys.executable
        args = [python_exe] + sys.argv
        try:
            subprocess.Popen(args)
        except Exception as e:
            print(f"Failed to relaunch: {e}")
        window.close()
    relaunch_action.triggered.connect(relaunch_app)
    file_menu.addAction(relaunch_action)

    exit_action = QAction(qta.icon('fa5s.sign-out-alt'), "Exit", window)
    exit_action.triggered.connect(window.close)
    file_menu.addAction(exit_action)

    api_menu = QMenu("API", menubar)
    add_api_action = QAction(qta.icon('fa5s.key'), "Add API Key", window)
    def show_api_dialog():
        dlg = AddApiKeyDialog(window)
        dlg.exec()
    add_api_action.triggered.connect(show_api_dialog)
    api_menu.addAction(add_api_action)

    edit_menu = QMenu("Edit", menubar)
    delete_action = QAction(qta.icon('fa5s.trash'), "Delete Selected", window)
    delete_action.triggered.connect(lambda: window.table.delete_selected())
    edit_menu.addAction(delete_action)

    clear_action = QAction(qta.icon('fa5s.broom'), "Clear All", window)
    clear_action.triggered.connect(lambda: window.table.clear_all())
    edit_menu.addAction(clear_action)

    clear_metadata_action = QAction(qta.icon('fa5s.eraser'), "Clear Existing Metadata", window)
    def clear_existing_metadata():
        msg = (
            "Are you sure you want to clear all metadata (title, description, tags, status)?\n\n"
            "This will NOT remove metadata embedded in the image files, only metadata stored in the database."
        )
        reply = QMessageBox.question(window, "Clear Metadata", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            window.db.clear_all_metadata()
            window.table.refresh_table()
    clear_metadata_action.triggered.connect(clear_existing_metadata)
    edit_menu.addAction(clear_metadata_action)

    batch_rename_action = QAction(qta.icon('fa5s.i-cursor'), "Batch Rename", window)
    def open_batch_rename():
        dialog = BatchRenameDialog(window, table_widget=window.table, db=window.db)
        dialog.exec()
    batch_rename_action.triggered.connect(open_batch_rename)
    edit_menu.addAction(batch_rename_action)

    metadata_menu = QMenu("Metadata", menubar)
    write_metadata_images_action = QAction(qta.icon('fa5s.save'), "Write Metadata to Images", window)
    def do_write_metadata_images():
        write_metadata_to_images(window.db, window)
    write_metadata_images_action.triggered.connect(do_write_metadata_images)
    metadata_menu.addAction(write_metadata_images_action)

    write_metadata_videos_action = QAction(qta.icon('fa5s.save'), "Write Metadata to Videos", window)
    def do_write_metadata_videos():
        write_metadata_to_videos(window.db, window)
    write_metadata_videos_action.triggered.connect(do_write_metadata_videos)
    metadata_menu.addAction(write_metadata_videos_action)

    export_metadata_action = QAction(qta.icon('fa5s.file-csv'), "Export Metadata to CSV", window)
    def show_export_dialog():
        dialog = CSVExporterDialog(window)
        dialog.exec()
    export_metadata_action.triggered.connect(show_export_dialog)
    metadata_menu.addAction(export_metadata_action)

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
        dialog = AboutDialog(window)
        dialog.exec()
    about_action.triggered.connect(show_about)
    help_menu.addAction(about_action)

    donate_action = QAction(qta.icon('fa5s.donate'), "Donate", window)
    def show_donate():
        dialog = DonateDialog(window)
        dialog.exec()
    donate_action.triggered.connect(show_donate)
    help_menu.addAction(donate_action)

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

    readme_action = QAction(qta.icon('fa5s.book'), "Open README.md (GitHub)", window)
    def open_readme():
        webbrowser.open("https://github.com/mudrikam/Image-Tea-nano/blob/main/README.md")
    readme_action.triggered.connect(open_readme)
    help_menu.addAction(readme_action)

    documentation_action = QAction(qta.icon('fa5s.book-open'), "Help", window)
    def open_documentation():
        dialog = ReadDocumentationDialog(window)
        dialog.exec()
    documentation_action.triggered.connect(open_documentation)
    help_menu.addAction(documentation_action)

    menubar.addMenu(file_menu)
    menubar.addMenu(api_menu)
    menubar.addMenu(edit_menu)
    menubar.addMenu(metadata_menu)
    menubar.addMenu(prompt_menu)
    menubar.addMenu(help_menu)
    window.setMenuBar(menubar)
