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
    # Prompt and Model are empty strings as requested
    prompt = ""
    model = ""
    return f'"{filename}";"{title}";"{tags}";"{prompt}";"{model}"'

def _adobe_stock_format(file):
    filename = file[2]
    title = file[3] if file[3] is not None else ""
    tags = file[5] if file[5] is not None else ""
    return f'{filename},"{title}","{tags}",,'

def _shutterstock_format(file):
    filename = file[2]
    description = file[4] if file[4] is not None else ""
    tags = file[5] if file[5] is not None else ""
    categories = ""
    editorial = "no"
    mature_content = "no"
    illustration = "yes"
    return f'{filename},"{description}","{tags}","{categories}",{editorial},{mature_content},{illustration}'

def export_csv_for_platforms(platforms, output_path=None):
    print(f"[csv_exporter] Exporting CSV for platforms: {platforms}")
    print(f"[csv_exporter] Output path: {output_path}")
    db = ImageTeaDB()
    files = db.get_all_files()
    if "Freepik" in platforms and output_path:
        rows = []
        header = 'File name;Title;Keywords;Prompt;Model'
        for file in files:
            rows.append(_freepik_format(file))
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
            rows.append(_adobe_stock_format(file))
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
            rows.append(_shutterstock_format(file))
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
