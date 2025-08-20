from database.db_operation import ImageTeaDB
import os
import datetime

def generate_export_filename(platform, output_path):
    today = datetime.datetime.now()
    base_name = f"{platform}_Image_Tea_Metadata_{today.year}_{today.strftime('%B')}_{today.day:02d}_"
    idx = 1
    while True:
        filename = f"{base_name}{idx:03d}.csv"
        full_path = os.path.join(output_path, filename)
        if not os.path.exists(full_path):
            return filename
        idx += 1

def _freepik_format(file):
    filename = file[2]
    title = file[3] if file[3] is not None else ""
    tags = file[5] if file[5] is not None else ""
    prompt = ""
    model = ""
    return f'"{filename}";"{title}";"{tags}";"{prompt}";"{model}"'

def _adobe_stock_format(file, adobe_map, category_mapping):
    filename = file[2]
    title = file[3] if file[3] is not None else ""
    tags = file[5] if file[5] is not None else ""
    file_id = file[0]
    adobe_cat_id = None
    for mapping in category_mapping:
        if mapping['file_id'] == file_id and mapping['platform'] == 'adobe_stock':
            adobe_cat_id = mapping['category_id']
            break
    category_text = str(adobe_cat_id) if adobe_cat_id is not None else ""
    return f'{filename},"{title}","{tags}","{category_text}",'

def _shutterstock_format(file, shutterstock_map, category_mapping):
    filename = file[2]
    description = file[4] if file[4] is not None else ""
    tags = file[5] if file[5] is not None else ""
    file_id = file[0]
    primary = None
    secondary = None
    for mapping in category_mapping:
        if mapping['file_id'] == file_id and mapping['platform'] == 'shutterstock':
            if mapping['category_name'].endswith('(primary)'):
                primary = mapping['category_id']
            elif mapping['category_name'].endswith('(secondary)'):
                secondary = mapping['category_id']
    categories = ""
    if primary and secondary:
        categories = f"{shutterstock_map.get(str(primary), '')},{shutterstock_map.get(str(secondary), '')}"
    elif primary:
        categories = shutterstock_map.get(str(primary), '')
    elif secondary:
        categories = shutterstock_map.get(str(secondary), '')
    editorial = "no"
    mature_content = "no"
    illustration = "yes"
    return f'{filename},"{description}","{tags}","{categories}",{editorial},{mature_content},{illustration}'

def _123rf_format(file):
    filename = file[2]
    title = file[3] if file[3] is not None else ""
    description = file[4] if file[4] is not None else ""
    keywords = file[5] if file[5] is not None else ""
    country = ""
    return f'"{filename}","{title}","{description}","{keywords}","{country}"'

def _vecteezy_format(file):
    filename = file[2]
    title = file[3] if file[3] is not None else ""
    description = file[4] if file[4] is not None else ""
    keywords = file[5] if file[5] is not None else ""
    license_type = "pro"
    return f'{filename},"{title}","{description}","{keywords}",{license_type}'

def _istock_format(file):
    filename = file[2]
    today = datetime.datetime.now()
    created_date = today.strftime("%m/%d/%Y")
    description = file[4] if file[4] is not None else ""
    country = ""
    brief_code = ""
    title = file[3] if file[3] is not None else ""
    keywords = file[5] if file[5] is not None else ""
    return f'{filename},{created_date},"{description}","{country}","{brief_code}","{title}","""{keywords}"""'

