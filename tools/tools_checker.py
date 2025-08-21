import os
import urllib.request
import zipfile
import sys
from config import BASE_PATH

expected = [
    "exiftool",
    "ghostscript"
]
expected_full = [os.path.join(BASE_PATH, "tools", f) for f in expected]

def print_progress_bar(downloaded, total_length):
    if total_length > 0:
        percent = int(downloaded * 100 / total_length)
        bar_length = 40
        filled_length = int(bar_length * percent // 100)
        green = '\033[92m'
        red = '\033[91m'
        reset = '\033[0m'
        bar = f"{green}{'+' * filled_length}{reset}{red}{'-' * (bar_length - filled_length)}{reset}"
        print(f"\r|{bar}| {percent}% ({downloaded}/{total_length} bytes)", end='', flush=True)
        if downloaded >= total_length:
            print()
    else:
        print(f"\rDownloading... ({downloaded} bytes)", end='', flush=True)

def download_with_progress(url, filename):
    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0 and downloaded > total_size:
            downloaded = total_size
        print_progress_bar(downloaded, total_size)
    print(f"Downloading from {url} to {filename} ...")
    try:
        urllib.request.urlretrieve(url, filename, reporthook)
        print("Download finished.")
    except Exception as e:
        print(f"Failed to download: {e}")

def check_folders():
    for folder in expected_full:
        if not os.path.isdir(folder):
            print(f"Missing folder: {folder}")
            os.makedirs(folder, exist_ok=True)
            if folder.endswith("ghostscript"):
                download_ghostscript(folder)
            elif folder.endswith("exiftool"):
                download_and_extract_exiftool(folder)

def download_ghostscript(target_folder):
    url = "https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10051/gs10051w64.exe"
    filename = os.path.join(target_folder, "gs10051w64.exe")
    if not os.path.isfile(filename):
        download_with_progress(url, filename)
        if os.path.isfile(filename):
            print("Ghostscript downloaded successfully.")

def download_and_extract_exiftool(target_folder):
    url = "https://github.com/mudrikam/exiftool-for-image-tea/archive/refs/heads/main.zip"
    zip_path = os.path.join(target_folder, "exiftool.zip")
    print(f"Downloading Exiftool to {zip_path} ...")
    try:
        download_with_progress(url, zip_path)
        print("Download complete. Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_folder)
            extracted_root = None
            for name in zip_ref.namelist():
                root = name.split('/')[0]
                if root:
                    extracted_root = os.path.join(target_folder, root)
                    break
            if extracted_root and os.path.isdir(extracted_root):
                for item in os.listdir(extracted_root):
                    src = os.path.join(extracted_root, item)
                    dst = os.path.join(target_folder, item)
                    if os.path.isdir(src):
                        if not os.path.exists(dst):
                            os.rename(src, dst)
                    else:
                        os.replace(src, dst)
                try:
                    os.rmdir(extracted_root)
                except Exception:
                    pass
        os.remove(zip_path)
        print("Exiftool extracted successfully.")
    except Exception as e:
        print(f"Failed to download or extract Exiftool: {e}")

if __name__ == "__main__":
    check_folders()
