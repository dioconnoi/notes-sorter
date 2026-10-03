from __future__ import annotations

import asyncio

import gkeepapi

from notes_sorter.config import Settings
from notes_sorter.ingestion.base import NoteSource, RawNote
from notes_sorter.ingestion.state import SeenIdStore


class GoogleKeepSource(NoteSource):
    """Uses the unofficial gkeepapi library — there is no public Google Keep API.
    See docs/BLINDSPOTS.md: this can break whenever Google changes Keep's internal
    endpoints, and requires a master token (not a normal password) obtained via a
    separate one-time device-login flow."""

    source_name = "google_keep"

    def __init__(self, settings: Settings):
        if not (settings.google_keep_email and settings.google_keep_master_token):
            raise RuntimeError("GOOGLE_KEEP_EMAIL and GOOGLE_KEEP_MASTER_TOKEN must be set")
        self._email = settings.google_keep_email
        self._token = settings.google_keep_master_token
        self._state = SeenIdStore(self.source_name)
        self._keep = gkeepapi.Keep()

    async def fetch_new_notes(self) -> list[RawNote]:
        # gkeepapi is synchronous; keep it off the event loop.
        return await asyncio.to_thread(self._fetch_sync)

    def _fetch_sync(self) -> list[RawNote]:
        self._keep.resume(self._email, self._token)
        self._keep.sync()

        new_notes = []
        for note in self._keep.all():
            if note.trashed or note.archived:
                continue
            if not self._state.is_new(note.id):
                continue
            text = f"{note.title}\n{note.text}".strip() if note.title else note.text
            if not text.strip():
                continue
            new_notes.append(RawNote(external_id=note.id, text=text, source=self.source_name))
            self._state.mark_seen(note.id)
        return new_notes
