# core.py — shared tools every agent uses.
#
#   ask()          talk to the AI model
#   agents         the registry: which agents exist and how their last run went
#   tasks          the task board: jobs waiting for agents, and their results
#   log()          write a line to the daily log file

import json
import urllib.request
from datetime import datetime
from pathlib import Path

HOME = Path(__file__).parent
DATA = HOME / "data"
LOGS = HOME / "logs"
DATA.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)

AGENTS_FILE = DATA / "agents.json"
TASKS_FILE = DATA / "tasks.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ---------- talking to the AI ----------

def ask(prompt, role="You are a helpful assistant.", want_json=False):
    """Send a prompt to the local model. With want_json=True the reply is
    forced to be JSON and returned as a Python dict/list."""
    body = {"model": MODEL, "system": role, "prompt": prompt, "stream": False}
    if want_json:
        body["format"] = "json"
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        text = json.loads(response.read())["response"]
    return json.loads(text) if want_json else text


# ---------- simple JSON storage ----------

def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save(path, data):
    path.write_text(json.dumps(data, indent=2))


# ---------- logging ----------

def log(agent, message):
    line = f"{now()} [{agent}] {message}"
    print(line)
    with open(LOGS / f"{datetime.now():%Y-%m-%d}.log", "a") as f:
        f.write(line + "\n")


# ---------- agent registry ----------

def register_agent(name, job, built=True):
    """Add an agent to the registry (does nothing if it's already there)."""
    agents = load(AGENTS_FILE, {})
    if name not in agents:
        agents[name] = {"job": job, "built": built,
                        "last_run": None, "last_status": "never run"}
        save(AGENTS_FILE, agents)


def record_run(name, status):
    """Call at the end of every agent run: status is 'ok' or an error message."""
    agents = load(AGENTS_FILE, {})
    agents.setdefault(name, {"job": "?", "built": True})
    agents[name]["last_run"] = now()
    agents[name]["last_status"] = status
    save(AGENTS_FILE, agents)


# ---------- task board ----------

def add_task(agent, description, created_by="you"):
    tasks = load(TASKS_FILE, [])
    task = {"id": len(tasks) + 1, "agent": agent, "description": description,
            "status": "pending", "created": now(), "created_by": created_by,
            "result": None}
    tasks.append(task)
    save(TASKS_FILE, tasks)
    return task


def pending_tasks(agent):
    return [t for t in load(TASKS_FILE, []) if t["agent"] == agent and t["status"] == "pending"]


def finish_task(task_id, result, status="done"):
    tasks = load(TASKS_FILE, [])
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = status
            t["result"] = result
            t["finished"] = now()
    save(TASKS_FILE, tasks)
