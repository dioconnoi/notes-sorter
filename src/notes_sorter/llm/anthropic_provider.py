from __future__ import annotations

from typing import TypeVar

import anthropic
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from notes_sorter.config import Settings
from notes_sorter.llm.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(LLMProvider):
    """Claude backend. Also the only provider that can talk to Notion over MCP directly,
    via the Messages API's remote-MCP connector (beta) — see notion/client.py."""

    supports_notion_mcp = True

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def structured_complete(self, system: str, user: str, schema: type[T]) -> T:
        tool_name = f"emit_{schema.__name__.lower()}"
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
            tools=[
                {
                    "name": tool_name,
                    "description": f"Return the result as {schema.__name__}.",
                    "input_schema": schema.model_json_schema(),
                }
            ],
            tool_choice={"type": "tool", "name": tool_name},
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return schema.model_validate(block.input)
        raise ValueError("Claude did not return the expected tool call")

    async def vision_ocr(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        import base64

        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": mime_type, "data": b64},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Transcribe every word of handwritten or printed text in this "
                                "photo exactly as written. Preserve line breaks and bullet/checkbox "
                                "markers. Output only the transcription, no commentary."
                            ),
                        },
                    ],
                }
            ],
        )
        return "".join(b.text for b in response.content if b.type == "text").strip()

    async def notion_mcp_complete(self, system: str, user: str) -> str:
        """Let Claude act on Notion directly through its hosted remote-MCP server.
        Used by notion/client.py when NOTION_ACCESS_MODE=mcp."""
        response = await self._client.beta.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
            mcp_servers=[
                {
                    "type": "url",
                    "url": self._settings.notion_mcp_url,
                    "name": "notion",
                    "authorization_token": self._settings.notion_mcp_token,
                }
            ],
            betas=["mcp-client-2025-04-04"],
        )
        return "".join(
            b.text for b in response.content if getattr(b, "type", None) == "text"
        ).strip()
