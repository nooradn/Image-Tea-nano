import time
import os
import json
import google.genai as genai
from google.genai import types
from config import BASE_PATH
from helpers.ai_helper.ai_variation_helper import generate_timestamp, generate_token

_generation_times_gemini = []

def track_gemini_generation_time(duration_ms):
    _generation_times_gemini.append(duration_ms)
    if len(_generation_times_gemini) > 1000:
        _generation_times_gemini.pop(0)
    gen_time = duration_ms
    avg_time = int(sum(_generation_times_gemini) / len(_generation_times_gemini)) if _generation_times_gemini else 0
    longest_time = max(_generation_times_gemini) if _generation_times_gemini else 0
    last_time = _generation_times_gemini[-1] if _generation_times_gemini else 0
    return gen_time, avg_time, longest_time, last_time

def load_gemini_prompt_vars():
    prompt_path = os.path.join(BASE_PATH, "configs", "ai_prompt.json")
    with open(prompt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    prompt_data = data["prompt"]
    return (
        prompt_data["ai_prompt"],
        prompt_data["negative_prompt"],
        prompt_data["system_prompt"],
        prompt_data["custom_prompt"],
        data["min_title_length"],
        data["max_title_length"],
        data["max_description_length"],
        data["required_tag_count"]
    )

def format_gemini_prompt(ai_prompt, negative_prompt, system_prompt, custom_prompt, min_title_length, max_title_length, max_description_length, required_tag_count):
    prompt = ai_prompt
    prompt = prompt.replace("_MIN_LEN_", str(min_title_length))
    prompt = prompt.replace("_MAX_LEN_", str(max_title_length))
    prompt = prompt.replace("_MAX_DESC_LEN_", str(max_description_length))
    prompt = prompt.replace("_TAGS_COUNT_", str(required_tag_count))
    prompt = prompt.replace("_TIMESTAMP_", generate_timestamp())
    prompt = prompt.replace("_TOKEN_", generate_token())
    if custom_prompt and custom_prompt.strip():
        prompt = f"{prompt}\n\nMANDATORY: {custom_prompt.strip()}\n"
    full_prompt = f"{prompt}\n\nNegative Prompt:\n{negative_prompt}\n\n{system_prompt}"
    print("[Gemini FULL PROMPT]")
    print(full_prompt)
    return full_prompt

def generate_metadata_gemini(api_key, model, image_path, prompt=None):
    start_time = time.perf_counter()
    try:
        client = genai.Client(api_key=api_key)
        ext = os.path.splitext(image_path)[1].lower()
        is_video = ext in ['.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp']
        if not prompt:
            ai_prompt, negative_prompt, system_prompt, custom_prompt, min_title_length, max_title_length, max_description_length, required_tag_count = load_gemini_prompt_vars()
            prompt = format_gemini_prompt(ai_prompt, negative_prompt, system_prompt, custom_prompt, min_title_length, max_title_length, max_description_length, required_tag_count)
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
                return '', '', '', 0, 0, 0
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
        token_input = 0
        token_output = 0
        token_total = 0
        usage = getattr(response, "usage_metadata", None)
        if usage:
            token_input = getattr(usage, "prompt_token_count", 0)
            token_output = getattr(usage, "candidates_token_count", 0)
            token_total = getattr(usage, "total_token_count", 0)
        text = None
        if hasattr(response, "candidates") and response.candidates:
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                text = str(response)
        elif hasattr(response, "text"):
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
        return title, description, tags, token_input, token_output, token_total
    except Exception as e:
        print(f"[Gemini ERROR] {e}")
        return '', '', '', 0, 0, 0
    finally:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        track_gemini_generation_time(duration_ms)