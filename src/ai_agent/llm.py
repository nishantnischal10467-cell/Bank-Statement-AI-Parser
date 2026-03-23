from __future__ import annotations

import base64
import os
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import get_settings


def _client() -> OpenAI:
    settings = get_settings()
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def get_openai_client() -> OpenAI:
    """Get OpenAI client for agent usage."""
    return _client()


@retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def vision_structured_extract_png(page_png: bytes) -> list[dict[str, Any]]:
    settings = get_settings()
    b64 = base64.b64encode(page_png).decode()
    client = _client()
    resp = client.chat.completions.create(
        model=settings.model_vision,
        messages=[
            {"role": "system", "content": "Extract bank transactions as JSON array."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "JSON array: date (DD-MM-YYYY), description, amount, balance. Credit=positive, debit=negative amount."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    text = (resp.choices[0].message.content or "{}").strip()
    try:
        import json
        obj = json.loads(text)
        if isinstance(obj, dict) and "transactions" in obj and isinstance(obj["transactions"], list):
            return obj["transactions"]
        if isinstance(obj, list):
            return obj
        return []
    except Exception:
        return []

