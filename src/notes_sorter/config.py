from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: Literal["anthropic", "openai", "ollama"] = "anthropic"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    notion_api_key: str | None = None
    notion_parent_page_id: str | None = None
    notion_notes_db_id: str | None = None
    notion_tasks_db_id: str | None = None
    notion_projects_db_id: str | None = None
    notion_access_mode: Literal["mcp", "api"] = "api"
    notion_mcp_url: str = "https://mcp.notion.com/mcp"
    notion_mcp_token: str | None = None

    telegram_bot_token: str | None = None
    telegram_allowed_user_ids: str = ""

    google_keep_email: str | None = None
    google_keep_master_token: str | None = None
    google_docs_credentials_file: str = "credentials.json"
    google_docs_folder_id: str | None = None

    digest_cron: str = "0 8 * * *"
    resync_interval_minutes: int = 60
    timezone: str = "UTC"

    @property
    def allowed_user_ids(self) -> set[int]:
        raw = self.telegram_allowed_user_ids.strip()
        if not raw:
            return set()
        return {int(x) for x in raw.split(",") if x.strip()}

    def notion_fully_provisioned(self) -> bool:
        return bool(self.notion_notes_db_id and self.notion_tasks_db_id and self.notion_projects_db_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()
