import time
import os
import json
import google.genai as genai
from google.genai import types
from config import BASE_PATH
from database.db_operation import ImageTeaDB

def load_gemini_prompt_vars():
    prompt_path = os.path.join(BASE_PATH, "configs", "ai_prompt.json")
    with open(prompt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["ai_prompt"], data["min_title_length"], data["max_title_length"], data["required_tag_count"]

def format_gemini_prompt(base_prompt, min_title_length, max_title_length, required_tag_count):
    prompt = base_prompt
    prompt = prompt.replace("_MIN_LEN_", str(min_title_length))
    prompt = prompt.replace("_MAX_LEN_", str(max_title_length))
    prompt = prompt.replace("_TAGS_COUNT_", str(required_tag_count))
    return prompt

def generate_metadata_gemini(api_key, image_path, prompt=None):
    try:
        db = ImageTeaDB()
        api_key_info = db.get_api_key('gemini')
        if not api_key_info or api_key_info.get('api_key') != api_key or not api_key_info.get('model'):
            raise RuntimeError("No model found for this Gemini API key in the database.")
        model = api_key_info.get('model')
        client = genai.Client(api_key=api_key)
        ext = os.path.splitext(image_path)[1].lower()
        is_video = ext in ['.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp']
        if not prompt:
            base_prompt, min_title_length, max_title_length, required_tag_count = load_gemini_prompt_vars()
            prompt = format_gemini_prompt(base_prompt, min_title_length, max_title_length, required_tag_count)
        if is_video:
            myfile = client.files.upload(file=image_path)
            file_id = myfile.name if hasattr(myfile, 'name') else getattr(myfile, 'id', None)
            status = None
            for _ in range(20):
                fileinfo = client.files.get(name=file_id)
                status = getattr(fileinfo, 'state', None) or getattr(fileinfo, 'status', None)
                if status == 'ACTIVE':
                    break
                time.sleep(0.5)
            if status != 'ACTIVE':
                print(f"[Gemini ERROR] File {file_id} not ACTIVE after upload, status: {status}")
                return '', '', ''
            contents = [myfile, prompt]
        else:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            contents = [types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'), prompt]
        response = client.models.generate_content(
            model=model,
            contents=contents
        )
        print("[Gemini RAW JSON Result]")
        print(response)
        text = None
        if hasattr(response, 'candidates') and response.candidates:
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                text = str(response)
        elif hasattr(response, 'text'):
            text = response.text
        elif isinstance(response, dict) and 'text' in response:
            text = response['text']
        else:
            text = str(response)
        try:
            if text.strip().startswith('```'):
                text = text.strip().lstrip('`').lstrip('json').strip()
                if text.endswith('```'):
                    text = text[:text.rfind('```')].strip()
            meta = json.loads(text)
            title = meta.get('title', '')
            description = meta.get('description', '')
            tags = ', '.join(meta.get('tags', [])) if isinstance(meta.get('tags'), list) else str(meta.get('tags', ''))
        except Exception as e:
            print(f"[Gemini JSON PARSE ERROR] {e}")
            title = description = tags = ''
        return title, description, tags
    except Exception as e:
        print(f"[Gemini ERROR] {e}")
        return '', '', ''