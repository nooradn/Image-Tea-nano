import sqlite3

DB_PATH = 'database.db'

class ImageTeaDB:
	def __init__(self, db_path=DB_PATH):
		self.conn = sqlite3.connect(db_path)
		self._init_db()

	def _init_db(self):
		c = self.conn.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			service TEXT UNIQUE,
			api_key TEXT
		)''')
		c.execute('''CREATE TABLE IF NOT EXISTS images (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			filepath TEXT UNIQUE,
			filename TEXT,
			title TEXT,
			description TEXT,
			tags TEXT
		)''')
		self.conn.commit()

	def set_api_key(self, service, api_key):
		c = self.conn.cursor()
		c.execute('INSERT OR REPLACE INTO api_keys (service, api_key) VALUES (?, ?)', (service, api_key))
		self.conn.commit()

	def get_api_key(self, service):
		c = self.conn.cursor()
		c.execute('SELECT api_key FROM api_keys WHERE service=?', (service,))
		row = c.fetchone()
		return row[0] if row else None

	def add_image(self, filepath, filename, title=None, description=None, tags=None):
		c = self.conn.cursor()
		c.execute('''INSERT OR IGNORE INTO images (filepath, filename, title, description, tags) VALUES (?, ?, ?, ?, ?)''',
				  (filepath, filename, title, description, tags))
		self.conn.commit()

	def update_metadata(self, filepath, title, description, tags):
		c = self.conn.cursor()
		c.execute('''UPDATE images SET title=?, description=?, tags=? WHERE filepath=?''',
				  (title, description, tags, filepath))
		self.conn.commit()

	def delete_image(self, filepath):
		c = self.conn.cursor()
		c.execute('DELETE FROM images WHERE filepath=?', (filepath,))
		self.conn.commit()

	def clear_images(self):
		c = self.conn.cursor()
		c.execute('DELETE FROM images')
		self.conn.commit()

	def get_all_images(self):
		c = self.conn.cursor()
		c.execute('SELECT id, filepath, filename, title, description, tags FROM images')
		return c.fetchall()
