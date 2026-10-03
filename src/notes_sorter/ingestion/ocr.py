from __future__ import annotations

from notes_sorter.llm.base import LLMProvider

# Deliberately not a classic OCR engine (Tesseract etc.): vision-LLM transcription
# handles messy handwriting far better in practice. See docs/BLINDSPOTS.md for the
# accuracy and cost trade-offs of this choice.


async def transcribe_photo(provider: LLMProvider, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    return await provider.vision_ocr(image_bytes, mime_type)
