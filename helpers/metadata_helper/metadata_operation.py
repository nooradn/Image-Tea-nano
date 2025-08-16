import pyexiv2
from helpers.ai_helper.gemini_helper import generate_metadata_gemini
from database.db_operation import ImageTeaDB, DB_PATH

from PySide6.QtCore import QThread, Signal

def _extract_xmp_value(val):
	if isinstance(val, dict):
		# pyexiv2 XMP dict: {'lang="x-default"': 'Title'}
		return next(iter(val.values()), '')
	return val if isinstance(val, str) else ''

class ImageTeaGeneratorThread(QThread):
	progress = Signal(int, int)  # current, total
	finished = Signal(list)
	row_status = Signal(int, str)  # row index, status: 'processing', 'success', 'failed'

	def __init__(self, api_key, model, rows, db_path):
		super().__init__()
		self.api_key = api_key
		self.model = model
		self.rows = rows
		self.db_path = db_path
		self.errors = []

	def run(self):
		db = ImageTeaDB(self.db_path)
		total = len(self.rows)
		for idx, row in enumerate(self.rows, 1):
			id_, filepath, filename, title, description, tags, status = row
			self.row_status.emit(idx - 1, "processing")
			try:
				t, d, tg = generate_metadata_gemini(self.api_key, self.model, filepath)
				t = _extract_xmp_value(t)
				d = _extract_xmp_value(d)
				if not t:
					db.update_file_status(filepath, "failed")
					self.errors.append(f"{filename}: Failed to generate metadata")
					self.row_status.emit(idx - 1, "failed")
				else:
					db.update_metadata(filepath, t, d, tg, status="success")
					self.row_status.emit(idx - 1, "success")
			except Exception as e:
				db.update_file_status(filepath, "failed")
				self.errors.append(f"{filename}: {e}")
				self.row_status.emit(idx - 1, "failed")
			self.progress.emit(idx, total)
		self.finished.emit(self.errors)

def write_metadata_pyexiv2(file_path, title, description, tag_list):
	try:
		title = _extract_xmp_value(title)
		description = _extract_xmp_value(description)
		with pyexiv2.Image(file_path) as metadata:
			# XMP
			metadata.modify_xmp({
				'Xmp.dc.title': title,
				'Xmp.dc.subject': tag_list,
				'Xmp.dc.description': description
			})
			# IPTC
			metadata.modify_iptc({
				'Iptc.Application2.ObjectName': title,
				'Iptc.Application2.Keywords': tag_list,
				'Iptc.Application2.Caption': description
			})
			# EXIF
			metadata.modify_exif({
				'Exif.Image.ImageDescription': description,
				'Exif.Photo.UserComment': ', '.join(tag_list)
			})
		print(f"[pyexiv2] Metadata written to {file_path}")
	except Exception as e:
		print(f"[pyexiv2 ERROR] {file_path}: {e}")

def read_metadata_pyexiv2(file_path):
	try:
		metadata = pyexiv2.Image(file_path)
		xmp = metadata.read_xmp()
		iptc = metadata.read_iptc()
		exif = metadata.read_exif()

		title = _extract_xmp_value(xmp.get('Xmp.dc.title')) if 'Xmp.dc.title' in xmp else None
		description = _extract_xmp_value(xmp.get('Xmp.dc.description')) if 'Xmp.dc.description' in xmp else None
		tags = xmp.get('Xmp.dc.subject') if 'Xmp.dc.subject' in xmp else None

		if not title:
			title = iptc.get('Iptc.Application2.ObjectName')
			if isinstance(title, list):
				title = title[0] if title else None
		if not title:
			title = exif.get('Exif.Image.ImageDescription')

		if not description:
			description = iptc.get('Iptc.Application2.Caption')
			if isinstance(description, list):
				description = description[0] if description else None
		if not description:
			description = exif.get('Exif.Image.ImageDescription')

		if not tags:
			tags = iptc.get('Iptc.Application2.Keywords')
		if not tags:
			user_comment = exif.get('Exif.Photo.UserComment')
			if user_comment:
				tags = [t.strip() for t in user_comment.split(',')]
		if isinstance(tags, list):
			tags_str = ','.join(tags)
		elif isinstance(tags, str):
			tags_str = tags
		else:
			tags_str = ''

		metadata.close()
		print(f"[pyexiv2 READ] {file_path} | title: {title} | description: {description} | tags: {tags_str}")
		return title, description, tags_str
	except Exception as e:
		print(f"[pyexiv2 READ ERROR] {file_path}: {e}")
		return None, None, None

def write_metadata_to_images(db, _unused1, _unused2):
	rows = db.get_all_files()
	errors = []
	for row in rows:
		id_, filepath, filename, title, description, tags, status = row
		if title or description or tags:
			try:
				tag_list = [t.strip() for t in tags.split(',')] if tags else []
				write_metadata_pyexiv2(filepath, title, description, tag_list)
			except Exception as e:
				errors.append(f"{filename}: {e}")
	if errors:
		print("[Write Metadata Errors]")
		for err in errors:
			print(err)
	else:
		print("[Write Metadata] Metadata written to all images.")