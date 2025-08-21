from PySide6.QtWidgets import QToolBar, QStyle, QWidget, QFrame, QWidgetAction, QHBoxLayout
from PySide6.QtGui import QAction
import qtawesome as qta
import webbrowser
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
    toolbar.setStyleSheet("QToolBar { padding: 5px; }")

    import_action = QAction(qta.icon('fa5s.folder-open'), "Import Files", window)
    import_action.triggered.connect(lambda: (
        import_files(window, window.db, None, None) and window.table.refresh_table()
    ))
    toolbar.addAction(import_action)

    # Grup: Clear All dan Delete Selected
    clear_all_action = QAction(qta.icon('fa5s.broom'), "Clear All", window)
    clear_all_action.triggered.connect(lambda: window.table.clear_all())
    toolbar.addAction(clear_all_action)

    delete_selected_action = QAction(qta.icon('fa5s.trash'), "Delete Selected", window)
    delete_selected_action.triggered.connect(lambda: window.table.delete_selected())
    toolbar.addAction(delete_selected_action)

    add_vertical_separator(toolbar)

    clear_metadata_action = QAction(qta.icon('fa5s.eraser'), "Clear Existing Metadata", window)
    def clear_existing_metadata():
        from PySide6.QtWidgets import QMessageBox
        msg = (
            "Are you sure you want to clear all metadata (title, description, tags, status)?\n\n"
            "This will NOT remove metadata embedded in the image files, only metadata stored in the database."
        )
        reply = QMessageBox.question(window, "Clear Metadata", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            window.db.clear_all_metadata()
            window.table.refresh_table()
    clear_metadata_action.triggered.connect(clear_existing_metadata)
    toolbar.addAction(clear_metadata_action)

    batch_rename_action = QAction(qta.icon('fa5s.i-cursor'), "Batch Rename", window)
    batch_rename_action.triggered.connect(lambda: BatchRenameDialog(window, table_widget=window.table, db=window.db).exec())
    toolbar.addAction(batch_rename_action)

    # Tambahkan Edit Metadata
    edit_metadata_action = QAction(qta.icon('fa5s.edit'), "Edit Metadata", window)
    def open_edit_metadata():
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
    edit_metadata_action.triggered.connect(open_edit_metadata)
    toolbar.addAction(edit_metadata_action)

    add_vertical_separator(toolbar)

    write_metadata_images_action = QAction(qta.icon('fa5s.image'), "Write Metadata to Images", window)
    write_metadata_images_action.triggered.connect(lambda: write_metadata_to_images(window.db, window))
    toolbar.addAction(write_metadata_images_action)

    write_metadata_videos_action = QAction(qta.icon('fa5s.film'), "Write Metadata to Videos", window)
    write_metadata_videos_action.triggered.connect(lambda: write_metadata_to_videos(window.db, window))
    toolbar.addAction(write_metadata_videos_action)

    export_metadata_action = QAction(qta.icon('fa5s.file-csv'), "Export Metadata to CSV", window)
    export_metadata_action.triggered.connect(lambda: CSVExporterDialog(window).exec())
    toolbar.addAction(export_metadata_action)

    add_vertical_separator(toolbar)

    edit_prompt_action = QAction(qta.icon('fa5s.edit'), "Edit Prompt", window)
    edit_prompt_action.triggered.connect(lambda: EditPromptDialog(window).exec())
    toolbar.addAction(edit_prompt_action)

    custom_prompt_action = QAction(qta.icon('fa5s.comment-alt'), "Custom Prompt", window)
    custom_prompt_action.triggered.connect(lambda: CustomPromptDialog(window).exec())
    toolbar.addAction(custom_prompt_action)

    add_vertical_separator(toolbar)

    add_api_action = QAction(qta.icon('fa5s.key'), "Add API Key", window)
    add_api_action.triggered.connect(lambda: AddApiKeyDialog(window).exec())
    toolbar.addAction(add_api_action)

    add_vertical_separator(toolbar)

    about_action = QAction(qta.icon('fa5s.info-circle'), "About", window)
    about_action.triggered.connect(lambda: AboutDialog(window).exec())
    toolbar.addAction(about_action)

    donate_action = QAction(qta.icon('fa5s.donate'), "Donate", window)
    donate_action.triggered.connect(lambda: DonateDialog(window).exec())
    toolbar.addAction(donate_action)

    wa_action = QAction(qta.icon('fa5b.whatsapp'), "WhatsApp Group", window)
    wa_action.triggered.connect(lambda: webbrowser.open("https://chat.whatsapp.com/CMQvDxpCfP647kBBA6dRn3"))
    toolbar.addAction(wa_action)

    repo_action = QAction(qta.icon('fa5b.github'), "Repository", window)
    repo_action.triggered.connect(lambda: webbrowser.open("https://github.com/mudrikam/Image-Tea-nano"))
    toolbar.addAction(repo_action)

    website_action = QAction(qta.icon('fa5s.globe'), "Website", window)
    website_action.triggered.connect(lambda: webbrowser.open("https://www.image-tea.cloud/"))
    toolbar.addAction(website_action)

    readme_action = QAction(qta.icon('fa5s.book'), "Open README.md (GitHub)", window)
    readme_action.triggered.connect(lambda: webbrowser.open("https://github.com/mudrikam/Image-Tea-nano/blob/main/README.md"))
    toolbar.addAction(readme_action)

    documentation_action = QAction(qta.icon('fa5s.book-open'), "Help", window)
    documentation_action.triggered.connect(lambda: ReadDocumentationDialog(window).exec())
    toolbar.addAction(documentation_action)

    window.addToolBar(toolbar)
