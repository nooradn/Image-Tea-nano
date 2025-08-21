from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from helpers.file_importer import import_files
import os

try:
    from PIL import Image
    PILLOW_FORMATS = set()
    for ext, fmt in Image.registered_extensions().items():
        PILLOW_FORMATS.add(ext.lower())
except ImportError:
    PILLOW_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.eps', '.svg', '.pdf'}

class DragDropWidget(QLabel):
	"""
	Widget drag & drop yang dapat menerima file.
	Agar dapat digunakan, set 'on_files_dropped' ke fungsi callback yang menerima list path.
	"""
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setText("Drag and drop images or videos here")
		self.setAlignment(Qt.AlignCenter)
		self.setAcceptDrops(True)
		self.setStyleSheet("border: 2px dashed #aaa; padding: 20px; font-size: 16px;")
		self.on_files_dropped = None  # callback, diisi oleh parent jika ingin handle drop
		self._default_style = "border: 2px dashed #aaa; padding: 20px; font-size: 16px;"
		self._accept_style = "border: 2px dashed rgba(121, 202, 12, 0.3); padding: 20px; font-size: 16px; background-color: rgba(121, 202, 12, 0.3);"
		self._reject_style = "border: 2px dashed rgba(224, 23, 23, 0.3); padding: 20px; font-size: 16px; background-color: rgba(224, 23, 23, 0.3);"
		video_exts = {
			".mp4", ".mpeg", ".mov", ".avi", ".flv",
			".mpg", ".webm", ".wmv", ".3gp", ".3gpp"
		}
		# Tambahkan .svg, .eps, .pdf ke PILLOW_FORMATS jika belum ada
		extra_exts = {'.svg', '.eps', '.pdf'}
		self._supported_exts = PILLOW_FORMATS | video_exts | extra_exts
		self._default_text = "Drag and drop images or videos here"
		# Daftar ekstensi umum
		common_exts = [
			"jpg", "jpeg", "png", "eps", "svg", "pdf", "tiff", "webp",
			"mp4", "mpeg", "mov", "avi", "flv", "mpg", "webm", "wmv", "3gp", "3gpp"
		]
		# Ekstensi yang benar-benar didukung
		supported_common = [ext for ext in common_exts if f".{ext}" in self._supported_exts]
		# Jika ada ekstensi lain yang didukung, tambahkan "..."
		has_other = len(self._supported_exts - set(f".{ext}" for ext in supported_common)) > 0
		supported_text = ", ".join(supported_common)
		if has_other:
			supported_text += ", ..."
		self._supported_text = "<span style='font-size:10px;color:#888;'>Supported: " + supported_text + "</span>"

	def dragEnterEvent(self, event: QDragEnterEvent):
		if event.mimeData().hasUrls():
			paths = [url.toLocalFile() for url in event.mimeData().urls()]
			unsupported_ext = None
			for p in paths:
				if not self._is_supported_file(p):
					unsupported_ext = p.lower().rsplit('.', 1)[-1] if '.' in p else ''
					break
			if unsupported_ext is None:
				self.setStyleSheet(self._accept_style)
				self.setText(self._default_text)
				event.acceptProposedAction()
			else:
				self.setStyleSheet(self._reject_style)
				self.setText(
					f".{unsupported_ext} is not supported<br>"
					f"{self._supported_text}"
				)
				event.ignore()
		else:
			self.setStyleSheet(self._reject_style)
			self.setText(
				"File type not supported<br>"
				f"{self._supported_text}"
			)
			event.ignore()

	def dragLeaveEvent(self, event):
		self.setStyleSheet(self._default_style)
		self.setText(self._default_text)

	def dropEvent(self, event: QDropEvent):
		self.setStyleSheet(self._default_style)
		self.setText(self._default_text)
		if event.mimeData().hasUrls():
			paths = [url.toLocalFile() for url in event.mimeData().urls()]
			if self.on_files_dropped:
				self.on_files_dropped(paths)
			else:
				mainwin = self.window()
				if hasattr(mainwin, "db") and hasattr(mainwin, "table"):
					if import_files(mainwin, mainwin.db, file_paths=paths):
						mainwin.table.refresh_table()

	def _is_supported_file(self, path):
		ext = os.path.splitext(path)[1].lower()
		return ext in self._supported_exts
