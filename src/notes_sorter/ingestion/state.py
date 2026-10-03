from __future__ import annotations

import json
from pathlib import Path

STATE_DIR = Path(".keep_state")


class SeenIdStore:
    """Tiny local JSON set, one file per source, so re-syncing never duplicates notes."""

    def __init__(self, source_name: str):
        STATE_DIR.mkdir(exist_ok=True)
        self._path = STATE_DIR / f"{source_name}.json"
        self._seen: set[str] = set(json.loads(self._path.read_text())) if self._path.exists() else set()

    def is_new(self, external_id: str) -> bool:
        return external_id not in self._seen

    def mark_seen(self, external_id: str) -> None:
        self._seen.add(external_id)
        self._path.write_text(json.dumps(sorted(self._seen)))
