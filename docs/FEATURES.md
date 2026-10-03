# Features and roadmap

## Shipped in v0.1
- Multi-source ingestion: Telegram (text + photo), Google Keep, Google Docs.
- Dynamic LLM categorization, reusing existing categories.
- Eisenhower Matrix + GTD task extraction.
- Notion sync with auto-tagging (category, quadrant, status, due date, project).
- Per-project progress tracking → Notion percent bar + Telegram text bar.
- Daily Telegram digest grouped by priority quadrant.
- LLM-agnostic (Claude / OpenAI / local Ollama).
- Interactive setup wizard + one-shot Notion schema provisioning.

## Natural next additions
- **Category/project dedup pass** — periodic LLM review of all categories/projects
  to merge obvious near-duplicates ("Finance" + "Financial Planning").
- **Weekly review prompt** — GTD's weekly review, pushed as a Telegram message
  with stale Someday/Maybe items and projects with no recent activity.
- **Snooze / defer** — a Telegram reply action that pushes a task's due date out
  without re-categorizing it.
- **Two-way status sync** — a light webhook or poll so marking a Task "Done" in
  Notion updates anything Telegram-side (e.g. removes it from the next digest).
- **Voice notes** — Telegram voice messages transcribed via the LLM provider's
  audio support, same pipeline as photos.
- **Email ingestion** — forward an email to a dedicated address, parsed like any
  other note source.
- **Per-category digest filters** — `/digest work` to see only one category.
- **Confidence flagging** — when the categorizer is unsure about quadrant/category,
  tag the Notion item "⚠️ needs review" instead of guessing silently.
- **Cost guardrail** — a daily/monthly token budget with a warning once exceeded.
- **Multi-user mode** — explicitly out of v0.1's single-user design, but the
  connector/provider abstractions would support it with a per-chat-id settings
  table instead of one global `.env`.

## Why these aren't in v0.1
Each above either depends on real usage data to design well (e.g. what "near
duplicate category" actually looks like in practice) or adds meaningful surface
area (two-way sync, multi-user) that's better built once the core loop — capture,
categorize, prioritize, track — has been used for a while. See `docs/BLINDSPOTS.md`
for the specific risks each of these would need to address.
