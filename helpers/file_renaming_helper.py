import os

def batch_rename_files(file_list, pattern_func):
    """
    Rename files in file_list using pattern_func which returns new filename for each file.
    Returns a list of tuples: (old_filepath, new_filepath, old_filename, new_filename, success, error)
    """
    results = []
    for idx, file_info in enumerate(file_list):
        old_filepath = file_info['filepath']
        old_filename = file_info['filename']
        try:
            dirpath = os.path.dirname(old_filepath)
            new_filename = pattern_func(file_info, idx)
            new_filepath = os.path.join(dirpath, new_filename)
            if os.path.abspath(old_filepath) == os.path.abspath(new_filepath):
                results.append((old_filepath, new_filepath, old_filename, new_filename, True, None))
                continue
            if os.path.exists(new_filepath):
                results.append((old_filepath, new_filepath, old_filename, new_filename, False, "Target file exists"))
                continue
            os.rename(old_filepath, new_filepath)
            results.append((old_filepath, new_filepath, old_filename, new_filename, True, None))
        except Exception as e:
            results.append((old_filepath, None, old_filename, None, False, str(e)))
    return results
