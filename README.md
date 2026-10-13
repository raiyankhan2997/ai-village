# AI Village — a multi-agent AI system I designed and built

A small team of specialised AI agents, orchestrated with Claude Code, that research
online income ideas, draft products, and report their work to a manager agent. A local
web dashboard ("Agent Village") shows what each agent is doing and lets a human
approve or reject the manager's proposals.

## The problem
One person with a few hours a week can't research markets, draft products and track
decisions at the same time. I wanted to see how far a *supervised* team of AI agents
could take that workload — while keeping a human in control of every decision.

## How it works
| Agent | Job |
|---|---|
| Manager (daily skill) | Reads my feedback, checks every agent, flags problems, assigns tasks, writes a briefing |
| Strategist (weekly skill) | Reviews everything and recommends next week's focus |
| Researcher | Researches online income ideas, each with a UK legal check and risk rating |
| University assistant | Revision help and internship tracking; forbidden from writing assessed work for me to submit |
| Content creator | Drafts revision material for me to check and edit before anything is sold |

* **Shared task board** (`board.py`, `core.py`): every agent starts, finishes, fails and
  logs tasks through one small Python CLI, so state lives in plain JSON files and is auditable.
* **Dashboard** (`world.py`): a local-only Python HTTP server (127.0.0.1) that shows agents,
  tasks and logs, and records my accept / reject / comment decisions for the manager's next run.
* **Guardrails written into every agent's instructions**: no invented numbers or sources,
  UK-legal checks, no trades or financial advice, no deception, human review before publishing.

## Governance check: `agent_audit.py`
A small script that reads each agent's instructions and checks them against a
responsible-AI checklist (no invented facts, sources required, legal check, human review,
explicit prohibitions, honesty about uncertainty). It also flags agents with elevated tools
(Bash, Write). Running it on my own agents showed the content creator had no explicit
"never invent facts" or legal-check rule, so I know what to tighten.
It is a keyword check — it shows what instructions say, not how an agent behaves.

## What I learned
* **Human-in-the-loop design:** the manager proposes, I decide. Agents never act on their own
  on anything outward-facing.
* **Responsible AI in practice:** agents had to flag platform rules (e.g. a marketplace that bans
  low-effort AI content) — so the workflow requires my genuine review and edits.
* **Reliability:** agents report through a structured log, which made failures and
  "never run" agents visible in the daily briefing.
* **Scoping:** separating research, content and strategy roles produced clearer output than
  one general-purpose prompt.

## Stack
Python 3 (standard library only), Claude Code (agents + skills), JSON data files, local HTML dashboard.

## Run it
```bash
python3 board.py status     # see agents and tasks
python3 world.py            # open the Agent Village dashboard
python3 agent_audit.py      # governance checklist across agents
```

## Limitations (honest)
* Early-stage: built over a few days; agents are prompt-defined, not evaluated with a formal test suite.
* Research quality depends on web sources and needs human fact-checking.
* No revenue claimed — this is a learning project.
