from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

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
		self._supported_exts = {
			".jpg", ".jpeg", ".png", ".bmp", ".gif",
			".mp4", ".mpeg", ".mov", ".avi", ".flv",
			".mpg", ".webm", ".wmv", ".3gp", ".3gpp"
		}
		self._default_text = "Drag and drop images or videos here"
		self._supported_text = "<span style='font-size:10px;color:#888;'>Supported: jpg, jpeg, png, bmp, gif, mp4, mpeg, mov, avi, flv, mpg, webm, wmv, 3gp, 3gpp</span>"

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
				if hasattr(mainwin, 'handle_dropped_files'):
					mainwin.handle_dropped_files(paths)

	def _is_supported_file(self, path):
		ext = path.lower().rsplit('.', 1)[-1] if '.' in path else ''
		return f".{ext}" in self._supported_exts
