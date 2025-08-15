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

	def dragEnterEvent(self, event: QDragEnterEvent):
		if event.mimeData().hasUrls():
			event.acceptProposedAction()

	def dropEvent(self, event: QDropEvent):
		if event.mimeData().hasUrls():
			paths = [url.toLocalFile() for url in event.mimeData().urls()]
			if self.on_files_dropped:
				self.on_files_dropped(paths)
			else:
				# fallback: cari parent window yang punya handle_dropped_files
				mainwin = self.window()
				if hasattr(mainwin, 'handle_dropped_files'):
					mainwin.handle_dropped_files(paths)
