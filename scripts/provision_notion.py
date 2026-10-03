"""Run once: `python -m scripts.provision_notion`.

Creates the Notes/Tasks/Projects databases under NOTION_PARENT_PAGE_ID and prints
the IDs to paste into your .env. Re-running this creates a second, duplicate set of
databases — it is intentionally not idempotent, since detecting "my previous
provisioning run" reliably is more complex than just telling you not to re-run it.
"""

from __future__ import annotations

import asyncio

from notes_sorter.config import get_settings
from notes_sorter.notion.client import build_notion_client
from notes_sorter.notion.schema import provision_workspace


async def _run() -> None:
    settings = get_settings()
    if not settings.notion_parent_page_id:
        raise SystemExit("Set NOTION_PARENT_PAGE_ID in .env first — the page must already be "
                          "shared with your Notion integration.")
    client = build_notion_client(settings)
    ids = await provision_workspace(client, settings.notion_parent_page_id)

    print("Provisioned. Add these to your .env:\n")
    for key, value in ids.items():
        print(f"{key}={value}")
    print(
        "\nOne manual step Notion's API can't do for you: open the new 'Projects' "
        "database, click the 'Progress' column header -> Edit property -> and toggle "
        "'Show as: Bar'. Everything else (percent values) updates automatically."
    )


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
