# AI Village: a supervised multi-agent AI system

A small team of role-specific AI agents, orchestrated with [Claude Code](https://claude.com/claude-code), that research online income ideas, draft revision material, support my university work and tutoring, and report what they do through one shared, auditable task board. A person (me) approves or rejects every proposal. Nothing outward-facing happens without a human decision.

**Status:** personal learning project, started June 2026 and still in progress.
**Built with:** Python 3 (standard library only) and Claude Code. I designed the system and wrote the agent instructions, and I used Claude Code to help write and revise the code. I say this plainly because the interesting parts of the project are the design decisions and the checks, not the typing.

> **Honest scope note.** This public repository contains the task board, the dashboard server, the governance audit, four agent definitions and one example output. The daily manager and weekly strategist (Claude Code skills), the dashboard front-end page, and my research reports and draft workbooks live in my full local project and are not published here. Sections below say which is which.

---

## 1. The problem

I have a few hours a week. In that time I wanted to research markets, draft products, keep up with university work and prepare tutoring sessions, and keep track of what I had decided. I wanted to find out how far a **supervised** team of AI agents could take that workload, with two constraints I cared about from the start:

1. A human stays in control of every decision.
2. Everything an agent does must be visible afterwards, so mistakes can be found.

## 2. How it fits together

```
              you (the owner)
                   |
        accept / reject / comment
                   |
   +---------------v----------------+        reads feedback
   |  Dashboard server (world.py)   |  ----> data/feedback.json
   |  127.0.0.1 only, local          |             |
   +---------------+----------------+             |
                   |                              v
                   |                     Manager (daily skill)  [full local project]
                   |                     Strategist (weekly)    [full local project]
                   v                              |
          Shared task board  <--- tasks ----------+
     (board.py + core.py, JSON)
        |        |        |        |
  researcher  content-  university  tutor-
              creator   assistant   assistant      <- agents/ (published here)
        |
        +--> logs/YYYY-MM-DD.log, data/agents.json, data/tasks.json
                              |
                              v
               agent_audit.py checks each agent's instructions
               against a responsible-AI checklist -> reports/agent-audit.md
```

## 3. The agents

Each agent is a Markdown file with a short header (name, description, allowed tools, model) followed by plain-English instructions. Claude Code reads them from `.claude/agents/`. A copy sits in `agents/` for easy browsing; the two folders are identical.

| Agent | What it does | Tools it may use | Hard limits written into its instructions |
|---|---|---|---|
| **researcher** | Researches legal ways to earn online and writes a short report with a verdict | WebSearch, WebFetch, Read, Write, Bash | At least 6 searches and 3 full pages read. Every idea gets a UK legal check rated *Clearly legal / Legal but needs care / Risky grey area / Illegal (excluded)*. A fixed exclusion list (scams, fake reviews, deceiving customers, targeting vulnerable people, unlicensed financial advice, and so on). Numbers without a source must be labelled "estimate". No investment advice or trades. |
| **content-creator** | Drafts original GCSE/A-level Maths and Chemistry revision packs | WebSearch, WebFetch, Read, Write, Bash | Everything must be original. Public specimen papers may be studied for style only. Maths answers are checked by running Python. Anything unverified goes in a "Needs owner check" list. Output stays a draft until I review it. |
| **university** | Explains topics, summarises my notes, makes practice questions, plans revision, tracks internship deadlines | WebSearch, WebFetch, Read, Write, Bash | One hard rule: it never writes assessed work for me to hand in. It must not invent organisations, programmes or deadlines, and it warns about red-flag roles (payment requests, unpaid roles that should be paid). It drafts messages but never sends anything. |
| **tutor-assistant** | Plans lessons and writes original practice questions with mark schemes for tutoring I run | Read, Write, Bash | I teach; it only prepares. It never contacts students or parents. Students appear only under codenames ("Student A") and no names, schools, contact details or health details are stored, because they are often children. Everything is reviewed by me first. |

An example of the tutor-assistant's output is in [`examples/sample-lesson-plan.md`](examples/sample-lesson-plan.md) (a 60-minute GCSE moles lesson with original questions, a mark scheme and common mistakes, marked DRAFT for owner review).

**Not published here:** a daily *manager* skill that reads my feedback, checks each agent's last run, flags problems, proposes tasks and writes a briefing, and a weekly *strategist* skill that recommends the next week's focus.

## 4. The shared task board (`core.py`, `board.py`)

State is plain JSON so it can be read, diffed and audited without special tools.

- `data/agents.json`: the registry. For each agent: its job, whether it is built, last run time and last status (`ok`, an error message, or `never run`).
- `data/tasks.json`: the task list. Each task has an id, the agent it is for, a description, a status (`pending`, `working`, `done`, `failed`), created and finished times, who created it, and a short result.
- `logs/YYYY-MM-DD.log`: a timestamped line for every start, finish, failure, message and meeting.

Agents report through one small command-line tool, so there is a single place where behaviour is recorded:

```bash
python3 board.py status                          # agents and open tasks
python3 board.py add <agent> "<task>" [by]       # post a task
python3 board.py start <task_id>                 # agent starts a task
python3 board.py finish <task_id> "<summary>"    # done, with a one-line result
python3 board.py fail <task_id> "<reason>"       # failed, with the reason
python3 board.py log <agent> "<message>"         # free-form log line
python3 board.py meet <from> <to> "<says>" ["<reply>"]  # record agent-to-agent collaboration
python3 board.py feedback                        # show the owner's unread decisions and messages
python3 board.py feedback-done <id> ["reply"]    # mark feedback as handled
```

Why this design: if an agent fails or never runs, it shows up as `error: ...` or `never run` in the next briefing rather than silently disappearing. That visibility was the most useful property of the whole project.

`core.py` also contains a small `ask()` helper that can call a local model served by Ollama. It is not used by the Claude Code agents, `board.py` or `world.py`.

## 5. The dashboard server (`world.py`)

A local-only Python HTTP server (standard library) that serves the project folder to `127.0.0.1` and accepts my decisions. It handles:

- `POST /api/decide`: accept, reject or comment on one of the manager's proposals. Accepting a proposal that names an agent and a task puts it on the task board automatically, and the decision is saved to `data/feedback.json` for the manager's next run. This is the human-in-the-loop step.
- `POST /api/message`: send the manager a free-text message.
- `POST /api/agent`: give an agent a nickname and outfit colour (cosmetic).
- `POST /api/product`: move a revision product through `draft → checked → listed`, record a sale or marketplace link by hand, and archive it. Nothing is published automatically.
- `GET /api/files?dir=...`: list files in an allow-listed set of folders.

Basic hardening that is actually in the code: it binds only to `127.0.0.1`; every POST must carry a custom `X-Village` header (so other websites cannot post to it); request size is capped (20,000 bytes, notes 2,000 characters); briefing dates must be plain `YYYY-MM-DD`; product paths are resolved and must sit inside `products/drafts`; prices and sale amounts are range-checked. This is sensible hygiene for a local tool, not a security review. Note that the server serves the project folder statically to localhost, which is fine on my own machine and the reason `data/feedback.json` and `logs/` are in `.gitignore`.

The dashboard's front-end page (`world.html`) is not in this repository yet, so `python3 world.py` starts the server but shows no page.

## 6. Governance check: `agent_audit.py`

A script that reads each agent's definition in `.claude/agents/` and checks its instructions against six responsible-AI controls using keyword matching:

| Control | What the check looks for |
|---|---|
| No invented facts | "never invent", "do not invent", "no invented", "never make up" |
| Sources or evidence required | "source", "cite", "evidence" |
| Legal or compliance check | "legal check", "legal in the UK", "UK law", "consumer law" |
| Human review before use | "owner to check/review", "human review", "review and edit" |
| Explicit prohibitions | "never", "must not", "do not", "don't" |
| Honest about uncertainty | "unsure", "uncertain", "not sure", "confidence", "say so" |

It also flags agents holding elevated tools (`Bash` can run shell commands, `Write` can overwrite files). Run it with `python3 agent_audit.py` (add `--save` to write `reports/agent-audit.md`).

### What it found on my own agents

| Agent | Controls found | Missing |
|---|---|---|
| researcher | 6 / 6 | none |
| tutor-assistant | 5 / 6 | no explicit legal-check wording |
| university | 5 / 6 | no explicit legal-check wording |
| content-creator | 4 / 6 | no explicit "never invent" wording; no legal-check wording |

All four agents hold `Write` and `Bash`, so all four are flagged for review. The full output is in [`reports/agent-audit.md`](reports/agent-audit.md).

### How I read the results (and where the check is weak)

- It is a **keyword check**. It shows what the instructions *say*, not how an agent *behaves*. It cannot tell me an agent obeys its rules.
- It produces false negatives. The content-creator says "Everything must be original" and "Accuracy matters more than volume" but never uses the exact phrase the check looks for, so it is marked missing. The fix may be better wording or a better check.
- Some controls do not apply to every agent. A legal check makes sense for the researcher and the content creator, but it is arguably not needed for a revision-help assistant. The checklist treats all agents the same, which is a simplification.
- The real value was the habit: writing the rules down as a checklist made me notice which agents had thinner instructions than others.

## 7. Guardrails

- No invented numbers, sources, grades or experience. Unverified items are labelled as such.
- UK legal check on every income idea, with a fixed list of excluded activities.
- No trades or financial advice.
- No contact with students or parents; students only as codenames; minimal, anonymous notes.
- No assessed work written for me to submit.
- Everything is a draft until a person reviews it. Agents never publish, send or sell.
- Personal details are removed from the public copies of the agent files, and `.gitignore` excludes feedback, logs and tutoring notes.

## 8. Design decisions and what I learned

- **Human in the loop by design.** The manager proposes, I decide. This was the first rule, not an afterthought, and it is why the dashboard exists.
- **Separate roles beat one general prompt.** Splitting research, content, university work and tutoring gave clearer, easier-to-check output than a single catch-all instruction.
- **Structured logging made failures visible.** Reporting through one CLI meant a failed or never-run agent showed up in the daily briefing.
- **Platform rules change the workflow.** While researching, an agent flagged that a marketplace bans low-effort AI content. I added a mandatory human review and edit step before anything could be sold.
- **Governance needs a measurable check, even a crude one.** Writing `agent_audit.py` showed me gaps I had not noticed, and also showed me the limits of keyword matching.
- **Instructions are not evidence of behaviour.** The biggest gap in the project is that I check what the prompts say, not what the agents do.

## 9. Limitations (honest)

- Agents are defined by prompts. There is **no formal test suite and no measured error rate**. I cannot yet say how often an agent is wrong.
- The audit is keyword-based, as described above.
- Research output depends on web sources and needs human fact-checking before anyone relies on it. Generated revision material has not been checked by an independent teacher.
- The dashboard front-end, manager and strategist skills, and my research reports and draft workbooks are not in this repo, so a reader cannot fully reproduce the system from it.
- It is a single-user, local tool. No authentication beyond running on localhost.
- This is a learning project. I claim no revenue.

## 10. What I would do next

1. Build a small evaluation set: give each agent real tasks with known answers and measure how often it is wrong.
2. Replace the keyword audit with checks that run an agent on tricky prompts (for example, "invent a statistic") and test whether it refuses.
3. Publish the dashboard front-end and the manager and strategist skills, with personal details removed.
4. Add automated tests for `core.py`, `board.py` and the input validation in `world.py`.

## 11. Repository layout

```
.claude/agents/      agent definitions Claude Code reads (researcher, content-creator, university, tutor-assistant)
agents/              identical copy for browsing
core.py              shared storage, logging and agent registry
board.py             command-line tool agents use to report their work
world.py             local dashboard server and decision handling
agent_audit.py       responsible-AI checklist over the agent definitions
reports/             agent-audit.md (output of the audit)
examples/            sample-lesson-plan.md (tutor-assistant output, marked draft)
data/                agents.json and tasks.json (empty starting state; feedback.json is git-ignored)
docs/                data-model.md (files, fields, dashboard API)
```

## 12. Running it

Requires Python 3 only. Agents run inside Claude Code.

```bash
python3 board.py status        # agents and tasks
python3 agent_audit.py         # governance checklist
python3 world.py               # dashboard server on http://localhost:8000 (front-end page not yet included)
