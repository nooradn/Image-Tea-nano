import time
import os
import json
import google.genai as genai
from google.genai import types

def generate_metadata_gemini(api_key, image_path, prompt=None):
	try:
		client = genai.Client(api_key=api_key)
		ext = os.path.splitext(image_path)[1].lower()
		is_video = ext in ['.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp', '.3gpp']
		if not prompt:
			prompt = (
				"Create high-quality image or video metadata following these guidelines:\n\n"
				"1. Title/Description Requirements:\n"
				"- Length: Min 8 - Max Length must be exactly 80 characters, no more than that since its CRITICAL\n"
				"- Write as a natural, descriptive sentence/phrase (not keyword list)\n"
				"- Cover Who, What, When, Where, Why aspects where relevant\n"
				"- Capture mood, emotion, and visual impact\n"
				"- Must be unique and detailed\n"
				"- Include visual style/technique if notable\n"
				"- Be factual and objective\n\n"
				"2. Description Requirements:\n"
				"- Provide a detailed description of the image or video, different from the title\n"
				"- Use a full sentence or two, not just keywords\n"
				"- Must be unique and informative\n\n"
				"3. Keywords Requirements:\n"
				"- You must provide exactly 40 keywords and not less since its CRITICAL\n"
				"- Keywords must be precise and directly relevant\n"
				"- Include both literal and conceptual terms\n"
				"- Cover key visual elements, themes, emotions, techniques\n"
				"- Avoid overly generic or irrelevant terms\n"
				"- Use industry-standard terminology\n"
				"- Separate keywords with commas\n\n"
				"4. General Guidelines:\n"
				"- Use only English language\n"
				"- Be respectful and accurate with identities\n"
				"- No personally identifiable information\n"
				"- No special characters except commas between keywords\n"
				"- Focus on commercial value and searchability\n\n"
				"5. Strict Don'ts:\n"
				"- No brand names, trademarks, or company names\n"
				"- No celebrity names or personal names\n"
				"- No specific event references or newsworthy content\n"
				"- No copyrighted elements or protected designs\n"
				"- No editorial content or journalistic references\n"
				"- No offensive, controversial, or sensitive terms\n"
				"- No location-specific landmarks unless generic\n"
				"- No date-specific references or temporal events\n"
				"- No product names or model numbers\n"
				"- No camera/tech specifications in metadata\n\n"
				"RESPONSE FORMAT (Strict JSON with ALL fields required):\n"
				"{\n"
				'  "title": "Your descriptive title here",\n'
				'  "description": "A detailed description of the image or video.",\n'
				'  "tags": ["tag1", "tag2", "tag3"]\n'
				"}\n"
				"\nVALIDATION RULES:\n"
				"1. Use DOUBLE quotes for all strings\n"
				"2. All fields (title, description, tags) are required\n"
				"3. Response must be valid JSON\n"
			)
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
			model='gemini-2.5-flash',
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
