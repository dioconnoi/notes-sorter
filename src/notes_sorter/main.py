from __future__ import annotations

import logging

from notes_sorter.bot.telegram_bot import BotContext, build_application
from notes_sorter.config import get_settings
from notes_sorter.ingestion.base import NoteSource
from notes_sorter.llm import build_provider
from notes_sorter.scheduler.jobs import build_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _build_sources(settings) -> list[NoteSource]:
    sources: list[NoteSource] = []
    if settings.google_keep_email and settings.google_keep_master_token:
        from notes_sorter.ingestion.google_keep import GoogleKeepSource

        sources.append(GoogleKeepSource(settings))
    if settings.google_docs_folder_id or settings.google_docs_credentials_file:
        try:
            from notes_sorter.ingestion.google_docs import GoogleDocsSource

            sources.append(GoogleDocsSource(settings))
        except Exception:  # noqa: BLE001 - optional source, any setup failure should be non-fatal
            logger.warning("Google Docs source not configured, skipping")
    return sources


def cli() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set. Run `notes-sorter-setup` first.")
    if not settings.notion_fully_provisioned():
        raise SystemExit(
            "Notion databases are not provisioned yet. Run `notes-sorter-provision` first, "
            "then copy the printed IDs into your .env."
        )

    provider = build_provider(settings)
    ctx = BotContext(settings, provider)
    app = build_application(ctx)
    sources = _build_sources(settings)

    scheduler = build_scheduler(ctx, app, sources)

    async def _on_startup(application):
        scheduler.start()
        logger.info("Scheduler started: resync every %sm, digest at '%s'", settings.resync_interval_minutes, settings.digest_cron)

    app.post_init = _on_startup
    logger.info("notes-sorter starting (provider=%s)", settings.llm_provider)
    app.run_polling()


if __name__ == "__main__":
    cli()
