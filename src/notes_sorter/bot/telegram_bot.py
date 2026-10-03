from __future__ import annotations

import logging

from notion_client import AsyncClient
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from notes_sorter.categorize.categorizer import categorize_note
from notes_sorter.categorize.eisenhower import QUADRANT_LABELS
from notes_sorter.config import Settings
from notes_sorter.llm.base import LLMProvider
from notes_sorter.notion.client import build_notion_client
from notes_sorter.notion.progress import recompute_all_project_progress
from notes_sorter.notion.sync import sync_note

logger = logging.getLogger(__name__)

BAR_WIDTH = 10


def render_bar(pct: float) -> str:
    filled = round(pct * BAR_WIDTH)
    return f"{'█' * filled}{'░' * (BAR_WIDTH - filled)} {round(pct * 100)}%"


def _authorized(settings: Settings, update: Update) -> bool:
    allowed = settings.allowed_user_ids
    if not allowed:
        return True  # no allowlist configured — open bot, single-user default
    return update.effective_user is not None and update.effective_user.id in allowed


async def _reject(update: Update) -> None:
    if update.message:
        await update.message.reply_text("Not authorized. Ask the bot owner to add your Telegram user ID.")


class BotContext:
    def __init__(self, settings: Settings, provider: LLMProvider):
        self.settings = settings
        self.provider = provider
        self.notion: AsyncClient = build_notion_client(settings)


def build_application(ctx: BotContext) -> Application:
    app = Application.builder().token(ctx.settings.telegram_bot_token).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not _authorized(ctx.settings, update):
            return await _reject(update)
        await update.message.reply_text(
            "notes-sorter is listening. Send text or a photo of a note and I'll "
            "categorize it, extract tasks, and file it in Notion.\n\n"
            "Commands:\n/status — per-project progress bars\n/digest — today's priorities"
        )

    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not _authorized(ctx.settings, update):
            return await _reject(update)
        await update.message.chat.send_action("typing")
        progress = await recompute_all_project_progress(ctx.notion, ctx.settings)
        if not progress:
            return await update.message.reply_text("No projects yet.")
        pages = await ctx.notion.databases.query(database_id=ctx.settings.notion_projects_db_id)
        name_by_id = {p["id"]: p["properties"]["Name"]["title"][0]["plain_text"] for p in pages["results"] if p["properties"]["Name"]["title"]}
        lines = [f"{name_by_id.get(pid, pid)}\n{render_bar(pct)}" for pid, pct in progress.items()]
        await update.message.reply_text("\n\n".join(lines))

    async def digest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not _authorized(ctx.settings, update):
            return await _reject(update)
        await update.message.chat.send_action("typing")
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

        if not by_quadrant:
            return await update.message.reply_text("Nothing open. Clear inbox 🎉")

        lines = []
        for label, titles in by_quadrant.items():
            lines.append(f"*{label}*")
            lines.extend(f"  • {t}" for t in titles)
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not _authorized(ctx.settings, update):
            return await _reject(update)
        await _process_note(update, ctx, update.message.text, source="telegram")

    async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not _authorized(ctx.settings, update):
            return await _reject(update)
        await update.message.chat.send_action("typing")
        photo = update.message.photo[-1]
        file = await photo.get_file()
        image_bytes = bytes(await file.download_as_bytearray())
        text = await ctx.provider.vision_ocr(image_bytes)
        if not text.strip():
            return await update.message.reply_text("Couldn't read any text in that photo.")
        await _process_note(update, ctx, text, source="hardcopy_photo")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("digest", digest))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    return app


async def _process_note(update: Update, ctx: BotContext, raw_text: str, source: str) -> None:
    await update.message.chat.send_action("typing")
    note = await categorize_note(ctx.provider, raw_text, source)
    await sync_note(ctx.notion, ctx.settings, note)

    reply = [f"📁 *{note.category}*: {note.title}"]
    if note.tasks:
        reply.append("")
        for task in note.tasks:
            quadrant = f" [{task.quadrant.value}]" if task.quadrant else ""
            reply.append(f"• {task.title}{quadrant}")
    else:
        reply.append("(reference note, no tasks extracted)")
    await update.message.reply_text("\n".join(reply), parse_mode="Markdown")
