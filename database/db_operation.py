import sqlite3

from config import BASE_PATH
import os
DB_PATH = os.path.join(BASE_PATH, 'database', 'database.db')

class ImageTeaDB:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            api_key TEXT,
            note TEXT,
            last_tested TEXT,
            status TEXT
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

    def set_api_key(self, service, api_key, note=None, last_tested=None, status=None):
        c = self.conn.cursor()
        c.execute('SELECT id FROM api_keys WHERE service=? AND api_key=?', (service, api_key))
        row = c.fetchone()
        if row:
            c.execute('''UPDATE api_keys SET note=?, last_tested=?, status=? WHERE id=?''',
                      (note, last_tested, status, row[0]))
        else:
            c.execute('''INSERT INTO api_keys (service, api_key, note, last_tested, status)
                         VALUES (?, ?, ?, ?, ?)''',
                      (service, api_key, note, last_tested, status))
        self.conn.commit()

    def get_api_key(self, service):
        c = self.conn.cursor()
        c.execute('SELECT api_key, note, last_tested, status FROM api_keys WHERE service=? ORDER BY id DESC LIMIT 1', (service,))
        row = c.fetchone()
        if row:
            return {
                'api_key': row[0],
                'note': row[1],
                'last_tested': row[2],
                'status': row[3]
            }
        return None

    def update_api_key_note(self, api_key, note):
        c = self.conn.cursor()
        c.execute('UPDATE api_keys SET note=? WHERE api_key=?', (note, api_key))
        self.conn.commit()

    def update_api_key_last_tested(self, api_key, last_tested):
        c = self.conn.cursor()
        c.execute('UPDATE api_keys SET last_tested=? WHERE api_key=?', (last_tested, api_key))
        self.conn.commit()

    def update_api_key_status(self, api_key, status):
        c = self.conn.cursor()
        c.execute('UPDATE api_keys SET status=? WHERE api_key=?', (status, api_key))
        self.conn.commit()

    def delete_api_key(self, service, api_key):
        c = self.conn.cursor()
        c.execute('DELETE FROM api_keys WHERE service=? AND api_key=?', (service, api_key))
        self.conn.commit()

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

    def get_all_api_keys(self):
        c = self.conn.cursor()
        c.execute('SELECT service, api_key, note, last_tested, status FROM api_keys')
        return c.fetchall()