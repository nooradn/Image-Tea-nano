import os
import urllib.request
import zipfile
from config import BASE_PATH

expected = [
    "exiftool",
    "ghostscript"
]
expected_full = [os.path.join(BASE_PATH, "tools", f) for f in expected]

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
        print(f"Downloading Ghostscript to {filename} ...")
        try:
            urllib.request.urlretrieve(url, filename)
            print("Ghostscript downloaded successfully.")
        except Exception as e:
            print(f"Failed to download Ghostscript: {e}")

def download_and_extract_exiftool(target_folder):
    url = "https://github.com/mudrikam/exiftool-for-image-tea/archive/refs/heads/main.zip"
    zip_path = os.path.join(target_folder, "exiftool.zip")
    print(f"Downloading Exiftool to {zip_path} ...")
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("Download complete. Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_folder)
            # Move extracted files from subfolder to target_folder
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
