from __future__ import annotations

import base64
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from notes_sorter.config import Settings
from notes_sorter.llm.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    supports_notion_mcp = False

    def __init__(self, settings: Settings):
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def structured_complete(self, system: str, user: str, schema: type[T]) -> T:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                },
            },
        )
        return schema.model_validate_json(response.choices[0].message.content)

    async def vision_ocr(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Transcribe every word of handwritten or printed text in this "
                                "photo exactly as written. Preserve line breaks and bullet/checkbox "
                                "markers. Output only the transcription, no commentary."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()
