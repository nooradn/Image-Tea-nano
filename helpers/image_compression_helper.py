import os
import json
from PIL import Image
import config

BASE_PATH = config.BASE_PATH

def ensure_temp_folder():
    temp_folder = os.path.join(BASE_PATH, "temp", "images")
    os.makedirs(temp_folder, exist_ok=True)
    return temp_folder

def get_compression_quality():
    config_path = os.path.join(BASE_PATH, "configs", "ai_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config_json = json.load(f)
    return config_json["compression_quality"]

def cleanup_temp_folder():
    temp_folder = ensure_temp_folder()
    for filename in os.listdir(temp_folder):
        file_path = os.path.join(temp_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning temp file {file_path}: {e}")

def compress_and_save_image(image_path):
    cleanup_temp_folder()
    temp_folder = ensure_temp_folder()
    quality = get_compression_quality()
    try:
        with Image.open(image_path) as img:
            rgb_img = img.convert("RGB")
            filename = os.path.splitext(os.path.basename(image_path))[0] + ".jpg"
            save_path = os.path.join(temp_folder, filename)
            rgb_img.save(
                save_path, 
                "JPEG", 
                quality=quality, 
                optimize=True
                )
            return save_path
    except Exception as e:
        print(f"Error compressing image: {e}")
        return None