import pyexiv2
from helpers.ai_helper.gemini_helper import generate_metadata_gemini
from database.db_operation import ImageTeaDB, DB_PATH

from PySide6.QtCore import QThread, Signal

class ImageTeaGeneratorThread(QThread):
	progress = Signal(int, int)  # current, total
	finished = Signal(list)

	def __init__(self, api_key, rows, db_path):
		super().__init__()
		self.api_key = api_key
		self.rows = rows
		self.db_path = db_path
		self.errors = []

	def run(self):
		db = ImageTeaDB(self.db_path)
		total = len(self.rows)
		for idx, (id_, filepath, filename, title, description, tags) in enumerate(self.rows, 1):
			if not title:
				t, d, tg = generate_metadata_gemini(self.api_key, filepath)
				if not t:
					self.errors.append(f"{filename}: Failed to generate metadata")
				else:
					db.update_metadata(filepath, t, d, tg)
			self.progress.emit(idx, total)
		self.finished.emit(self.errors)

def write_metadata_pyexiv2(file_path, title, description, tag_list):
	"""
	Write metadata (title, description, tags) to an image file using pyexiv2.
	"""
	try:
		metadata = pyexiv2.Image(file_path)
		metadata.modify_xmp({
			'Xmp.dc.title': title,
			'Xmp.dc.description': description,
			'Xmp.dc.subject': tag_list
		})
		metadata.close()
		print(f"[pyexiv2] Metadata written to {file_path}")
	except Exception as e:
		print(f"[pyexiv2 ERROR] {file_path}: {e}")

def write_metadata_to_images(db, is_image_file, is_video_file):
	rows = db.get_all_images()
	errors = []
	for id_, filepath, filename, title, description, tags in rows:
		if is_image_file(filepath):
			if title or description or tags:
				try:
					tag_list = [t.strip() for t in tags.split(',')] if tags else []
					write_metadata_pyexiv2(filepath, title or '', description or '', tag_list)
				except Exception as e:
					errors.append(f"{filename}: {e}")
		elif is_video_file(filepath):
			continue
	if errors:
		print("[Write Metadata Errors]")
		for err in errors:
			print(err)
	else:
		print("[Write Metadata] Metadata written to all images.")
