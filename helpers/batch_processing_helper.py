import json
import os
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QColor
from config import BASE_PATH

def get_batch_size():
    config_path = os.path.join(BASE_PATH, "configs", "ai_config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return int(config['batch_size'])

class BatchWorkerSignals(QObject):
    finished = Signal(list)
    progress = Signal(int, int)
    row_status = Signal(int, str)

class BatchWorker(QThread):
    def __init__(self, api_key, model, batch, service, metadata_func, row_map, parent=None, stop_flag=None):
        super().__init__(parent)
        self.api_key = api_key
        self.model = model
        self.batch = batch
        self.service = service
        self.metadata_func = metadata_func
        self.row_map = row_map
        self.signals = BatchWorkerSignals()
        self._results = []
        self._errors = []
        self._should_stop = False
        self._external_stop_flag = stop_flag

    def stop(self):
        self._should_stop = True
        if self._external_stop_flag is not None:
            self._external_stop_flag['stop'] = True

    def run(self):
        from concurrent.futures import ThreadPoolExecutor, Future
        cache_results = []
        errors = []
        futures = []
        stop_flag = self._external_stop_flag
        with ThreadPoolExecutor(max_workers=len(self.batch)) as executor:
            for row in self.batch:
                if self._should_stop or (stop_flag and stop_flag.get('stop')):
                    break
                image_path = row[1]
                prompt = None
                futures.append(executor.submit(self.metadata_func, self.api_key, self.model, image_path, prompt, stop_flag))
            completed = 0
            for idx, future in enumerate(futures):
                if self._should_stop or (stop_flag and stop_flag.get('stop')):
                    break
                try:
                    result = future.result()
                    cache_results.append((completed, result))
                except Exception as e:
                    errors.append(str(e))
                completed += 1
                self.signals.progress.emit(completed, len(self.batch))
            if self._should_stop or (stop_flag and stop_flag.get('stop')):
                for f in futures[completed:]:
                    if isinstance(f, Future) and not f.done():
                        f.cancel()
        self._results = cache_results
        self._errors = errors
        self.signals.finished.emit(errors)

def batch_generate_metadata(window):
    if getattr(window, 'is_generating', False):
        return

    api_key = None
    model = None
    service = None
    if hasattr(window, "api_key_combo") and hasattr(window, "api_key_map"):
        idx = window.api_key_combo.currentIndex()
        api_key = window.api_key_combo.currentData() if idx >= 0 else None
        if api_key and api_key in window.api_key_map:
            model = window.api_key_map[api_key].get("model")
            service = window.api_key_map[api_key].get("service")
            if service:
                service = service.lower()
    if not api_key or not model or not service:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(window, "API Key", "Please select both API Key and Model first.")
        return

    mode = "all"
    selected_ids = []
    row_map = {}
    if hasattr(window, "gen_mode_combo"):
        mode_idx = window.gen_mode_combo.currentIndex()
        mode_text = window.gen_mode_combo.currentText().lower()
        if "selected" in mode_text:
            mode = "selected"
        elif "failed" in mode_text:
            mode = "failed"
        else:
            mode = "all"
    rows = []
    all_rows = window.db.get_all_files()
    if mode == "all":
        rows = all_rows
    elif mode == "selected":
        table_widget = window.table.table
        selected_ids = []
        for row_idx in range(table_widget.rowCount()):
            checkbox_item = table_widget.item(row_idx, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                id_data = checkbox_item.data(Qt.UserRole)
                if id_data is not None:
                    try:
                        selected_ids.append(int(id_data))
                        row_map[int(id_data)] = row_idx
                    except Exception:
                        print(f"[DEBUG] Failed to parse id from checkbox row {row_idx}: {id_data}")
        print(f"[DEBUG] Selected IDs for generate: {selected_ids}")
        rows = [row for row in all_rows if row[0] in selected_ids]
    elif mode == "failed":
        rows = [row for row in all_rows if row[6] == "failed"]
    if mode == "selected" and not selected_ids:
        print("[DEBUG] No rows checked for Selected Only mode.")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(window, "No Files", "No files selected (checkbox) to process.")
        return
    if not rows:
        print("[DEBUG] No rows to process after filtering.")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(window, "No Files", "No files to process.")
        return

    window.table.progress_bar.setVisible(True)
    window.table.progress_bar.setMinimum(0)
    window.table.progress_bar.setMaximum(len(rows))
    window.table.progress_bar.setValue(0)
    window.table.progress_bar.setFormat('Generating metadata...')
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()

    stop_flag = {'stop': False}
    if service == "gemini":
        from helpers.ai_helper.gemini_helper import generate_metadata_gemini, track_gemini_generation_time
        def metadata_func(api_key, model, image_path, prompt=None, stop_flag=None):
            if stop_flag and stop_flag.get('stop'):
                return {'title': '', 'description': '', 'tags': '', 'token_input': 0, 'token_output': 0, 'token_total': 0, 'image_path': image_path}
            import time
            t0 = time.perf_counter()
            title, description, tags, token_input, token_output, token_total = generate_metadata_gemini(api_key, model, image_path, prompt, stop_flag)
            t1 = time.perf_counter()
            duration_ms = int((t1 - t0) * 1000)
            gen_time, avg_time, longest_time, last_time = track_gemini_generation_time(duration_ms)
            if hasattr(window, "stats_section"):
                window.stats_section.update_generation_times(gen_time, avg_time, longest_time, last_time)
            return {
                "title": title,
                "description": description,
                "tags": tags,
                "token_input": token_input,
                "token_output": token_output,
                "token_total": token_total,
                "image_path": image_path
            }
    elif service == "openai":
        from helpers.ai_helper.openai_helper import generate_metadata_openai, track_openai_generation_time
        def metadata_func(api_key, model, image_path, prompt=None, stop_flag=None):
            if stop_flag and stop_flag.get('stop'):
                return {'title': '', 'description': '', 'tags': '', 'token_input': 0, 'token_output': 0, 'token_total': 0, 'image_path': image_path}
            import time
            t0 = time.perf_counter()
            title, description, tags, error_message, token_input, token_output, token_total = generate_metadata_openai(api_key, model, image_path, prompt, stop_flag)
            t1 = time.perf_counter()
            duration_ms = int((t1 - t0) * 1000)
            gen_time, avg_time, longest_time, last_time = track_openai_generation_time(duration_ms)
            if hasattr(window, "stats_section"):
                window.stats_section.update_generation_times(gen_time, avg_time, longest_time, last_time)
            if error_message:
                window.show_ai_unsupported_dialog.emit(error_message)
                return {
                    "title": "",
                    "description": "",
                    "tags": "",
                    "token_input": token_input,
                    "token_output": token_output,
                    "token_total": token_total,
                    "image_path": image_path
                }
            return {
                "title": title,
                "description": description,
                "tags": tags,
                "token_input": token_input,
                "token_output": token_output,
                "token_total": token_total,
                "image_path": image_path
            }
    else:
        print(f"[DEBUG] Unknown service: {service}")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(window, "API Service", f"Unknown service: {service}")
        window.table.progress_bar.setVisible(False)
        window.table.progress_bar.setValue(0)
        window.table.progress_bar.setFormat('')
        return

    batch_size = get_batch_size()
    total_files = len(rows)
    batches = [rows[i:i+batch_size] for i in range(0, total_files, batch_size)]
    window._batch_processing_state = {
        'batches': batches,
        'current': 0,
        'errors': [],
        'api_key': api_key,
        'model': model,
        'service': service,
        'row_map': row_map,
        'metadata_func': metadata_func,
        'rows': rows,
        'should_stop': False,
        'worker': None,
        'stop_flag': stop_flag
    }
    window.is_generating = True
    _set_gen_btn_stop_state(window, True)
    _run_next_batch(window)

def _run_next_batch(window):
    state = window._batch_processing_state
    if state.get('should_stop', False):
        _on_generation_finished(window, state['errors'], stopped=True)
        return
    if state['current'] >= len(state['batches']):
        _on_generation_finished(window, state['errors'])
        return
    batch = state['batches'][state['current']]
    api_key = state['api_key']
    model = state['model']
    service = state['service']
    row_map = state['row_map']
    metadata_func = state['metadata_func']
    rows = state['rows']
    stop_flag = state.get('stop_flag')
    batch_indices = []
    table_widget = window.table.table
    for row in batch:
        filepath = row[1]
        for row_idx in range(table_widget.rowCount()):
            item = table_widget.item(row_idx, 1)
            if item and item.text() == filepath:
                batch_indices.append(row_idx)
                window.table.set_row_status_color(row_idx, "processing")
    worker = BatchWorker(api_key, model, batch, service, metadata_func, row_map, stop_flag=stop_flag)
    state['worker'] = worker
    def on_progress(cur, total):
        if state.get('should_stop', False) or (stop_flag and stop_flag.get('stop')):
            window.table.progress_bar.setFormat('Stopping...')
            window.table.progress_bar.setMinimum(0)
            window.table.progress_bar.setMaximum(0)
        else:
            window.table.progress_bar.setFormat('Generating metadata...')
            window.table.progress_bar.setMinimum(0)
            window.table.progress_bar.setMaximum(len(rows))
            window.table.progress_bar.setValue(state['current'] * get_batch_size() + cur)
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
    def on_finished(errors):
        if state.get('should_stop', False) or (stop_flag and stop_flag.get('stop')):
            for row in batch:
                filepath = row[1]
                window.db.update_file_status(filepath, "stopped")
                for row_idx in range(table_widget.rowCount()):
                    item = table_widget.item(row_idx, 1)
                    if item and item.text() == filepath:
                        window.table.set_row_status_color(row_idx, "stopped")
            window.table.refresh_table()
            window.table.progress_bar.setFormat('Stopped')
            window.table.progress_bar.setValue(0)
            window.table.progress_bar.setMinimum(0)
            window.table.progress_bar.setMaximum(1)
            window.table.progress_bar.setVisible(True)
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            _on_generation_finished(window, state['errors'], stopped=True)
            return
        cache_results = worker._results
        for idx, result in cache_results:
            if not isinstance(result, dict):
                continue
            image_path = result.get("image_path")
            title = result.get("title")
            description = result.get("description")
            tags = result.get("tags")
            token_input = result.get("token_input")
            token_output = result.get("token_output")
            token_total = result.get("token_total")
            window.db.update_metadata(image_path, title, description, tags, status="success" if title else "failed")
            window.db.insert_api_token_stats(image_path, service, model, token_input, token_output, token_total)
        update_token_stats_ui(window)
        for row in batch:
            filepath = row[1]
            for row_idx in range(table_widget.rowCount()):
                item = table_widget.item(row_idx, 1)
                if item and item.text() == filepath:
                    if any(r.get("image_path") == filepath and r.get("title") for _, r in cache_results if isinstance(r, dict)):
                        window.table.set_row_status_color(row_idx, "success")
                    else:
                        window.table.set_row_status_color(row_idx, "failed")
        window.table.refresh_table()
        window.table.progress_bar.setFormat('Generating metadata...')
        window.table.progress_bar.setMinimum(0)
        window.table.progress_bar.setMaximum(len(rows))
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        state['current'] += 1
        if errors:
            state['errors'].extend(errors)
        _run_next_batch(window)
    worker.signals.progress.connect(on_progress)
    worker.signals.finished.connect(on_finished)
    worker.start()

def stop_generate_metadata(window):
    state = getattr(window, '_batch_processing_state', None)
    if state and state.get('worker'):
        worker = state['worker']
        if worker.isRunning():
            print("[STOP] Stopping batch worker thread...")
            state['should_stop'] = True
            stop_flag = state.get('stop_flag')
            if stop_flag is not None:
                stop_flag['stop'] = True
            table_widget = window.table.table
            for row in range(table_widget.rowCount()):
                status_item = table_widget.item(row, 8)
                if status_item and status_item.text().lower() == "processing":
                    window.table.set_row_status_color(row, "stopping")
            window.table.progress_bar.setFormat('Stopping...')
            window.table.progress_bar.setMinimum(0)
            window.table.progress_bar.setMaximum(0)
            window.table.progress_bar.setVisible(True)
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            worker.stop()
    window.is_generating = False
    _set_gen_btn_stop_state(window, False)
    window.table.refresh_table()
    print("[STOP] Metadata generation stopped and UI reset.")

def _set_gen_btn_stop_state(window, is_stop):
    if hasattr(window, "gen_btn"):
        import qtawesome as qta
        if is_stop:
            window.gen_btn.setText("Stop Processes")
            window.gen_btn.setIcon(qta.icon('fa5s.stop'))
            window.gen_btn.setStyleSheet("background-color: rgba(204, 0, 0, 0.3);")
        else:
            window.gen_btn.setText("Generate Metadata")
            window.gen_btn.setIcon(qta.icon('fa5s.magic'))
            window.gen_btn.setStyleSheet("")

def _on_generation_finished(window, errors, stopped=False):
    window.is_generating = False
    _set_gen_btn_stop_state(window, False)
    table_widget = window.table.table
    if stopped:
        for row in range(table_widget.rowCount()):
            status_item = table_widget.item(row, 8)
            if status_item and status_item.text().lower() == "stopping":
                filepath_item = table_widget.item(row, 1)
                if filepath_item:
                    filepath = filepath_item.text()
                    window.db.update_file_status(filepath, "stopped")
                window.table.set_row_status_color(row, "stopped")
        window.table.progress_bar.setFormat('Stopped')
        window.table.progress_bar.setValue(0)
        window.table.progress_bar.setMinimum(0)
        window.table.progress_bar.setMaximum(1)
        window.table.progress_bar.setVisible(True)
    else:
        window.table.progress_bar.setFormat('Done')
        window.table.progress_bar.setMaximum(1)
        window.table.progress_bar.setValue(1)
        window.table.progress_bar.setVisible(True)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    window.table.refresh_table()
    update_token_stats_ui(window)
    if errors:
        print("[Gemini Errors]")
        for err in errors:
            print(err)
    else:
        print("[Gemini] Metadata generated for all files.")

def update_token_stats_ui(window):
    if hasattr(window, "stats_section") and hasattr(window.stats_section, "update_token_stats"):
        token_input, token_output, token_total = window.db.get_token_stats_sum()
        window.stats_section.update_token_stats(token_input, token_output, token_total)
