from __future__ import annotations

from notion_client import AsyncClient

from notes_sorter.categorize.models import CategorizedNote, ExtractedTask
from notes_sorter.config import Settings

_STATUS_FOR_GTD = {
    "someday_maybe": "Someday",
    "reference": "Not Started",
}


def _rich_text(content: str) -> list[dict]:
    return [{"type": "text", "text": {"content": content[:2000]}}]


async def _find_or_create_project(client: AsyncClient, projects_db_id: str, name: str) -> str:
    existing = await client.databases.query(
        database_id=projects_db_id,
        filter={"property": "Name", "title": {"equals": name}},
        page_size=1,
    )
    if existing["results"]:
        return existing["results"][0]["id"]

    page = await client.pages.create(
        parent={"database_id": projects_db_id},
        properties={
            "Name": {"title": [{"type": "text", "text": {"content": name}}]},
            "Status": {"select": {"name": "Active"}},
            "Progress": {"number": 0},
        },
    )
    return page["id"]


async def _create_task_page(
    client: AsyncClient, tasks_db_id: str, task: ExtractedTask, note_title: str, project_page_id: str | None
) -> str:
    properties: dict = {
        "Name": {"title": [{"type": "text", "text": {"content": task.title}}]},
        "Status": {"select": {"name": _STATUS_FOR_GTD.get(task.gtd_type.value, "Not Started")}},
        "Done": {"checkbox": False},
        "GTD Type": {"select": {"name": task.gtd_type.value}},
        "Source Note": {"rich_text": _rich_text(note_title)},
    }
    if task.quadrant is not None:
        properties["Quadrant"] = {"select": {"name": task.quadrant.value}}
    if task.due_date:
        properties["Due Date"] = {"date": {"start": task.due_date}}
    if task.context:
        properties["Context"] = {"rich_text": _rich_text(task.context)}
    if task.waiting_on:
        properties["Waiting On"] = {"rich_text": _rich_text(task.waiting_on)}
    if project_page_id:
        properties["Project"] = {"relation": [{"id": project_page_id}]}

    page = await client.pages.create(parent={"database_id": tasks_db_id}, properties=properties)
    return page["id"]


async def sync_note(client: AsyncClient, settings: Settings, note: CategorizedNote) -> str:
    """Write a categorized note and its tasks to Notion. Returns the created Notes page id."""
    task_page_ids: list[str] = []
    project_cache: dict[str, str] = {}

    for task in note.tasks:
        project_page_id = None
        if task.project_hint:
            if task.project_hint not in project_cache:
                project_cache[task.project_hint] = await _find_or_create_project(
                    client, settings.notion_projects_db_id, task.project_hint
                )
            project_page_id = project_cache[task.project_hint]

        task_page_ids.append(
            await _create_task_page(client, settings.notion_tasks_db_id, task, note.title, project_page_id)
        )

    note_page = await client.pages.create(
        parent={"database_id": settings.notion_notes_db_id},
        properties={
            "Name": {"title": [{"type": "text", "text": {"content": note.title}}]},
            "Category": {"rich_text": _rich_text(note.category)},
            "Tags": {"multi_select": [{"name": t[:100]} for t in note.tags]},
            "Source": {"select": {"name": note.source}},
            "Summary": {"rich_text": _rich_text(note.summary)},
            "Raw Text": {"rich_text": _rich_text(note.raw_text)},
            **({"Related Tasks": {"relation": [{"id": pid} for pid in task_page_ids]}} if task_page_ids else {}),
        },
    )
    return note_page["id"]
