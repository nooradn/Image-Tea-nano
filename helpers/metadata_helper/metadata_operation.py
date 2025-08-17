import pyexiv2
from database.db_operation import ImageTeaDB, DB_PATH

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox

def _extract_xmp_value(val):
	if isinstance(val, dict):
		return next(iter(val.values()), '')
	return val if isinstance(val, str) else ''

class ImageTeaGeneratorThread(QThread):
	progress = Signal(int, int)
	finished = Signal(list)
	row_status = Signal(int, str)  # row visual index in table, status

	def __init__(self, api_key, model, rows, db_path, row_map=None, generate_metadata_func=None):
		super().__init__()
		self.api_key = api_key
		self.model = model
		self.rows = rows
		self.db_path = db_path
		self.errors = []
		self.row_map = row_map or {}
		self.generate_metadata_func = generate_metadata_func

	def run(self):
		db = ImageTeaDB(self.db_path)
		total = len(self.rows)
		for idx, row in enumerate(self.rows):
			id_, filepath, filename, title, description, tags, status, _ = row
			visual_idx = self.row_map.get(id_, idx)
			self.row_status.emit(visual_idx, "processing")
			try:
				result = self.generate_metadata_func(self.api_key, self.model, filepath)
				if isinstance(result, tuple) and len(result) >= 3:
					t, d, tg = result[0], result[1], result[2]
				else:
					t, d, tg = '', '', ''
				t = _extract_xmp_value(t)
				d = _extract_xmp_value(d)
				if not t:
					db.update_file_status(filepath, "failed")
					self.errors.append(f"{filename}: Failed to generate metadata")
					self.row_status.emit(visual_idx, "failed")
				else:
					db.update_metadata(filepath, t, d, tg, status="success")
					self.row_status.emit(visual_idx, "success")
			except Exception as e:
				db.update_file_status(filepath, "failed")
				self.errors.append(f"{filename}: {e}")
				self.row_status.emit(visual_idx, "failed")
			self.progress.emit(idx + 1, total)
		self.finished.emit(self.errors)

def write_metadata_pyexiv2(file_path, title, description, tag_list):
	try:
		title = _extract_xmp_value(title)
		description = _extract_xmp_value(description)
		if isinstance(tag_list, str):
			tag_list = [t.strip() for t in tag_list.split(',') if t.strip()]
		elif not isinstance(tag_list, list):
			tag_list = []
		subject_str = ', '.join(tag_list)
		# XPSubject must be UTF-16LE encoded and null-terminated for Windows
		def encode_xpsubject(s):
			if not s:
				return b''
			return s.encode('utf-16le') + b'\x00\x00'
		with pyexiv2.Image(file_path) as metadata:
			metadata.modify_xmp({
				'Xmp.dc.title': title,
				'Xmp.dc.subject': tag_list,
				'Xmp.dc.description': description
			})
			metadata.modify_iptc({
				'Iptc.Application2.ObjectName': title,
				'Iptc.Application2.Keywords': tag_list,
				'Iptc.Application2.Caption': description
			})
			exif_dict = {
				'Exif.Image.ImageDescription': description,
				'Exif.Photo.UserComment': ', '.join(tag_list),
				'Exif.Image.XPSubject': encode_xpsubject(subject_str)
			}
			metadata.modify_exif(exif_dict)
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
		if not tags and 'Exif.Image.XPSubject' in exif:
			try:
				xpsubject = exif['Exif.Image.XPSubject']
				if isinstance(xpsubject, bytes):
					xpsubject = xpsubject.decode('utf-16le').rstrip('\x00')
				tags = [t.strip() for t in xpsubject.split(',')]
			except Exception:
				pass
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
		id_, filepath, filename, title, description, tags, status, _ = row
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
		msg_box = QMessageBox()
		msg_box.setIcon(QMessageBox.Warning)
		msg_box.setWindowTitle("Write Metadata")
		msg_box.setText("Some errors occurred while writing metadata.\n\n" + "\n".join(errors))
		try:
			from PySide6.QtWidgets import QApplication
			app = QApplication.instance()
			if app and app.activeWindow():
				msg_box.setWindowIcon(app.activeWindow().windowIcon())
		except Exception:
			pass
		msg_box.exec()
	else:
		msg_box = QMessageBox()
		msg_box.setIcon(QMessageBox.Information)
		msg_box.setWindowTitle("Write Metadata")
		msg_box.setText("Metadata written to all images.")
		try:
			from PySide6.QtWidgets import QApplication
			app = QApplication.instance()
			if app and app.activeWindow():
				msg_box.setWindowIcon(app.activeWindow().windowIcon())
		except Exception:
			pass
		msg_box.exec()