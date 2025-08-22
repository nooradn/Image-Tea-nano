from PySide6.QtWidgets import QToolBar, QStyle, QWidget, QFrame, QWidgetAction, QHBoxLayout
from PySide6.QtGui import QAction
import qtawesome as qta
import webbrowser
import os
import subprocess
from config import BASE_PATH
from dialogs.csv_exporter_dialog import CSVExporterDialog
from dialogs.edit_prompt_dialog import EditPromptDialog
from dialogs.custom_prompt_dialog import CustomPromptDialog
from dialogs.batch_rename_dialog import BatchRenameDialog
from dialogs.read_documentation_dialog import ReadDocumentationDialog
from dialogs.donation_dialog import DonateDialog
from dialogs.add_api_key_dialog import AddApiKeyDialog
from dialogs.about_dialog import AboutDialog
from dialogs.file_metadata_dialog import FileMetadataDialog
from helpers.file_importer import import_files
from helpers.metadata_helper.metadata_operation import write_metadata_to_images, write_metadata_to_videos

def add_vertical_separator(toolbar):
    wrapper = QWidget()
    layout = QHBoxLayout(wrapper)
    layout.setContentsMargins(8, 0, 8, 0)
    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    sep.setFrameShadow(QFrame.Sunken)
    sep.setFixedHeight(32)
    layout.addWidget(sep)
    sep_action = QWidgetAction(toolbar)
    sep_action.setDefaultWidget(wrapper)
    toolbar.addAction(sep_action)

def setup_main_toolbar(window: QWidget):
    toolbar = QToolBar("Main Toolbar", window)
    toolbar.setMovable(False)
    toolbar.setFloatable(False)
    toolbar.setIconSize(window.style().standardIcon(QStyle.SP_DesktopIcon).actualSize(toolbar.iconSize()))
    toolbar.setStyleSheet("""
        QToolBar { padding: 5px; }
        QToolButton {
            padding: 4px;
            border-radius: 6px;
        }
        QToolButton:hover {
            background-color: rgba(174, 174, 174, 0.4);
        }
        QToolButton:hover .qicon {
            color: #fff;
        }
    """)

    icon_color = "#888"
    icon_color_hover = "#4e9e20"

    def make_action(icon_name, text, triggered_func):
        icon = qta.icon(icon_name, color=icon_color, color_active=icon_color_hover)
        action = QAction(icon, text, window)
        action.triggered.connect(triggered_func)
        return action

    import_action = make_action('fa5s.folder-open', "Import Files", lambda: (
        import_files(window, window.db) and window.table.refresh_table()
    ))
    toolbar.addAction(import_action)

    clear_all_action = make_action('fa5s.broom', "Clear All", lambda: window.table.clear_all())
    toolbar.addAction(clear_all_action)

    delete_selected_action = make_action('fa5s.trash', "Delete Selected", lambda: window.table.delete_selected())
    toolbar.addAction(delete_selected_action)

    add_vertical_separator(toolbar)

    clear_metadata_action = make_action('fa5s.eraser', "Clear Existing Metadata", lambda: clear_existing_metadata(window))
    toolbar.addAction(clear_metadata_action)

    batch_rename_action = make_action('fa5s.i-cursor', "Batch Rename", lambda: BatchRenameDialog(window, table_widget=window.table, db=window.db).exec())
    toolbar.addAction(batch_rename_action)

    edit_metadata_action = make_action('fa5s.edit', "Edit Metadata", lambda: open_edit_metadata(window))
    toolbar.addAction(edit_metadata_action)

    add_vertical_separator(toolbar)

    write_metadata_images_action = make_action('fa5s.image', "Write Metadata to Images", lambda: write_metadata_to_images(window.db, window))
    toolbar.addAction(write_metadata_images_action)

    write_metadata_videos_action = make_action('fa5s.film', "Write Metadata to Videos", lambda: write_metadata_to_videos(window.db, window))
    toolbar.addAction(write_metadata_videos_action)

    export_metadata_action = make_action('fa5s.file-csv', "Export Metadata to CSV", lambda: CSVExporterDialog(window).exec())
    toolbar.addAction(export_metadata_action)

    add_vertical_separator(toolbar)

    edit_prompt_action = make_action('fa5s.edit', "Edit Prompt", lambda: EditPromptDialog(window).exec())
    toolbar.addAction(edit_prompt_action)

    custom_prompt_action = make_action('fa5s.comment-alt', "Custom Prompt", lambda: CustomPromptDialog(window).exec())
    toolbar.addAction(custom_prompt_action)

    add_api_action = make_action('fa5s.key', "Add API Key", lambda: AddApiKeyDialog(window).exec())
    toolbar.addAction(add_api_action)

    add_vertical_separator(toolbar)

    about_action = make_action('fa5s.info-circle', "About", lambda: AboutDialog(window).exec())
    toolbar.addAction(about_action)

    def run_updater():
        updater_path = os.path.join(BASE_PATH, "Image Tea Updater.exe")
        try:
            subprocess.Popen([updater_path])
        except Exception as e:
            print(f"Failed to run updater: {e}")
    update_now_action = make_action('fa5s.download', "Update Now", run_updater)
    toolbar.addAction(update_now_action)

    donate_action = make_action('fa5s.donate', "Donate", lambda: DonateDialog(window).exec())
    toolbar.addAction(donate_action)

    wa_action = make_action('fa5b.whatsapp', "WhatsApp Group", lambda: webbrowser.open("https://chat.whatsapp.com/CMQvDxpCfP647kBBA6dRn3"))
    toolbar.addAction(wa_action)

    repo_action = make_action('fa5b.github', "Repository", lambda: webbrowser.open("https://github.com/mudrikam/Image-Tea-nano"))
    toolbar.addAction(repo_action)

    website_action = make_action('fa5s.globe', "Website", lambda: webbrowser.open("https://www.image-tea.cloud/"))
    toolbar.addAction(website_action)

    readme_action = make_action('fa5s.book', "Open README.md (GitHub)", lambda: webbrowser.open("https://github.com/mudrikam/Image-Tea-nano/blob/main/README.md"))
    toolbar.addAction(readme_action)

    documentation_action = make_action('fa5s.book-open', "Help", lambda: ReadDocumentationDialog(window).exec())
    toolbar.addAction(documentation_action)

    window.addToolBar(toolbar)

def clear_existing_metadata(window):
    from PySide6.QtWidgets import QMessageBox
    msg = (
        "Are you sure you want to clear all metadata (title, description, tags, status and categories)?\n\n"
        "This will NOT remove metadata embedded in the image files, only metadata stored in the database."
    )
    reply = QMessageBox.question(window, "Clear Metadata", msg, QMessageBox.Yes | QMessageBox.No)
    if reply == QMessageBox.Yes:
        window.db.clear_all_metadata()
        window.table.refresh_table()

def open_edit_metadata(window):
    selected = window.table.table.selectionModel().selectedRows()
    if selected:
        idx = selected[0].row()
        filepath_item = window.table.table.item(idx, 1)
        if filepath_item:
            filepath = filepath_item.data(0x0100)
            if not filepath:
                filepath = filepath_item.text()
            dialog = FileMetadataDialog(filepath, parent=window)
            dialog.exec()