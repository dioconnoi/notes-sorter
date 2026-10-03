from __future__ import annotations

from notion_client import AsyncClient

from notes_sorter.config import Settings


async def recompute_all_project_progress(client: AsyncClient, settings: Settings) -> dict[str, float]:
    """Walk every project, compute % of its linked tasks marked Done, and push the
    number back onto the Project page's `Progress` property (formatted as percent,
    so Notion's "Show as bar" display option renders it as a progress bar).

    Notion's own rollups can't safely do this for us here: we want Done/total across
    *active* tasks (Someday/Dropped tasks shouldn't count against progress), which is
    easier to express in code than in a single rollup formula. Returns {project_id: pct}.
    """
    results: dict[str, float] = {}
    cursor: str | None = None
    while True:
        page = await client.databases.query(
            database_id=settings.notion_projects_db_id,
            start_cursor=cursor,
        )
        for project in page["results"]:
            pct = await _project_progress(client, settings.notion_tasks_db_id, project["id"])
            results[project["id"]] = pct
            await client.pages.update(
                page_id=project["id"],
                properties={"Progress": {"number": pct}},
            )
        if not page.get("has_more"):
            break
        cursor = page.get("next_cursor")
    return results


async def _project_progress(client: AsyncClient, tasks_db_id: str, project_page_id: str) -> float:
    tasks = []
    cursor: str | None = None
    while True:
        page = await client.databases.query(
            database_id=tasks_db_id,
            filter={"property": "Project", "relation": {"contains": project_page_id}},
            start_cursor=cursor,
        )
        tasks.extend(page["results"])
        if not page.get("has_more"):
            break
        cursor = page.get("next_cursor")

    countable = [
        t for t in tasks
        if t["properties"]["Status"]["select"] and t["properties"]["Status"]["select"]["name"] not in ("Someday", "Dropped")
    ]
    if not countable:
        return 0.0
    done = sum(1 for t in countable if t["properties"]["Status"]["select"]["name"] == "Done")
    return round(done / len(countable), 4)
