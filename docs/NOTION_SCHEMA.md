# Notion schema

Created by `notes-sorter-provision` under `NOTION_PARENT_PAGE_ID`.

## Projects
| Property | Type | Notes |
|---|---|---|
| Name | Title | |
| Status | Select | Active / On Hold / Completed / Archived |
| Progress | Number (percent) | Computed by `notion/progress.py`; toggle "Show as: Bar" once, manually, after provisioning |
| Category | Rich text | |

## Tasks
| Property | Type | Notes |
|---|---|---|
| Name | Title | |
| Status | Select | Not Started / In Progress / Done / Someday / Dropped |
| Done | Checkbox | Convenience flag, kept in sync with Status=Done conceptually (not auto-linked yet — see FEATURES.md) |
| Quadrant | Select | do_now / schedule / delegate / eliminate |
| GTD Type | Select | next_action / project / waiting_for / someday_maybe / reference |
| Due Date | Date | Only set when the source text states or implies one |
| Context | Rich text | GTD context, e.g. `@calls` |
| Waiting On | Rich text | Only for GTD Type = waiting_for |
| Tags | Multi-select | |
| Project | Relation → Projects | |
| Source Note | Rich text | Title of the originating note, for traceability |

## Notes
| Property | Type | Notes |
|---|---|---|
| Name | Title | |
| Category | Rich text | Freeform, LLM-assigned |
| Tags | Multi-select | |
| Source | Select | telegram / google_keep / google_docs / hardcopy_photo |
| Summary | Rich text | LLM-generated |
| Raw Text | Rich text | Original text (or OCR transcription), for audit |
| Related Tasks | Relation → Tasks | |

Re-running the provisioning script creates a second set of databases — it is not
idempotent by design (see `scripts/provision_notion.py`).
