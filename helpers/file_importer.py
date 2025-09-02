from PySide6.QtWidgets import QFileDialog, QProgressDialog, QApplication
from PySide6.QtCore import QThread, Signal, Qt, QTimer
import os
import signal
import threading
from helpers.metadata_helper.metadata_operation import read_metadata_pyexiv2, read_metadata_video

try:
    from PIL import Image
    PILLOW_FORMATS = set()
    for ext, fmt in Image.registered_extensions().items():
        PILLOW_FORMATS.add(ext.lower())
except ImportError:
    PILLOW_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.eps', '.svg', '.pdf'}

class FileImportThread(QThread):
    progress = Signal(int, int, str)  # current, total, filename
    finished = Signal(int, list)  # added_count, errors
    
    def __init__(self, db, file_paths):
        super().__init__()
        self.db = db
        self.file_paths = file_paths
        self.added = 0
        self.errors = []
    
    def read_metadata_lightweight(self, file_path, ext):
        """Lightweight metadata reading that skips heavy operations."""
        # For now, just return basic file info without metadata reading
        # This prevents hanging while still allowing file import
        fname = os.path.basename(file_path)
        # Use filename (without extension) as default title
        title = os.path.splitext(fname)[0].replace('_', ' ').replace('-', ' ').title()
        return title, None, None
    
    def read_metadata_with_timeout(self, metadata_func, file_path, timeout=10):
        """Read metadata with timeout to prevent hanging on problematic files."""
        result = [None, None, None]  # title, description, tags
        exception = [None]
        completed = [False]
        
        def target():
            try:
                print(f"[METADATA] Starting to read {os.path.basename(file_path)}")
                result[0], result[1], result[2] = metadata_func(file_path)
                completed[0] = True
                print(f"[METADATA] Completed reading {os.path.basename(file_path)}")
            except Exception as e:
                exception[0] = e
                completed[0] = True
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if not completed[0] or thread.is_alive():
            print(f"[IMPORT TIMEOUT] Metadata reading timeout for {os.path.basename(file_path)}, using lightweight fallback")
            # Use lightweight fallback instead
            return self.read_metadata_lightweight(file_path, os.path.splitext(file_path)[1].lower())
        
        if exception[0]:
            print(f"[IMPORT ERROR] Metadata reading failed for {os.path.basename(file_path)}, using lightweight fallback: {exception[0]}")
            return self.read_metadata_lightweight(file_path, os.path.splitext(file_path)[1].lower())
            
        return result[0], result[1], result[2]
        
    def run(self):
        """Process files in a separate thread to avoid blocking UI."""
        video_exts = {'.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp'}
        extra_exts = {'.svg', '.eps', '.pdf'}
        
        total_files = len(self.file_paths)
        
        # Get existing file paths once to avoid repeated database queries
        existing_file_paths = set()
        try:
            existing_files = self.db.get_all_files()
            existing_file_paths = {row[1] for row in existing_files}
        except Exception as e:
            print(f"[IMPORT WARNING] Could not load existing files: {e}")
        
        for idx, path in enumerate(self.file_paths):
            if self.isInterruptionRequested():
                break
                
            if not os.path.isfile(path):
                self.errors.append(f"File not found: {path}")
                continue
                
            fname = os.path.basename(path)
            ext = os.path.splitext(path)[1].lower()
            
            self.progress.emit(idx + 1, total_files, fname)
            
            # Skip if file already exists in database
            if path in existing_file_paths:
                print(f"[IMPORT SKIP] {fname}: File already exists in database")
                continue
            
            # Use fast import mode - skip metadata reading to prevent hanging
            # Metadata can be generated later using the AI generation feature
            print(f"[IMPORT FAST] {fname}: Using fast import (metadata will be generated later)")
            
            # Generate a basic title from filename
            base_name = os.path.splitext(fname)[0]
            title = base_name.replace('_', ' ').replace('-', ' ').title()
            
            t, d, tg = title, None, None
            
            # Add file to database
            try:
                title = t if t else None
                description = d if d else None
                tags = tg if tg else None
                self.db.add_file(path, fname, title, description, tags, status="draft", original_filename=fname)
                self.added += 1
                print(f"[IMPORT SUCCESS] {fname}: Added to database")
            except Exception as e:
                self.errors.append(f"{fname}: Database error - {e}")
        
        self.finished.emit(self.added, self.errors)

def import_files(parent, db, file_paths=None):
    """Import files asynchronously with progress dialog."""
    if file_paths is None:
        home_dir = os.path.expanduser("~")
        video_exts = {'.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp'}
        extra_exts = {'.svg', '.eps', '.pdf'}
        all_exts = sorted(PILLOW_FORMATS | video_exts | extra_exts)
        filter_str = "Images/Videos (" + " ".join(f"*{ext}" for ext in all_exts) + ")"
        files, _ = QFileDialog.getOpenFileNames(
            parent,
            "Select Images or Videos",
            home_dir,
            filter_str
        )
    else:
        files = file_paths
    
    if not files:
        return False
    
    # Filter out non-existent files
    valid_files = [f for f in files if os.path.isfile(f)]
    if not valid_files:
        return False
    
    # Create progress dialog
    progress_dialog = QProgressDialog("Importing files...", "Cancel", 0, len(valid_files), parent)
    progress_dialog.setWindowTitle("Importing Files")
    progress_dialog.setWindowModality(Qt.WindowModal)
    progress_dialog.setMinimumDuration(0)
    progress_dialog.setValue(0)
    progress_dialog.setAutoClose(False)
    progress_dialog.setAutoReset(False)
    
    # Create and start import thread
    import_thread = FileImportThread(db, valid_files)
    
    def on_progress(current, total, filename):
        if progress_dialog.wasCanceled():
            import_thread.requestInterruption()
            return
        progress_dialog.setValue(current)
        progress_dialog.setLabelText(f"Importing: {filename}")
        QApplication.processEvents()
    
    def on_finished(added_count, errors):
        progress_dialog.close()
        
        # Show results
        from PySide6.QtWidgets import QMessageBox
        if errors:
            error_msg = f"Imported {added_count} files with {len(errors)} errors:\n\n"
            error_msg += "\n".join(errors[:10])  # Show first 10 errors
            if len(errors) > 10:
                error_msg += f"\n... and {len(errors) - 10} more errors"
            QMessageBox.warning(parent, "Import Completed with Errors", error_msg)
        elif added_count > 0:
            QMessageBox.information(parent, "Import Successful", f"Successfully imported {added_count} files.")
        else:
            QMessageBox.information(parent, "Import Complete", "No new files were imported.")
        
        # Refresh the table if parent has it
        if hasattr(parent, 'table') and hasattr(parent.table, 'refresh_table'):
            parent.table.refresh_table()
    
    # Connect signals
    import_thread.progress.connect(on_progress)
    import_thread.finished.connect(on_finished)
    
    # Handle dialog cancel
    def on_cancel():
        import_thread.requestInterruption()
        import_thread.wait(3000)  # Wait up to 3 seconds for thread to finish
        progress_dialog.close()
    
    progress_dialog.canceled.connect(on_cancel)
    
    # Start the import process
    import_thread.start()
    progress_dialog.exec()
    
    # Wait for thread to finish if not already done
    if import_thread.isRunning():
        import_thread.wait()
    
    return True
