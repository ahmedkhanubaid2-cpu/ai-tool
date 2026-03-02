import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

SYSTEM_PROMPT = """
You are a children's picture-book scene generator.

Given a book title and page text, infer:
- setting
- time of day
- mood
- characters present (from text only)
- character actions and emotions
- props
- composition notes
- continuity notes

Rules:
- Do NOT invent plot beyond the page text
- Maintain continuity with previous pages if provided
- Output MUST be valid JSON only (no markdown, no extra text)
"""

def generate_scene(book_title: str, page: dict, prev_summary: str = "") -> dict:
    user_payload = {
        "book_title": book_title,
        "previous_page_summary": prev_summary,
        "page": page,
        "output_schema": {
            "page_number": "int",
            "page_text": "string",
            "setting": "string",
            "time_of_day": "string",
            "mood": "string",
            "characters": [
                {"name": "string", "actions": ["string"], "emotions": ["string"]}
            ],
            "props": ["string"],
            "composition_notes": "string",
            "continuity_notes": "string"
        }
    }

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload)}
        ],
        temperature=0.4,
        max_tokens=2000
    )

    content = resp.choices[0].message.content.strip()

    # Parse JSON safely
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # If model returns extra text, try to extract JSON block
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start:end+1])
        raise
