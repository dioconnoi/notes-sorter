from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EisenhowerQuadrant(str, Enum):
    DO_NOW = "do_now"            # urgent + important
    SCHEDULE = "schedule"        # important, not urgent
    DELEGATE = "delegate"        # urgent, not important
    ELIMINATE = "eliminate"      # neither


class GTDType(str, Enum):
    NEXT_ACTION = "next_action"
    PROJECT = "project"
    WAITING_FOR = "waiting_for"
    SOMEDAY_MAYBE = "someday_maybe"
    REFERENCE = "reference"      # not actionable, pure information


class ExtractedTask(BaseModel):
    title: str
    gtd_type: GTDType
    quadrant: EisenhowerQuadrant | None = Field(
        default=None, description="Only set when gtd_type is next_action or project"
    )
    due_date: str | None = Field(default=None, description="ISO 8601 date, if mentioned or inferable")
    context: str | None = Field(default=None, description="GTD context, e.g. '@calls', '@computer'")
    project_hint: str | None = Field(
        default=None, description="Name of the project this task belongs to, if any"
    )
    waiting_on: str | None = Field(default=None, description="Who/what this is blocked on, if gtd_type is waiting_for")


class CategorizationResult(BaseModel):
    """What the LLM itself produces — no fields we already know on our side."""

    title: str
    summary: str
    category: str = Field(description="Freeform, LLM-chosen category — not from a fixed list")
    tags: list[str] = Field(default_factory=list)
    tasks: list[ExtractedTask] = Field(default_factory=list)
    is_reference_only: bool = Field(
        default=False, description="True if the note has no actionable tasks at all"
    )


class CategorizedNote(CategorizationResult):
    """The full structured result of running one raw note through the categorizer,
    including the metadata we attach ourselves rather than asking the LLM for it."""

    source: str = Field(description="Where the note came from, e.g. 'telegram', 'google_keep'")
    raw_text: str
