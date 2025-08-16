from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox
from PySide6.QtGui import QAction
import qtawesome as qta
import webbrowser

def setup_main_menu(window):
    menubar = QMenuBar(window)
    file_menu = QMenu("File", menubar)

    exit_action = QAction(qta.icon('fa5s.sign-out-alt'), "Exit", window)
    exit_action.triggered.connect(window.close)
    file_menu.addAction(exit_action)

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
    menubar.addMenu(help_menu)
    window.setMenuBar(menubar)
