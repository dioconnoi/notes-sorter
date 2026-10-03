from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """LLM-agnostic interface. Every backend must support structured output and vision OCR."""

    supports_notion_mcp: bool = False

    @abstractmethod
    async def structured_complete(self, system: str, user: str, schema: type[T]) -> T:
        """Run a prompt and parse the response into `schema`, retrying on invalid JSON."""

    @abstractmethod
    async def vision_ocr(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """Transcribe a photographed note into plain text using the model's vision capability."""
