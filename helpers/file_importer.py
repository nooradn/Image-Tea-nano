from PySide6.QtWidgets import QFileDialog
import os
from helpers.metadata_helper.metadata_operation import read_metadata_pyexiv2, read_metadata_video

try:
    from PIL import Image
    PILLOW_FORMATS = set()
    for ext, fmt in Image.registered_extensions().items():
        PILLOW_FORMATS.add(ext.lower())
except ImportError:
    PILLOW_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

def import_files(parent, db, file_paths=None):
    if file_paths is None:
        home_dir = os.path.expanduser("~")
        video_exts = {'.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp'}
        all_exts = sorted(PILLOW_FORMATS | video_exts)
        filter_str = "Images/Videos (" + " ".join(f"*{ext}" for ext in all_exts) + ")"
        files, _ = QFileDialog.getOpenFileNames(
            parent,
            "Select Images or Videos",
            home_dir,
            filter_str
        )
    else:
        files = file_paths
    added = 0
    video_exts = {'.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp'}
    for path in files:
        if os.path.isfile(path):
            fname = os.path.basename(path)
            ext = os.path.splitext(path)[1].lower()
            if ext in video_exts:
                try:
                    t, d, tg = read_metadata_video(path)
                except Exception as e:
                    print(f"[IMPORT ERROR] {fname}: {e}")
                    t, d, tg = None, None, None
            elif ext in PILLOW_FORMATS:
                try:
                    t, d, tg = read_metadata_pyexiv2(path)
                except Exception as e:
                    print(f"[IMPORT ERROR] {fname}: {e}")
                    t, d, tg = None, None, None
            else:
                print(f"[IMPORT SKIP] {fname}: Unsupported file extension {ext}")
                continue
            title = t if t else None
            description = d if d else None
            tags = tg if tg else None
            db.add_file(path, fname, title, description, tags, status="draft", original_filename=fname)
            added += 1
    return bool(added)
