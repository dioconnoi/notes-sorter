# notes-sorter

Your notes are scattered — Notion, Google Keep, Google Docs, photos of paper notes.
notes-sorter pulls them into one place, uses an LLM to categorize each one and pull
out real action items, prioritizes them with the Eisenhower Matrix + GTD, and keeps
a live Notion workspace (with per-project progress bars) and a Telegram bot as your
two windows into it.

Every person who runs this uses **their own** Telegram bot, their own LLM API key,
and their own Notion integration — there is no shared server and no shared data.

## What it does

- **Captures notes** via Telegram (text or a photo of a handwritten/printed note) and
  by periodically pulling from Google Keep and Google Docs.
- **Categorizes dynamically** — the LLM assigns a category per note rather than
  forcing everything into a fixed list, and reuses categories you already have.
- **Extracts tasks** from note text and classifies each with the **Eisenhower
  Matrix** (Do Now / Schedule / Delegate / Eliminate) and **GTD** concepts (next
  action, project, waiting-for, someday/maybe, reference).
- **Syncs to Notion** — three linked databases (Notes, Tasks, Projects), auto-
  tagged with category, priority quadrant, status, due date, and project.
- **Tracks progress per project** as a percentage, rendered as a native Notion
  progress bar and as a text bar (`████████░░ 80%`) in Telegram.
- **Digests** — a daily Telegram message of what's open, grouped by priority
  quadrant, plus every project's current progress.

See [`docs/FEATURES.md`](docs/FEATURES.md) for the fuller feature set and roadmap,
and [`docs/BLINDSPOTS.md`](docs/BLINDSPOTS.md) for what this deliberately does *not*
handle yet.

## Quickstart

```bash
git clone https://github.com/dioconnoi/notes-sorter
cd notes-sorter
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

notes-sorter-setup        # interactive: LLM key, Telegram bot, Notion integration
notes-sorter-provision    # one-time: creates your Notion databases
notes-sorter               # starts the bot + scheduler
```

Message your bot on Telegram. Send it a note, or a photo of a handwritten one, and
watch it show up categorized in Notion within seconds.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design, including
why Notion access defaults to the REST API even though Claude users can optionally
route through Notion's MCP connector, and [`docs/NOTION_SCHEMA.md`](docs/NOTION_SCHEMA.md)
for exactly what gets created in your workspace.

## Running your friends through it

Each person:
1. Forks or clones this repo.
2. Creates their own Telegram bot via [@BotFather](https://t.me/BotFather).
3. Gets their own LLM API key (Anthropic/OpenAI), or points at a local Ollama.
4. Creates their own Notion integration and shares a page with it.
5. Runs `notes-sorter-setup`.

No part of this requires access to anyone else's account or infrastructure.

## License

MIT — see [`LICENSE`](LICENSE).
