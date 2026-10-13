# world.py — runs the Agent Village on your Mac and saves your decisions.
#
# Run it with:  python3 world.py            (opens your browser)
#               python3 world.py --quiet    (doesn't open a browser)
# Stop it with Ctrl + C.
#
# It only listens on your Mac ("127.0.0.1"), so nobody else can reach it.
#
# Besides showing files, it accepts two kinds of input from the village page:
#   POST /api/decide   accept / reject / comment on one of the manager's proposals
#   POST /api/message  send the manager a message
#   POST /api/agent    give an agent a name and outfit colour
#   POST /api/product  move a product through the Market (checked / listed), record a sale, or save its Tes link and stats
# Everything you send is saved in data/feedback.json for the manager's next run.

import http.server
import json
import sys
import webbrowser
from functools import partial

from core import AGENTS_FILE, DATA, HOME, add_task, load, log, now, save

PORT = 8000
FEEDBACK_FILE = DATA / "feedback.json"
MAX_TEXT = 2000
PRODUCTS_FILE = DATA / "products.json"
STAGES = ("draft", "checked", "listed")
ALLOWED_DIRS = {"reports", "briefings", "strategy", "products/drafts", "university"}
OUTFITS = {"red", "blue", "green", "purple", "orange", "pink", "teal", "gold"}


def briefing_file(date):
    # Only allow plain dates like 2026-09-30, so nobody can point this at other files.
    if not (isinstance(date, str) and len(date) == 10 and date.replace("-", "").isdigit()):
        raise ValueError("bad date")
    return HOME / "briefings" / f"{date}.json"


def add_feedback(entry):
    feedback = load(FEEDBACK_FILE, [])
    entry = {"id": len(feedback) + 1, "time": now(), "processed": False, **entry}
    feedback.append(entry)
    save(FEEDBACK_FILE, feedback)
    return entry


class VillageHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the terminal quiet

    def reply(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # /api/files?dir=reports -> files in that folder, newest first (by when they were last changed)
        if self.path.startswith("/api/files"):
            from urllib.parse import parse_qs, urlparse
            folder = parse_qs(urlparse(self.path).query).get("dir", [""])[0]
            if folder not in ALLOWED_DIRS:
                return self.reply(404, {"error": "unknown folder"})
            base = HOME / folder
            files = [f for f in base.glob("*") if f.is_file() and f.suffix in (".md", ".json") and not f.name.startswith(("~", "."))] if base.is_dir() else []
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return self.reply(200, [f.name for f in files])
        return super().do_GET()

    def do_POST(self):
        # The custom header stops other websites from sending data to this server.
        if self.headers.get("X-Village") != "1":
            return self.reply(403, {"error": "forbidden"})
        try:
            length = min(int(self.headers.get("Content-Length", 0)), 20000)
            data = json.loads(self.rfile.read(length) or b"{}")
            note = str(data.get("note", "")).strip()[:MAX_TEXT]

            if self.path == "/api/decide":
                decision = data.get("decision")
                if decision not in ("accept", "reject", "comment"):
                    raise ValueError("bad decision")
                briefing = json.loads(briefing_file(data.get("briefing")).read_text())
                proposal = next(p for p in briefing.get("proposals", []) if p.get("id") == data.get("proposal"))
                entry = {"type": "decision", "briefing": data["briefing"], "proposal": proposal["id"],
                         "title": proposal.get("title"), "decision": decision, "note": note}
                # Accepting a quest that has an agent and a task puts it straight on the task board.
                if decision == "accept" and proposal.get("agent") and proposal.get("task"):
                    task = add_task(proposal["agent"], proposal["task"], created_by="you")
                    entry["task_id"] = task["id"]
                    log("you", f"accepted quest '{proposal.get('title')}' → task #{task['id']} for {proposal['agent']}")
                else:
                    log("you", f"{decision} on quest '{proposal.get('title')}'" + (f": {note[:100]}" if note else ""))
                return self.reply(200, add_feedback(entry))

            if self.path == "/api/message":
                if not note:
                    raise ValueError("empty message")
                log("you", f"message to manager: {note[:100]}")
                return self.reply(200, add_feedback({"type": "message", "note": note}))

            if self.path == "/api/agent":
                agents = load(AGENTS_FILE, {})
                agent = data.get("agent")
                if agent not in agents:
                    raise ValueError("no such agent")
                nickname = " ".join(str(data.get("nickname", "")).split())[:20]
                outfit = data.get("outfit")
                if nickname:
                    agents[agent]["nickname"] = nickname
                if outfit in OUTFITS:
                    agents[agent]["outfit"] = outfit
                save(AGENTS_FILE, agents)
                log("you", f"named {agent} '{agents[agent].get('nickname', agent)}'")
                return self.reply(200, agents[agent])

            if self.path == "/api/product":
                file = str(data.get("file", ""))
                path = (HOME / file).resolve()
                drafts = (HOME / "products" / "drafts").resolve()
                if path.parent != drafts or path.suffix != ".md" or not path.exists():
                    raise ValueError("no such product")
                products = load(PRODUCTS_FILE, {})
                item = products.setdefault(file, {"stage": "draft", "price": None, "sales": []})
                if data.get("stage") in STAGES:
                    item["stage"] = data["stage"]
                    log("you", f"marked {path.stem} as {data['stage']}")
                if data.get("price") is not None:
                    price = round(float(data["price"]), 2)
                    if not 0 <= price <= 300:
                        raise ValueError("price must be £0–£300")
                    item["price"] = price
                if data.get("sale") is not None:
                    amount = round(float(data["sale"]), 2)
                    if not 0 < amount <= 1000:
                        raise ValueError("sale must be £0.01–£1000")
                    item["sales"].append({"time": now(), "amount": amount})
                    log("you", f"💷 recorded a £{amount:.2f} sale of {path.stem}")
                if data.get("url") is not None:
                    url = str(data["url"]).strip()[:300]
                    if url and not url.startswith("https://"):
                        raise ValueError("the link must start with https://")
                    item["url"] = url
                if data.get("tes_status") in ("pending", "live"):
                    item["tes_status"] = data["tes_status"]
                    log("you", f"{path.stem} is {'live on Tes' if data['tes_status'] == 'live' else 'waiting for Tes approval'}")
                for field in ("views", "downloads"):
                    if data.get(field) is not None:
                        n = int(data[field])
                        if not 0 <= n <= 10_000_000:
                            raise ValueError(f"{field} must be 0 or more")
                        item[field] = n
                if data.get("archived") is not None:
                    item["archived"] = bool(data["archived"])
                save(PRODUCTS_FILE, products)
                return self.reply(200, item)

            return self.reply(404, {"error": "unknown endpoint"})
        except (ValueError, KeyError, StopIteration, FileNotFoundError, json.JSONDecodeError) as e:
            return self.reply(400, {"error": str(e) or "bad request"})


if __name__ == "__main__":
    handler = partial(VillageHandler, directory=str(HOME))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    url = f"http://localhost:{PORT}/world.html"
    print(f"Agent Village is live at {url}  (Ctrl + C to stop)")
    if "--quiet" not in sys.argv:
        webbrowser.open(url)
    server.serve_forever()
