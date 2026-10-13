# board.py — how agents report what they're doing.
#
# Agents run these commands so the task board, logs and Agent Village stay up to date.
#
#   python3 board.py status                       show all agents and open tasks
#   python3 board.py register <agent> "<job>"      add a new agent to the village
#   python3 board.py add <agent> "<task>" [by]     post a task for an agent
#   python3 board.py start <task_id>               agent starts working on a task
#   python3 board.py finish <task_id> "<result>"   task done (result = short summary)
#   python3 board.py fail <task_id> "<reason>"     task failed
#   python3 board.py log <agent> "<message>"       write to today's village log
#   python3 board.py meet <from> <to> "<says>" ["<reply>"]   two agents meet to work together
#   python3 board.py feedback                      show the owner's unread decisions & messages
#   python3 board.py feedback-done <id> ["reply"]  mark feedback as handled (optional reply to the owner)

import sys

from core import (AGENTS_FILE, DATA, TASKS_FILE, add_task, finish_task, load, log,
                  now, record_run, save)


def set_built(agent, job):
    agents = load(AGENTS_FILE, {})
    info = agents.setdefault(agent, {"last_run": None, "last_status": "never run"})
    info["job"] = job
    info["built"] = True
    save(AGENTS_FILE, agents)


def find_task(task_id):
    for t in load(TASKS_FILE, []):
        if t["id"] == task_id:
            return t
    sys.exit(f"No task #{task_id}")


def start(task_id):
    tasks = load(TASKS_FILE, [])
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "working"
    save(TASKS_FILE, tasks)
    task = find_task(task_id)
    record_run(task["agent"], "ok")
    log(task["agent"], f"started task #{task_id}: {task['description']}")


def status():
    for name, info in load(AGENTS_FILE, {}).items():
        state = info["last_status"] if info.get("built") else "not built"
        nick = f" \"{info['nickname']}\"" if info.get("nickname") else ""
        print(f"{name}{nick}: {state} · last run: {info['last_run'] or 'never'} — {info['job']}")
    print()
    open_tasks = [t for t in load(TASKS_FILE, []) if t["status"] in ("pending", "working")]
    for t in open_tasks:
        print(f"#{t['id']} [{t['status']}] {t['agent']}: {t['description']}")
    if not open_tasks:
        print("No open tasks.")


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("status", [])
    if cmd == "status":
        status()
    elif cmd == "register":
        set_built(args[0], args[1])
        log(args[0], "joined the village")
    elif cmd == "add":
        t = add_task(args[0], args[1], created_by=args[2] if len(args) > 2 else "you")
        log(t["created_by"], f"posted task #{t['id']} for {t['agent']}")
        print(f"Task #{t['id']} added")
    elif cmd == "start":
        start(int(args[0]))
    elif cmd in ("finish", "fail"):
        task = find_task(int(args[0]))
        finish_task(task["id"], args[1], status="done" if cmd == "finish" else "failed")
        record_run(task["agent"], "ok" if cmd == "finish" else f"error: {args[1]}")
        log(task["agent"], f"{'finished' if cmd == 'finish' else 'FAILED'} task #{task['id']}: {args[1][:150]}")
    elif cmd == "log":
        log(args[0], args[1])
    elif cmd == "meet":
        meetings = load(DATA / "meetings.json", [])
        meetings.append({"id": len(meetings) + 1, "time": now(), "from": args[0], "to": args[1],
                         "says": args[2], "reply": args[3] if len(args) > 3 else ""})
        save(DATA / "meetings.json", meetings[-200:])
        log(args[0], f"went to see {args[1]}: {args[2][:100]}")
    elif cmd == "feedback":
        unread = [f for f in load(DATA / "feedback.json", []) if not f["processed"]]
        for f in unread:
            if f["type"] == "message":
                print(f"#{f['id']} MESSAGE ({f['time']}): {f['note']}")
            else:
                extra = f" → task #{f['task_id']}" if f.get("task_id") else ""
                print(f"#{f['id']} {f['decision'].upper()} '{f['title']}' ({f['briefing']}){extra}"
                      + (f" — note: {f['note']}" if f['note'] else ""))
        if not unread:
            print("No new feedback from the owner.")
    elif cmd == "feedback-done":
        feedback = load(DATA / "feedback.json", [])
        for f in feedback:
            if f["id"] == int(args[0]):
                f["processed"] = True
                if len(args) > 1:
                    f["reply"] = args[1]
        save(DATA / "feedback.json", feedback)
    else:
        sys.exit(__doc__ or f"Unknown command: {cmd}")
