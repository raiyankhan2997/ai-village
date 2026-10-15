 Data model and commands

Everything the system knows is stored as plain files so it can be read, diffed and audited.

## `data/agents.json` (agent registry)
Keyed by agent name. Fields: `job` (what it is for), `built` (true or false), `last_run` (timestamp or null), `last_status` (`ok`, `error: <reason>` or `never run`), and optionally `nickname` and `outfit` (cosmetic, set from the dashboard).

## `data/tasks.json` (task board)
A list of tasks. Fields: `id`, `agent`, `description`, `status`, `created`, `created_by`, `result`, and `finished` once the task ends.
Status moves `pending` -> `working` -> `done` or `failed`. A failed task keeps its reason in `result`, and the agent's registry entry records `error: <reason>`, so the next briefing can see it.

## `data/feedback.json` (owner decisions, git-ignored)
Written by the dashboard server. Each entry has an `id`, `time`, `processed` flag and a `type`:
- `decision`: `briefing`, `proposal`, `title`, `decision` (accept, reject or comment), optional `note`, and `task_id` if accepting created a task.
- `message`: a free-text `note` for the manager.
The manager reads unprocessed entries (`python3 board.py feedback`) and marks them handled with `feedback-done`.

## `data/meetings.json`
Created on first use of `board.py meet`. Records agent-to-agent collaboration (`from`, `to`, `says`, `reply`, `time`). Only the latest 200 are kept.

## `logs/YYYY-MM-DD.log` (git-ignored)
One line per event: `YYYY-MM-DD HH:MM [agent] message`.

## Dashboard API (`world.py`, localhost only)
| Endpoint | Purpose |
|---|---|
| `GET /api/files?dir=<name>` | List files in an allow-listed folder (reports, briefings, strategy, products/drafts, university) |
| `POST /api/decide` | Accept, reject or comment on a manager proposal |
| `POST /api/message` | Send the manager a message |
| `POST /api/agent` | Set an agent's nickname or outfit colour |
| `POST /api/product` | Move a product through draft, checked and listed; record a price, sale, link, views or downloads by hand |

All POSTs require the header `X-Village: 1`. Inputs are length- and range-checked, and file paths are restricted to expected folders.
