import os
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QTextBrowser, QSizePolicy, QSplitter, QComboBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import qtawesome as qta
from config import BASE_PATH

class ReadDocumentationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Read Documentation")
        self.resize(900, 600)

        # Language selection combobox
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Bahasa Indonesia", "id")
        self.lang_combo.addItem("English", "en")
        lang_label = QLabel("Language:")
        lang_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Layout for language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()

        splitter = QSplitter(Qt.Horizontal, self)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        font = QFont()
        font.setPointSize(12)
        self.viewer.setFont(font)
        self.viewer.setStyleSheet(
            "QTextBrowser {"
            "  padding: 24px;"
            "  line-height: 1.7;"
            "  white-space: pre-wrap;"
            "}"
        )
        self.viewer.setLineWrapMode(QTextBrowser.WidgetWidth)

        splitter.addWidget(self.tree)
        splitter.addWidget(self.viewer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(lang_layout)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        self.doc_root_id = os.path.join(BASE_PATH, "documentation", "lang_ID")
        self.doc_root_en = os.path.join(BASE_PATH, "documentation", "lang_EN")
        self.res_images_path = os.path.join(BASE_PATH, "res", "images")
        self.file_icon = qta.icon('fa5s.file-alt', color='#2196F3')
        self.folder_icon = qta.icon('fa5s.folder', color='#FFA500')

        self.current_lang = "id"
        self.populate_tree()
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)

        self.load_default_markdown()

    def get_doc_root(self):
        if self.current_lang == "en":
            return self.doc_root_en
        return self.doc_root_id

    def get_root_label(self):
        if self.current_lang == "en":
            return "Documentation"
        return "Dokumentasi"

    def get_lang_label(self):
        if self.current_lang == "en":
            return "English"
        return "Bahasa Indonesia"

    def populate_tree(self):
        self.tree.clear()
        root_label = self.get_root_label()
        root_item = QTreeWidgetItem([root_label])
        root_item.setData(0, Qt.UserRole, None)
        root_item.setIcon(0, self.folder_icon)
        self.tree.addTopLevelItem(root_item)

        doc_root = self.get_doc_root()
        lang_label = self.get_lang_label()
        lang_item = QTreeWidgetItem([lang_label])
        lang_item.setData(0, Qt.UserRole, doc_root)
        lang_item.setIcon(0, self.folder_icon)
        root_item.addChild(lang_item)

        self.add_children(doc_root, lang_item)
        root_item.setExpanded(True)
        lang_item.setExpanded(True)

    def add_children(self, folder_path, parent_item):
        try:
            entries = sorted(os.listdir(folder_path))
        except Exception as e:
            print(f"Error reading directory {folder_path}: {e}")
            return
        files = []
        dirs = []
        for entry in entries:
            full_path = os.path.join(folder_path, entry)
            if os.path.isdir(full_path):
                dirs.append((entry, full_path))
            elif entry.lower().endswith(".md"):
                files.append((entry, full_path))
        for entry, full_path in files:
            display_name = os.path.splitext(entry)[0].replace('_', ' ').replace('-', ' ').title()
            file_item = QTreeWidgetItem([display_name])
            file_item.setData(0, Qt.UserRole, full_path)
            file_item.setIcon(0, self.file_icon)
            parent_item.addChild(file_item)
        for entry, full_path in dirs:
            dir_item = QTreeWidgetItem([entry.title()])
            dir_item.setData(0, Qt.UserRole, full_path)
            dir_item.setIcon(0, self.folder_icon)
            parent_item.addChild(dir_item)
            self.add_children(full_path, dir_item)

    def on_item_clicked(self, item, column):
        file_path = item.data(0, Qt.UserRole)
        if file_path is None:
            self.viewer.clear()
            return
        if os.path.isdir(file_path):
            item.setExpanded(True)
            if item.childCount() > 0:
                first_child = item.child(0)
                self.tree.setCurrentItem(first_child)
                self.on_item_clicked(first_child, 0)
            else:
                self.viewer.clear()
        elif os.path.isfile(file_path) and file_path.lower().endswith(".md"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    md_text = f.read()
                self.viewer.setSearchPaths([self.res_images_path])
                self.viewer.setMarkdown(md_text)
                self.viewer.setLineWrapMode(QTextBrowser.WidgetWidth)
            except Exception as e:
                self.viewer.setPlainText(f"Failed to load file:\n{file_path}\n\nError: {e}")
        else:
            self.viewer.clear()

    def on_language_changed(self, idx):
        self.current_lang = self.lang_combo.currentData()
        self.populate_tree()
        self.load_default_markdown()

    def load_default_markdown(self):
        doc_root = self.get_doc_root()
        if self.current_lang == "en":
            default_md = "about_image_tea.md"
        else:
            default_md = "tentang_image_tea.md"
        about_path = os.path.join(doc_root, default_md)
        if os.path.isfile(about_path):
            try:
                with open(about_path, "r", encoding="utf-8") as f:
                    md_text = f.read()
                self.viewer.setSearchPaths([self.res_images_path])
                self.viewer.setMarkdown(md_text)
                self.viewer.setLineWrapMode(QTextBrowser.WidgetWidth)
            except Exception as e:
                self.viewer.setPlainText(f"Failed to load file:\n{about_path}\n\nError: {e}")
        else:
            self.viewer.clear()
