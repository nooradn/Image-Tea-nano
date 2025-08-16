import os
import json
import base64
from openai import OpenAI
from config import BASE_PATH

def load_openai_prompt_vars():
    prompt_path = os.path.join(BASE_PATH, "configs", "ai_prompt.json")
    with open(prompt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    prompt_data = data["prompt"]
    return (
        prompt_data["ai_prompt"],
        prompt_data["negative_prompt"],
        prompt_data["system_prompt"],
        data["min_title_length"],
        data["max_title_length"],
        data["max_description_length"],
        data["required_tag_count"]
    )

def format_openai_prompt(ai_prompt, negative_prompt, system_prompt, min_title_length, max_title_length, max_description_length, required_tag_count):
    prompt = ai_prompt
    prompt = prompt.replace("_MIN_LEN_", str(min_title_length))
    prompt = prompt.replace("_MAX_LEN_", str(max_title_length))
    prompt = prompt.replace("_MAX_DESC_LEN_", str(max_description_length))
    prompt = prompt.replace("_TAGS_COUNT_", str(required_tag_count))
    full_prompt = f"{prompt}\n\nNegative Prompt:\n{negative_prompt}\n\n{system_prompt}"
    return full_prompt

def generate_metadata_openai(api_key, model, image_path, prompt=None):
    try:
        ext = os.path.splitext(image_path)[1].lower()
        is_video = ext in ['.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp']
        if is_video:
            error_message = (
                "OpenAI Vision API belum mendukung input video secara langsung. "
                "Silakan gunakan gambar atau pilih layanan Gemini untuk video. "
                "Jika di masa depan OpenAI sudah mendukung video, fitur ini akan segera ditambahkan."
            )
            return '', '', '', error_message
        client = OpenAI(api_key=api_key)
        if not prompt:
            ai_prompt, negative_prompt, system_prompt, min_title_length, max_title_length, max_description_length, required_tag_count = load_openai_prompt_vars()
            prompt = format_openai_prompt(ai_prompt, negative_prompt, system_prompt, min_title_length, max_title_length, max_description_length, required_tag_count)
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{image_b64}"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_data_url}
                ]
            }
        ]
        response = client.responses.create(
            model=model,
            input=messages
        )
        print("[OpenAI RAW JSON Result]")
        print(response)
        text = getattr(response, "output_text", None)
        if not text:
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
            print(f"[OpenAI JSON PARSE ERROR] {e}")
            title = description = tags = ''
        return title, description, tags, ''
    except Exception as e:
        error_message = f"[OpenAI ERROR] {e}"
        return '', '', '', error_message