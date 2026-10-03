from __future__ import annotations

from notion_client import AsyncClient

from notes_sorter.config import Settings


def build_notion_client(settings: Settings) -> AsyncClient:
    if not settings.notion_api_key:
        raise RuntimeError(
            "NOTION_API_KEY is required even when NOTION_ACCESS_MODE=mcp: schema "
            "provisioning and reliable sync always go through the REST API. MCP mode "
            "only adds an extra conversational path for Claude users — see "
            "docs/ARCHITECTURE.md#notion-access."
        )
    return AsyncClient(auth=settings.notion_api_key)
