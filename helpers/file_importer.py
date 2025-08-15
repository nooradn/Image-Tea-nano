from PySide6.QtWidgets import QFileDialog
import os

def import_files(parent, db, is_image_file, is_video_file):
    files, _ = QFileDialog.getOpenFileNames(
        parent,
        "Select Images or Videos",
        "",
        "Images/Videos (*.jpg *.jpeg *.png *.bmp *.gif *.mp4 *.mpeg *.mov *.avi *.flv *.mpg *.webm *.wmv *.3gp *.3gpp)"
    )
    for path in files:
        fname = os.path.basename(path)
        db.add_file(path, fname)
    return bool(files)
