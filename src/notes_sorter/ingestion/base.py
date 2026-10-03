from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RawNote:
    external_id: str   # stable id in the source system, used for dedup
    text: str
    source: str


class NoteSource(ABC):
    """A pluggable connector that can list notes which haven't been ingested yet.
    Implementations are responsible for their own "seen" bookkeeping (e.g. a local
    state file of already-synced external_ids) — see ingestion/state.py."""

    source_name: str

    @abstractmethod
    async def fetch_new_notes(self) -> list[RawNote]:
        """Return only notes not previously returned by this method."""
