from __future__ import annotations

from notion_client import AsyncClient

from notes_sorter.categorize.models import EisenhowerQuadrant, GTDType

QUADRANT_OPTIONS = [{"name": q.value} for q in EisenhowerQuadrant]
GTD_TYPE_OPTIONS = [{"name": t.value} for t in GTDType]
TASK_STATUS_OPTIONS = [{"name": s} for s in ("Not Started", "In Progress", "Done", "Someday", "Dropped")]
PROJECT_STATUS_OPTIONS = [{"name": s} for s in ("Active", "On Hold", "Completed", "Archived")]


async def provision_workspace(client: AsyncClient, parent_page_id: str) -> dict[str, str]:
    """Create the three linked databases from scratch. Idempotent is NOT guaranteed —
    call this once and save the returned IDs into .env; re-running creates duplicates."""

    projects_db = await client.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Projects"}}],
        properties={
            "Name": {"title": {}},
            "Status": {"select": {"options": PROJECT_STATUS_OPTIONS}},
            "Progress": {"number": {"format": "percent"}},
            "Category": {"rich_text": {}},
        },
    )
    projects_db_id = projects_db["id"]

    tasks_db = await client.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Tasks"}}],
        properties={
            "Name": {"title": {}},
            "Status": {"select": {"options": TASK_STATUS_OPTIONS}},
            "Done": {"checkbox": {}},
            "Quadrant": {"select": {"options": QUADRANT_OPTIONS}},
            "GTD Type": {"select": {"options": GTD_TYPE_OPTIONS}},
            "Due Date": {"date": {}},
            "Context": {"rich_text": {}},
            "Waiting On": {"rich_text": {}},
            "Tags": {"multi_select": {}},
            "Project": {"relation": {"database_id": projects_db_id, "single_property": {}}},
            "Source Note": {"rich_text": {}},
        },
    )

    notes_db = await client.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Notes"}}],
        properties={
            "Name": {"title": {}},
            "Category": {"rich_text": {}},
            "Tags": {"multi_select": {}},
            "Source": {"select": {"options": [
                {"name": "telegram"}, {"name": "google_keep"},
                {"name": "google_docs"}, {"name": "hardcopy_photo"},
            ]}},
            "Summary": {"rich_text": {}},
            "Raw Text": {"rich_text": {}},
            "Related Tasks": {"relation": {"database_id": tasks_db["id"], "single_property": {}}},
        },
    )

    return {
        "NOTION_PROJECTS_DB_ID": projects_db_id,
        "NOTION_TASKS_DB_ID": tasks_db["id"],
        "NOTION_NOTES_DB_ID": notes_db["id"],
    }
