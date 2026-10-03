import pytest

from notes_sorter.categorize.categorizer import categorize_note
from notes_sorter.categorize.models import CategorizationResult, ExtractedTask, GTDType
from notes_sorter.llm.base import LLMProvider


class FakeProvider(LLMProvider):
    def __init__(self, result: CategorizationResult):
        self._result = result
        self.last_system = None
        self.last_user = None

    async def structured_complete(self, system, user, schema):
        self.last_system = system
        self.last_user = user
        assert schema is CategorizationResult
        return self._result

    async def vision_ocr(self, image_bytes, mime_type="image/jpeg"):
        raise NotImplementedError


@pytest.mark.asyncio
async def test_categorize_note_attaches_source_and_raw_text():
    fake_result = CategorizationResult(
        title="Buy groceries",
        summary="Need milk and eggs",
        category="Household",
        tags=["shopping"],
        tasks=[ExtractedTask(title="Buy milk and eggs", gtd_type=GTDType.NEXT_ACTION)],
        is_reference_only=False,
    )
    provider = FakeProvider(fake_result)

    note = await categorize_note(provider, raw_text="milk, eggs", source="telegram")

    assert note.title == "Buy groceries"
    assert note.category == "Household"
    assert note.source == "telegram"
    assert note.raw_text == "milk, eggs"
    assert len(note.tasks) == 1
    assert "milk, eggs" in provider.last_user


@pytest.mark.asyncio
async def test_categorize_note_passes_existing_categories_hint():
    fake_result = CategorizationResult(
        title="t", summary="s", category="Finance", tags=[], tasks=[], is_reference_only=True
    )
    provider = FakeProvider(fake_result)

    await categorize_note(provider, raw_text="x", source="telegram", existing_categories=["Finance", "Health"])

    assert "Finance" in provider.last_user
    assert "Health" in provider.last_user
