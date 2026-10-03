from __future__ import annotations

import base64
from typing import TypeVar

import httpx
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from notes_sorter.config import Settings
from notes_sorter.llm.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OllamaProvider(LLMProvider):
    """Local backend via Ollama. No Notion-MCP support — notion/client.py falls back
    to the direct REST API for this provider. Vision OCR requires a vision-capable
    local model (e.g. llama3.2-vision, llava); accuracy on handwriting will be
    noticeably weaker than the hosted providers — see docs/BLINDSPOTS.md."""

    supports_notion_mcp = False

    def __init__(self, settings: Settings):
        self._base_url = settings.ollama_host.rstrip("/")
        self._model = settings.ollama_model
        self._client = httpx.AsyncClient(timeout=120)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def structured_complete(self, system: str, user: str, schema: type[T]) -> T:
        response = await self._client.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "stream": False,
                "format": schema.model_json_schema(),
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        return schema.model_validate_json(content)

    async def vision_ocr(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        response = await self._client.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Transcribe every word of handwritten or printed text in this "
                            "photo exactly as written. Preserve line breaks and bullet/checkbox "
                            "markers. Output only the transcription, no commentary."
                        ),
                        "images": [b64],
                    }
                ],
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
