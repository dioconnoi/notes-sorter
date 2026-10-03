# Blind spots and known limitations

Being upfront about these matters more than pretending they don't exist.

## Accuracy
- **Categorization/priority is a judgment call the LLM makes.** It will sometimes
  mis-rank urgency/importance or invent a due date... actually it's instructed not
  to invent dates, but it can still misread an implied one. Expect to manually
  correct Quadrant/Status in Notion sometimes — this is assistive, not authoritative.
- **Handwriting OCR via vision LLM** is good but not perfect, especially for messy
  handwriting, cursive, or low-light photos. A classic OCR engine (Tesseract) would
  be *worse* here, not better, which is why we didn't use one — but errors still
  happen and aren't auto-detected.
- **Category drift**: since categories are freeform, over months you may end up
  with near-duplicate categories ("Finance" vs "Financial Planning") if the LLM
  isn't shown enough of your existing list, or if you change providers/models.
  There's no dedup pass yet — see FEATURES.md.

## Reliability of third-party integrations
- **Google Keep has no official API.** `gkeepapi` reverse-engineers Keep's internal
  endpoints and can break without warning when Google changes them, and requires a
  "master token" obtained through a separate device-login dance, not your normal
  password — treat the Keep connector as the most fragile part of this system.
- **Notion's MCP connector mode** (`NOTION_ACCESS_MODE=mcp`) depends on Anthropic's
  beta remote-MCP connector API and Notion's hosted MCP server both staying up and
  compatible; it is not used for schema provisioning for exactly this reason.
- **Rate limits**: Notion's API (~3 req/s), Telegram's bot API, and your LLM
  provider's own limits all apply. Heavy backfills (e.g. first-time Google Docs
  sync of hundreds of documents) can hit them — there's basic retry via `tenacity`
  but no sophisticated backoff/queueing yet.

## Data integrity
- **No duplicate detection across sources.** The same idea jotted in Keep and then
  photographed on paper becomes two separate Notion entries.
- **One-way sync.** Editing a Task's Status in Notion doesn't flow back into any
  local state; editing the *source* note (e.g. in Google Docs) re-ingests it as a
  new note rather than updating the old one, because Docs sync keys on
  `(file_id, modifiedTime)`.
- **Local state loss = re-ingestion.** `.keep_state/*.json` is what prevents
  duplicate ingestion from Keep/Docs. Delete it (or run on a fresh machine without
  it) and every note gets re-processed and re-created in Notion.
- **`Done` checkbox vs `Status` select on Tasks** are two separate properties by
  design (Notion's API makes a single property do double duty awkwardly), but
  nothing currently keeps them in lockstep if you edit one manually in Notion.

## Operational
- **This is a long-running process, not serverless.** `notes-sorter` needs to stay
  running (polling Telegram + the APScheduler loop) for the bot and digests to
  work — it's not a cron job you can fire-and-forget on a serverless platform
  without adaptation.
- **Secrets live in a local `.env` file** in plaintext. Fine for a personal
  machine; don't commit it, and don't run this on shared/untrusted hardware
  without further hardening.
- **Telegram access control is a flat allowlist** (`TELEGRAM_ALLOWED_USER_IDS`).
  If you leave it empty the bot accepts messages from anyone who finds its
  username — fine for a private bot nobody else knows about, but not a real
  authorization boundary.

## Cost
- Every note costs one categorization LLM call; every photo costs one vision call.
  Heavy note-takers on a paid API (vs. local Ollama) should watch usage — there's
  no token/cost budget guard yet.

## Deliberately out of scope for v0.1
- Two-way Notion → source sync.
- Cross-source duplicate detection.
- A web dashboard (Telegram + Notion are the only interfaces).
- Multi-user/shared workspaces (each install is single-user by design).
