from __future__ import annotations

import asyncio
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from notes_sorter.config import Settings
from notes_sorter.ingestion.base import NoteSource, RawNote
from notes_sorter.ingestion.state import SeenIdStore

SCOPES = ["https://www.googleapis.com/auth/documents.readonly", "https://www.googleapis.com/auth/drive.readonly"]
TOKEN_PATH = Path("google_token.json")


def _get_credentials(credentials_file: str) -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # One-time interactive consent; run `notes-sorter-setup` to do this ahead of time.
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


class GoogleDocsSource(NoteSource):
    source_name = "google_docs"

    def __init__(self, settings: Settings):
        self._settings = settings
        self._state = SeenIdStore(self.source_name)

    async def fetch_new_notes(self) -> list[RawNote]:
        return await asyncio.to_thread(self._fetch_sync)

    def _fetch_sync(self) -> list[RawNote]:
        creds = _get_credentials(self._settings.google_docs_credentials_file)
        drive = build("drive", "v3", credentials=creds)
        docs = build("docs", "v1", credentials=creds)

        query = "mimeType='application/vnd.google-apps.document' and trashed=false"
        if self._settings.google_docs_folder_id:
            query += f" and '{self._settings.google_docs_folder_id}' in parents"

        files = drive.files().list(q=query, fields="files(id, name, modifiedTime)").execute().get("files", [])

        new_notes = []
        for f in files:
            dedup_key = f"{f['id']}:{f['modifiedTime']}"  # re-ingest if the doc changed
            if not self._state.is_new(dedup_key):
                continue
            doc = docs.documents().get(documentId=f["id"]).execute()
            text = _extract_text(doc)
            if not text.strip():
                continue
            new_notes.append(RawNote(external_id=f["id"], text=f"{f['name']}\n{text}", source=self.source_name))
            self._state.mark_seen(dedup_key)
        return new_notes


def _extract_text(doc: dict) -> str:
    parts = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for run in paragraph.get("elements", []):
            text_run = run.get("textRun")
            if text_run:
                parts.append(text_run.get("content", ""))
    return "".join(parts)
