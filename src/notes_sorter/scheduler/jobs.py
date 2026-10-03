from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application

from notes_sorter.bot.telegram_bot import BotContext, render_bar
from notes_sorter.categorize.categorizer import categorize_note
from notes_sorter.categorize.eisenhower import QUADRANT_LABELS
from notes_sorter.ingestion.base import NoteSource
from notes_sorter.notion.progress import recompute_all_project_progress
from notes_sorter.notion.sync import sync_note

logger = logging.getLogger(__name__)


async def run_resync(ctx: BotContext, sources: list[NoteSource]) -> int:
    """Pull new notes from every configured connector, categorize, and sync to Notion.
    Returns the number of notes ingested."""
    count = 0
    for source in sources:
        try:
            notes = await source.fetch_new_notes()
        except Exception:
            logger.exception("Ingestion failed for source=%s", source.source_name)
            continue
        for raw in notes:
            try:
                categorized = await categorize_note(ctx.provider, raw.text, raw.source)
                await sync_note(ctx.notion, ctx.settings, categorized)
                count += 1
            except Exception:
                logger.exception("Failed to categorize/sync a note from %s", raw.source)
    await recompute_all_project_progress(ctx.notion, ctx.settings)
    return count


async def send_digest(ctx: BotContext, app: Application) -> None:
    tasks = await ctx.notion.databases.query(
        database_id=ctx.settings.notion_tasks_db_id,
        filter={"property": "Status", "select": {"equals": "Not Started"}},
    )
    by_quadrant: dict[str, list[str]] = {}
    for t in tasks["results"]:
        q = t["properties"]["Quadrant"]["select"]
        label = QUADRANT_LABELS.get(q["name"], q["name"]) if q else "Unclassified"
        title = t["properties"]["Name"]["title"][0]["plain_text"] if t["properties"]["Name"]["title"] else "(untitled)"
        by_quadrant.setdefault(label, []).append(title)

    progress = await recompute_all_project_progress(ctx.notion, ctx.settings)
    lines = ["*Daily digest*", ""]
    for label, titles in by_quadrant.items():
        lines.append(f"*{label}*")
        lines.extend(f"  • {t}" for t in titles)
    if progress:
        lines.append("")
        lines.append("*Project progress*")
        pages = await ctx.notion.databases.query(database_id=ctx.settings.notion_projects_db_id)
        name_by_id = {
            p["id"]: p["properties"]["Name"]["title"][0]["plain_text"]
            for p in pages["results"] if p["properties"]["Name"]["title"]
        }
        for pid, pct in progress.items():
            lines.append(f"{name_by_id.get(pid, pid)}: {render_bar(pct)}")

    text = "\n".join(lines)
    for user_id in ctx.settings.allowed_user_ids:
        try:
            await app.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
        except Exception:
            logger.exception("Failed to send digest to user_id=%s", user_id)


def build_scheduler(ctx: BotContext, app: Application, sources: list[NoteSource]) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ctx.settings.timezone)

    scheduler.add_job(
        run_resync, "interval", minutes=ctx.settings.resync_interval_minutes, args=[ctx, sources], id="resync"
    )
    scheduler.add_job(
        send_digest, CronTrigger.from_crontab(ctx.settings.digest_cron, timezone=ctx.settings.timezone),
        args=[ctx, app], id="digest",
    )
    return scheduler
