# Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Telegram     │────▶│              │────▶│                  │
│  (text/photo) │     │              │     │   LLM provider    │
└──────────────┘     │  categorize/  │────▶│  (Claude/OpenAI/  │
┌──────────────┐     │  categorizer  │     │   Ollama)          │
│ Google Keep   │────▶│              │     └──────────────────┘
└──────────────┘     │  (structured  │
┌──────────────┐     │   output)     │     ┌──────────────────┐
│ Google Docs   │────▶│              │────▶│  notion/sync.py   │──▶ Notion
└──────────────┘     └──────────────┘     │  notion/progress  │
                                            └──────────────────┘
                            ▲
                      scheduler/jobs.py
                 (resync interval + daily digest)
```

## LLM-agnostic core

`llm/base.py` defines two capabilities every provider must implement:
`structured_complete` (prompt in, validated Pydantic model out) and `vision_ocr`
(photo in, transcribed text out). `categorize/categorizer.py` and the Telegram
photo handler only ever talk to this interface, so switching `LLM_PROVIDER` in
`.env` is the only change needed to run on Claude, OpenAI, or a local Ollama model.

Structured output is implemented per-provider with whatever that provider's API
offers natively (Claude: forced tool-use; OpenAI: `response_format=json_schema`;
Ollama: `format=<json schema>`), rather than asking the model to "please output
JSON" and hoping — this is the single biggest reliability lever for categorization
accuracy.

## Notion access

Two things are true at once:

- **Provisioning and sync always use the Notion REST API** (`notion-client`,
  wrapped in `notion/client.py`), authenticated with `NOTION_API_KEY`. This is
  deterministic and testable, which matters for creating the exact schema in
  `notion/schema.py` and for the always-on bot/scheduler process.
- **`NOTION_ACCESS_MODE=mcp`** is an additional, optional path available only to
  Claude (`AnthropicProvider.notion_mcp_complete`), which calls Notion through its
  hosted remote-MCP server instead of a bespoke REST integration — useful if
  you've already connected Notion to Claude elsewhere and would rather not create
  a second integration token. It's not used for the deterministic provisioning/
  sync paths above, because an LLM-mediated tool call is not guaranteed to produce
  the exact property schema a database needs.

In short: `NOTION_API_KEY` is required either way; MCP mode only adds a
conversational fallback on top.

## Progress bars

Notion's own rollups can sum/average, but can't cleanly express "percent of tasks
done, excluding Someday/Dropped ones" in one formula — so `notion/progress.py`
computes that in code and writes a plain `Progress` number (0.0–1.0, formatted as
percent) back onto each Project page. The Notion API has no way to turn on the
"Show as bar" *display* toggle for a property — that's a one-time manual click
after provisioning (the provisioning script tells you to do this).

## Dynamic categories

Categories are not a fixed enum. The categorizer prompt is given the list of
categories already seen in this user's workspace and told to reuse one when it
fits, coining a new short Title-Case name otherwise. This avoids both category
explosion (a new category per note) and forcing a rigid taxonomy nobody chose.

## Ingestion connectors

`ingestion/base.py` defines `NoteSource.fetch_new_notes()`. Each connector (Keep,
Docs) tracks what it's already returned in a local JSON file under `.keep_state/`
so re-running the scheduler never double-ingests. Adding a new source (e.g. Apple
Notes export, email) means implementing one class.
