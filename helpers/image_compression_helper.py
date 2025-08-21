import os
import sys
import json
import subprocess
from PIL import Image
import config

BASE_PATH = config.BASE_PATH

CAIRO_DLL_DIR = os.path.join(BASE_PATH, "tools", "cairo", "cairo-windows-1.17.2", "lib", "x64")
if os.name == "nt":
    if CAIRO_DLL_DIR not in os.environ.get("PATH", ""):
        os.environ["PATH"] = CAIRO_DLL_DIR + ";" + os.environ.get("PATH", "")
    try:
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(CAIRO_DLL_DIR)
    except Exception as e:
        print(f"Error setting Cairo DLL directory: {e}")

PILLOW_FORMATS = set()
for ext, fmt in Image.registered_extensions().items():
    PILLOW_FORMATS.add(ext.lower())

# Ambil Ghostscript dari tools/ghostscript/gswin64c.exe
GHOSTSCRIPT_PATH = os.path.join(BASE_PATH, "tools", "ghostscript", "gswin64c.exe")

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

def convert_eps_pdf_to_jpg(input_path, output_path, quality):
    try:
        args = [
            GHOSTSCRIPT_PATH,
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=jpeg",
            f"-dJPEGQ={quality}",
            "-r300",
            f"-sOutputFile={output_path}",
            input_path
        ]
        subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(output_path):
            return output_path
        else:
            print(f"Ghostscript did not produce output: {output_path}")
            return None
    except Exception as e:
        print(f"Ghostscript error: {e}")
        return None

def convert_svg_to_jpg(input_path, output_path, quality):
    try:
        import cairosvg
        temp_png = output_path.replace(".jpg", ".png")
        cairosvg.svg2png(url=input_path, write_to=temp_png)
        with Image.open(temp_png) as img:
            rgb_img = img.convert("RGB")
            rgb_img.save(output_path, "JPEG", quality=quality, optimize=True)
        os.remove(temp_png)
        return output_path
    except Exception as e:
        print(f"CairoSVG error: {e}")
        return None

def compress_and_save_image(image_path):
    cleanup_temp_folder()
    temp_folder = ensure_temp_folder()
    quality = get_compression_quality()
    ext = os.path.splitext(image_path)[1].lower()
    filename = os.path.splitext(os.path.basename(image_path))[0] + ".jpg"
    save_path = os.path.join(temp_folder, filename)

    if ext in (".eps", ".pdf"):
        return convert_eps_pdf_to_jpg(image_path, save_path, quality)
    elif ext == ".svg":
        return convert_svg_to_jpg(image_path, save_path, quality)
    elif ext in PILLOW_FORMATS:
        try:
            with Image.open(image_path) as img:
                rgb_img = img.convert("RGB")
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
    else:
        print(f"Error: File extension {ext} is not supported by Pillow or converters.")
        return None