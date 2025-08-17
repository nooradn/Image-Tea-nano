from PySide6.QtWidgets import QFileDialog
import os
from helpers.metadata_helper.metadata_operation import read_metadata_pyexiv2, read_metadata_video

def import_files(parent, db, is_image_file, is_video_file, file_paths=None):
    if file_paths is None:
        home_dir = os.path.expanduser("~")
        files, _ = QFileDialog.getOpenFileNames(
            parent,
            "Select Images or Videos",
            home_dir,
            "Images/Videos (*.jpg *.jpeg *.png *.bmp *.gif *.mp4 *.mpeg *.mov *.avi *.flv *.mpg *.webm *.wmv *.3gp *.3gpp)"
        )
    else:
        files = file_paths
    added = 0
    video_exts = {'.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp', '.mkv'}
    for path in files:
        if os.path.isfile(path):
            fname = os.path.basename(path)
            ext = os.path.splitext(path)[1].lower()
            if ext in video_exts:
                t, d, tg = read_metadata_video(path)
            else:
                t, d, tg = read_metadata_pyexiv2(path)
            title = t if t else None
            description = d if d else None
            tags = tg if tg else None
            db.add_file(path, fname, title, description, tags, status="draft", original_filename=fname)
            added += 1
    return bool(added)
