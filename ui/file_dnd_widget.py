from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

class DragDropWidget(QLabel):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setText("Drag and drop images or videos here")
		self.setAlignment(Qt.AlignCenter)
		self.setAcceptDrops(True)
		self.setStyleSheet("border: 2px dashed #aaa; padding: 20px; font-size: 16px;")

	def dragEnterEvent(self, event: QDragEnterEvent):
		if event.mimeData().hasUrls():
			event.acceptProposedAction()

	def dropEvent(self, event: QDropEvent):
		if event.mimeData().hasUrls():
			paths = [url.toLocalFile() for url in event.mimeData().urls()]
			mainwin = self.window()
			if hasattr(mainwin, 'handle_dropped_files'):
				mainwin.handle_dropped_files(paths)
