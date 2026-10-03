from __future__ import annotations

from datetime import UTC, datetime

from notes_sorter.categorize.models import CategorizationResult, CategorizedNote
from notes_sorter.llm.base import LLMProvider

SYSTEM_PROMPT = """You are a meticulous personal-organization assistant. You read a raw \
note (which may be messy, fragmentary, or OCR'd from handwriting) and turn it into \
structured data.

Rules:
- Pick `category` freely based on the note's actual content — do not force it into a \
fixed list. Reuse an existing category name when the note clearly belongs with it; \
otherwise coin a short, sensible new one (2-3 words, Title Case).
- Extract every actionable item as a separate entry in `tasks`. A note can have zero, \
one, or many tasks.
- For each task, set `gtd_type`:
  - next_action: a single concrete, doable step
  - project: requires multiple steps to complete
  - waiting_for: blocked on someone/something else
  - someday_maybe: not actionable now, a future idea
  - reference: not actually a task, just information worth keeping
- For next_action and project tasks only, set `quadrant` using the Eisenhower Matrix:
  - do_now: urgent AND important
  - schedule: important, NOT urgent
  - delegate: urgent, NOT important (someone else could/should do it)
  - eliminate: neither urgent nor important — question whether it's worth doing
  Judge urgency from explicit deadlines/time pressure in the text; judge importance \
from stated consequences, goals, or relationships affected. Do not default everything \
to do_now — be discriminating.
- Infer `due_date` only if the text states or clearly implies one (e.g. "by Friday" \
relative to today's date). Leave null otherwise — never invent a date.
- Set `is_reference_only=true` only when there are no actionable tasks at all.
"""


async def categorize_note(
    provider: LLMProvider, raw_text: str, source: str, existing_categories: list[str] | None = None
) -> CategorizedNote:
    today = datetime.now(tz=UTC).date().isoformat()
    categories_hint = (
        f"\nExisting categories already in use (prefer reusing one of these when it fits): "
        f"{', '.join(existing_categories)}"
        if existing_categories
        else ""
    )
    user_prompt = (
        f"Today's date: {today}\n"
        f"Note source: {source}{categories_hint}\n\n"
        f"Raw note:\n---\n{raw_text}\n---"
    )
    result = await provider.structured_complete(SYSTEM_PROMPT, user_prompt, CategorizationResult)
    return CategorizedNote(**result.model_dump(), source=source, raw_text=raw_text)
