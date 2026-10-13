# agent_audit.py — a simple governance check for the AI Village agents.
#
#   python3 agent_audit.py            print a report
#   python3 agent_audit.py --save     also write it to reports/agent-audit.md
#
# It reads each agent's definition in .claude/agents/ and checks it against a small
# checklist of responsible-AI controls. It is a keyword check, not a proof of safety:
# it shows what the instructions SAY, not how the agent behaves.

import re
import sys
from pathlib import Path

HOME = Path(__file__).parent
AGENTS = HOME / ".claude" / "agents"

# (control name, regex looked for in the instructions, why it matters)
CONTROLS = [
    ("No invented facts", r"never invent|do not invent|don't invent|no invented|never make up",
     "Reduces fabricated numbers and sources"),
    ("Sources / evidence required", r"\bsource|cite|citation|evidence",
     "Makes claims checkable by a human"),
    ("Legal / compliance check", r"legal check|legal in the uk|uk law|consumer law",
     "Flags legal risk before anything is acted on"),
    ("Human review before use", r"owner (to )?(check|review)|human review|for the owner|owner decides|review and edit",
     "Keeps a person accountable for outputs"),
    ("Explicit prohibitions", r"\bnever\b|must not|do not|don't",
     "States what the agent must not do"),
    ("Honest about uncertainty", r"unsure|uncertain|not sure|confidence|say so",
     "Encourages the agent to flag what it doesn't know"),
]

RISKY_TOOLS = {"Bash": "can run shell commands", "Write": "can create/overwrite files"}


def read_agent(path):
    text = path.read_text()
    front = {}
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    body = text
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                front[k.strip()] = v.strip()
    return front, body


def audit(path):
    front, body = read_agent(path)
    tools = [t.strip() for t in front.get("tools", "").split(",") if t.strip()]
    results = [(name, bool(re.search(rx, body, re.I)), why) for name, rx, why in CONTROLS]
    risky = [f"{t} ({RISKY_TOOLS[t]})" for t in tools if t in RISKY_TOOLS]
    return {"name": front.get("name", path.stem), "model": front.get("model", "?"),
            "tools": tools, "risky": risky, "results": results}


def main():
    files = sorted(AGENTS.glob("*.md"))
    if not files:
        print("No agent files found in", AGENTS)
        return
    lines = ["# Agent governance audit", "",
             "Keyword check of each agent's instructions against a responsible-AI checklist.",
             "It shows what the instructions say, not how the agent behaves.", ""]
    for f in files:
        a = audit(f)
        passed = sum(ok for _, ok, _ in a["results"])
        lines.append(f"## {a['name']}  ({passed}/{len(a['results'])} controls found)")
        lines.append(f"- Model: {a['model']}  |  Tools: {', '.join(a['tools']) or 'none listed'}")
        if a["risky"]:
            lines.append(f"- Elevated tools to review: {'; '.join(a['risky'])}")
        for name, ok, why in a["results"]:
            lines.append(f"- [{'x' if ok else ' '}] {name} — {why}")
        lines.append("")
    out = "\n".join(lines)
    print(out)
    if "--save" in sys.argv:
        (HOME / "reports" / "agent-audit.md").write_text(out)
        print("Saved to reports/agent-audit.md")


main()