def export_csv_for_platforms(platforms, output_path=None, progress_callback=None):
    print(f"[csv_exporter] Exporting CSV for platforms: {platforms}")
    print(f"[csv_exporter] Output path: {output_path}")
    db = ImageTeaDB()
    files = db.get_all_files()
    shutterstock_map, adobe_map = db.get_category_maps()
    category_mapping = db.get_category_mapping()
    if "Freepik" in platforms and output_path:
        rows = []
        header = 'File name;Title;Keywords;Prompt;Model'
        for file in files:
            rows.append(_freepik_format(file))
            if progress_callback:
                progress_callback()
        if rows:
            csv_filename = generate_export_filename("Freepik", output_path)
            csv_path = os.path.join(output_path, csv_filename)
            try:
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write(header + "\n")
                    for row in rows:
                        f.write(row + "\n")
                print(f"[csv_exporter] Freepik CSV exported to: {csv_path}")
            except Exception as e:
                print(f"[csv_exporter] Error exporting Freepik CSV: {e}")
    if "Adobe Stock" in platforms and output_path:
        rows = []
        header = "Filename,Title,Keywords,Category,Releases"
        for file in files:
            rows.append(_adobe_stock_format(file, adobe_map, category_mapping))
            if progress_callback:
                progress_callback()
        if rows:
            csv_filename = generate_export_filename("Adobe_Stock", output_path)
            csv_path = os.path.join(output_path, csv_filename)
            try:
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write(header + "\n")
                    for row in rows:
                        f.write(row + "\n")
                print(f"[csv_exporter] Adobe Stock CSV exported to: {csv_path}")
            except Exception as e:
                print(f"[csv_exporter] Error exporting Adobe Stock CSV: {e}")
    if "Shutterstock" in platforms and output_path:
        rows = []
        header = "Filename,Description,Keywords,Categories,Editorial,Mature content,illustration"
        for file in files:
            rows.append(_shutterstock_format(file, shutterstock_map, category_mapping))
            if progress_callback:
                progress_callback()
        if rows:
            csv_filename = generate_export_filename("Shutterstock", output_path)
            csv_path = os.path.join(output_path, csv_filename)
            try:
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write(header + "\n")
                    for row in rows:
                        f.write(row + "\n")
                print(f"[csv_exporter] Shutterstock CSV exported to: {csv_path}")
            except Exception as e:
                print(f"[csv_exporter] Error exporting Shutterstock CSV: {e}")
    if "123RF" in platforms and output_path:
        rows = []
        header = '"oldfilename","123rf_filename","description","keywords","country"'
        for file in files:
            rows.append(_123rf_format(file))
            if progress_callback:
                progress_callback()
        if rows:
            csv_filename = generate_export_filename("123rf", output_path)
            csv_path = os.path.join(output_path, csv_filename)
            try:
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write(header + "\n")
                    for row in rows:
                        f.write(row + "\n")
                print(f"[csv_exporter] 123rf CSV exported to: {csv_path}")
            except Exception as e:
                print(f"[csv_exporter] Error exporting 123rf CSV: {e}")
    if "Vecteezy" in platforms and output_path:
        rows = []
        header = "Filename,Title,Description,Keywords,License"
        for file in files:
            rows.append(_vecteezy_format(file))
            if progress_callback:
                progress_callback()
        if rows:
            csv_filename = generate_export_filename("Vecteezy", output_path)
            csv_path = os.path.join(output_path, csv_filename)
            try:
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write(header + "\n")
                    for row in rows:
                        f.write(row + "\n")
                print(f"[csv_exporter] Vecteezy CSV exported to: {csv_path}")
            except Exception as e:
                print(f"[csv_exporter] Error exporting Vecteezy CSV: {e}")
    if "iStock" in platforms and output_path:
        rows = []
        header = "file name,created date,description,country,brief code,title,keywords"
        for file in files:
            rows.append(_istock_format(file))
            if progress_callback:
                progress_callback()
        if rows:
            csv_filename = generate_export_filename("iStock", output_path)
            csv_path = os.path.join(output_path, csv_filename)
            try:
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write(header + "\n")
                    for row in rows:
                        f.write(row + "\n")
                print(f"[csv_exporter] iStock CSV exported to: {csv_path}")
            except Exception as e:
                print(f"[csv_exporter] Error exporting iStock CSV: {e}")
