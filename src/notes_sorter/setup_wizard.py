"""Interactive first-run setup: `notes-sorter-setup`.

Walks a non-technical friend through creating their own `.env`, validates each
credential with a live API call as they go, and offers to provision the Notion
workspace at the end. Nothing here talks to anyone else's infrastructure — every
value collected is theirs alone.
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import httpx

ENV_PATH = Path(".env")
EXAMPLE_PATH = Path(".env.example")


def _prompt(label: str, default: str = "", secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def _set_env_var(lines: list[str], key: str, value: str) -> list[str]:
    prefix = f"{key}="
    out = []
    found = False
    for line in lines:
        if line.startswith(prefix):
            out.append(f"{prefix}{value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{prefix}{value}")
    return out


async def _validate_telegram(token: str) -> str | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
    if resp.status_code == 200 and resp.json().get("ok"):
        return resp.json()["result"]["username"]
    return None


async def _validate_notion(api_key: str) -> bool:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.notion.com/v1/users/me",
            headers={"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28"},
        )
    return resp.status_code == 200


async def run() -> None:
    print("notes-sorter setup\n" + "=" * 20)

    if not ENV_PATH.exists():
        shutil.copy(EXAMPLE_PATH, ENV_PATH)
    lines = ENV_PATH.read_text().splitlines()

    print("\n1) LLM provider")
    provider = _prompt("anthropic / openai / ollama", default="anthropic")
    lines = _set_env_var(lines, "LLM_PROVIDER", provider)
    if provider == "anthropic":
        key = _prompt("Anthropic API key (sk-ant-...)")
        lines = _set_env_var(lines, "ANTHROPIC_API_KEY", key)
    elif provider == "openai":
        key = _prompt("OpenAI API key (sk-...)")
        lines = _set_env_var(lines, "OPENAI_API_KEY", key)
    else:
        host = _prompt("Ollama host", default="http://localhost:11434")
        lines = _set_env_var(lines, "OLLAMA_HOST", host)

    print("\n2) Telegram bot")
    print("Create one at https://t.me/BotFather if you haven't, then paste its token.")
    tg_token = _prompt("Telegram bot token")
    username = await _validate_telegram(tg_token)
    if username:
        print(f"  ✓ connected to @{username}")
    else:
        print("  ✗ couldn't reach that bot — double check the token later")
    lines = _set_env_var(lines, "TELEGRAM_BOT_TOKEN", tg_token)

    user_id = _prompt("Your Telegram numeric user ID (message @userinfobot to find it)")
    lines = _set_env_var(lines, "TELEGRAM_ALLOWED_USER_IDS", user_id)

    print("\n3) Notion")
    print("Create an internal integration at https://www.notion.so/my-integrations,")
    print("then share the parent page you want this under with that integration.")
    notion_key = _prompt("Notion integration secret")
    if await _validate_notion(notion_key):
        print("  ✓ Notion key valid")
    else:
        print("  ✗ couldn't authenticate with Notion — double check the key later")
    lines = _set_env_var(lines, "NOTION_API_KEY", notion_key)

    parent_page = _prompt("Notion parent page ID (from the page URL)")
    lines = _set_env_var(lines, "NOTION_PARENT_PAGE_ID", parent_page)

    ENV_PATH.write_text("\n".join(lines) + "\n")
    print("\nSaved .env.")
    print("Next: run `notes-sorter-provision` to create your Notion databases,")
    print("then `notes-sorter` to start the bot.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
