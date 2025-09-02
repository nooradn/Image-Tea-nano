from database.db_operation import ImageTeaDB
import os
import datetime
import json
from config import BASE_PATH

def generate_export_filename(output_path):
    """Generate a unique filename for CSV export with timestamp."""
    today = datetime.datetime.now()
    base_name = f"Image_Tea_Metadata_{today.year}_{today.strftime('%B')}_{today.day:02d}_"
    idx = 1
    while True:
        filename = f"{base_name}{idx:03d}.csv"
        full_path = os.path.join(output_path, filename)
        if not os.path.exists(full_path):
            return filename
        idx += 1

def load_csv_config():
    """Load CSV configuration settings."""
    config_path = os.path.join(BASE_PATH, "configs", "csv_config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"export_format": "unified", "include_headers": True, "encoding": "utf-8"}

def format_csv_value(value):
    """Format a value for CSV output, handling nulls and escaping quotes."""
    if value is None:
        return ""
    # Escape quotes by doubling them and wrap in quotes if contains comma or quotes
    str_value = str(value)
    if '"' in str_value:
        str_value = str_value.replace('"', '""')
    if ',' in str_value or '"' in str_value or '\n' in str_value:
        return f'"{str_value}"'
    return str_value

def format_unified_row(file, shutterstock_map, category_mapping):
    """Format a file record according to the unified SQL definition."""
    file_id = file[0]
    filename = file[2] if file[2] is not None else ""
    title = file[3] if file[3] is not None else ""
    description = file[4] if file[4] is not None else ""
    keywords = file[5] if file[5] is not None else ""
    
    # Get Shutterstock category text
    ss_category = ""
    shutterstock_cats = []
    for mapping in category_mapping:
        if mapping['file_id'] == file_id and mapping['platform'] == 'shutterstock':
            category_id = mapping['category_id']
            category_text = shutterstock_map.get(str(category_id), '')
            if category_text:
                shutterstock_cats.append(category_text)
    if shutterstock_cats:
        ss_category = ", ".join(shutterstock_cats)
    
    # Get Adobe Stock category code (integer)
    as_code = ""
    for mapping in category_mapping:
        if mapping['file_id'] == file_id and mapping['platform'] == 'adobe_stock':
            as_code = str(mapping['category_id']) if mapping['category_id'] is not None else ""
            break
    
    # Format all values for CSV
    return ",".join([
        format_csv_value(filename),
        format_csv_value(title),
        format_csv_value(description),
        format_csv_value(keywords),
        format_csv_value(ss_category),
        format_csv_value(as_code)
    ])

def export_csv(output_path=None, progress_callback=None):
    """Export metadata to CSV using the unified format definition."""
    print(f"[csv_exporter] Exporting CSV to: {output_path}")
    
    if not output_path:
        print(f"[csv_exporter] Error: No output path specified")
        return False
    
    try:
        db = ImageTeaDB()
        files = db.get_all_files()
        shutterstock_map, adobe_map = db.get_category_maps()
        category_mapping = db.get_category_mapping()
        config = load_csv_config()
        
        if not files:
            print(f"[csv_exporter] No files found to export")
            return False
        
        rows = []
        
        # Add header if configured
        if config.get("include_headers", True):
            header = "file_name,title,description,keywords,ss_category,as_code"
            rows.append(header)
        
        # Format each file according to the unified definition
        for file in files:
            row = format_unified_row(file, shutterstock_map, category_mapping)
            rows.append(row)
            if progress_callback:
                progress_callback()
        
        # Generate filename and write CSV
        csv_filename = generate_export_filename(output_path)
        csv_path = os.path.join(output_path, csv_filename)
        
        encoding = config.get("encoding", "utf-8")
        with open(csv_path, "w", encoding=encoding, newline='') as f:
            for row in rows:
                f.write(row + "\n")
        
        print(f"[csv_exporter] CSV exported successfully to: {csv_path}")
        return True
        
    except Exception as e:
        print(f"[csv_exporter] Error exporting CSV: {e}")
        return False
