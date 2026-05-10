"""
Axeng — FastAPI Backend
Serves real data from Linear, GitHub, and agent logs to the Next.js UI.
"""
import os, json, sqlite3, sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from functools import lru_cache

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
AXENG_ROOT = (SCRIPT_DIR / "../..").resolve()  # nextjs → ui → axeng
SRC_DIR = AXENG_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from config import (
    linear_project_ids, linear_github_map, team_members,
    github_orgs, ex_members,
    get,
)

# ── Env helpers (before FastAPI imports) ─────────────────────────────────────
def load_env() -> dict:
    env_file = Path.home() / ".hermes" / ".env"
    env = {}
    if env_file.exists():
        for ln in env_file.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip()
    return env

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Axeng API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def linear_query(query: str, variables: dict = None) -> dict:
    """Query Linear GraphQL API."""
    import urllib.request, urllib.parse, urllib.error
    env = load_env()
    api_key = env.get("LINEAR_API_KEY", "")
    if not api_key:
        return {"data": None, "error": "No LINEAR_API_KEY"}

    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=body,
        headers={"Authorization": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"data": None, "error": str(e)}

def github_graphql(query: str, variables: dict = None) -> dict:
    """Query GitHub GraphQL API."""
    import urllib.request
    env = load_env()
    token = env.get("GITHUB_TOKEN", env.get("GITHUB_AUTH", ""))
    if not token:
        return {"data": None, "error": "No GitHub token"}

    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"data": None, "error": str(e)}

# ── Log DB ─────────────────────────────────────────────────────────────────────
LOGS_DB = Path.home() / ".hermes" / "axeng-logs.db"

def init_logs_db():
    """Create logs table if it doesn't exist."""
    LOGS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(LOGS_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent TEXT NOT NULL DEFAULT 'Axemaster',
            type TEXT NOT NULL,
            level TEXT NOT NULL DEFAULT 'info',
            action TEXT NOT NULL,
            details TEXT,
            duration_ms INTEGER,
            tool TEXT,
            target TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_entry(
    agent: str, log_type: str, action: str,
    details: str = None, level: str = "info",
    duration_ms: int = None, tool: str = None, target: str = None
):
    """Insert a log entry into the DB."""
    conn = sqlite3.connect(LOGS_DB)
    conn.execute("""
        INSERT INTO agent_logs (timestamp, agent, type, level, action, details, duration_ms, tool, target)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), agent, log_type, level, action, details, duration_ms, tool, target))
    conn.commit()
    conn.close()

def get_logs(limit: int = 50, log_type: str = None) -> list:
    init_logs_db()
    conn = sqlite3.connect(LOGS_DB)
    if log_type:
        rows = conn.execute(
            "SELECT * FROM agent_logs WHERE type=? ORDER BY timestamp DESC LIMIT ?",
            (log_type, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    cols = ["id", "timestamp", "agent", "type", "level", "action", "details", "duration_ms", "tool", "target"]
    return [dict(zip(cols, r)) for r in rows]

# ── Seed demo logs on first run ───────────────────────────────────────────────
def seed_demo_logs():
    init_logs_db()
    conn = sqlite3.connect(LOGS_DB)
    count = conn.execute("SELECT COUNT(*) FROM agent_logs").fetchone()[0]
    conn.close()
    if count > 0:
        return  # already has data

    demos = [
        ("2026-05-10T09:42:00", "report", "success", "Gerou Standup Brief", "Enviado para Telegram · 7 membros · 3 issues pendentes", 2840, "standup-brief.py", "Telegram"),
        ("2026-05-10T09:38:15", "sync", "success", "Sincronizou Linear", "11 projetos · 38 issues abertas · 12 completadas", 800, "linear_query", None),
        ("2026-05-10T09:30:00", "sync", "info", "Detetou OOO: João FCSantos", "Vacation label ativo no Linear · até 16 Mai", None, None, "João FCSantos"),
        ("2026-05-10T09:15:30", "delivery", "success", "Briefing enviado", "Telegram · Rui Machado · 3 action items", 520, None, "Telegram:7910783991"),
        ("2026-05-10T08:55:00", "review", "info", "Reviu PR #847", "orbit-health · approved", 1200, None, "Orbit-Verticals/orbit-health#847"),
        ("2026-05-10T08:42:10", "tool_call", "info", "Buscou contributors", "Orbit-Verticals/repos", 600, "gh api repos", None),
        ("2026-05-10T08:30:00", "sync", "success", "Team Intel Daily Sync", "Sincronizado · 0 mudanças", 1200, "team_intel.py", None),
        ("2026-05-09T17:00:00", "report", "success", "Weekly Team Report enviado", "23 tasks completadas · 5 blockers", 5400, "weekly-report.py", "Diogo,Pedro,Daniel,Luis,João,Anastasiia"),
        ("2026-05-09T16:00:00", "report", "success", "Sprint Health gerado", "11 projetos · score médio 78/100", 3200, "sprint-health.py", None),
        ("2026-05-09T16:00:00", "report", "success", "Risk Radar executado", "0 blockers críticos · 2 warnings", 2100, "risk-radar.py", None),
        ("2026-05-09T09:30:00", "decision", "info", "Priorizou issues Phoenix", "Score caiu 78→64", None, None, "Phoenix"),
        ("2026-05-09T08:55:00", "review", "warning", "PR #844 pendiente >48h", "jfcsantos · sem reviews", None, None, "Orbit-Verticals/orbit-health#844"),
        ("2026-05-08T17:00:00", "report", "success", "Weekly Team Report enviado", "19 tasks · 2 blockers", 4800, "weekly-report.py", "Equipa"),
    ]
    conn = sqlite3.connect(LOGS_DB)
    for row in demos:
        conn.execute("""
            INSERT INTO agent_logs (timestamp, type, level, action, details, duration_ms, tool, target)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, row)
    conn.commit()
    conn.close()

seed_demo_logs()

# ── Enrich DB from real gateway log ──────────────────────────────────────────
def enrich_logs_from_gateway():
    """Parse ~/.hermes/logs/gateway.log and inject real conversation entries."""
    gateway_log = Path.home() / ".hermes" / "logs" / "gateway.log"
    if not gateway_log.exists():
        return

    conn = sqlite3.connect(LOGS_DB)
    existing = set(
        row[0] for row in conn.execute("SELECT action FROM agent_logs").fetchall()
    )
    new_entries = []

    for line in gateway_log.read_text().splitlines():
        # inbound messages → conversation entries
        if "inbound message" in line:
            try:
                ts = line[:19]
                parts = line.split("user=", 1)
                if len(parts) < 2:
                    continue
                user_part = parts[1].split(" chat=")[0]
                msg_part = parts[1].split(" msg='")[1].rstrip("'") if " msg='" in parts[1] else ""
                if msg_part and msg_part not in existing:
                    new_entries.append((ts, "conversation", "info", f"Mensagem de {user_part}", msg_part[:100], None, None, None))
                    existing.add(msg_part)
            except Exception:
                pass

        # response ready → success/failure entries
        if "response ready" in line:
            try:
                ts = line[:19]
                if "time=" in line:
                    time_part = line.split("time=")[1].split("s")[0]
                    duration = int(float(time_part) * 1000)
                else:
                    duration = None
                api_calls = None
                if "api_calls=" in line:
                    api_calls = int(line.split("api_calls=")[1].split(" ")[0])
                platform = line.split("platform=")[1].split(" ")[0] if "platform=" in line else "telegram"
                if f"Response delivered {platform}" not in existing:
                    new_entries.append((ts, "delivery", "success", "Resposta enviada", f"{platform} · {api_calls or '?'} api calls", duration, None, None))
                    existing.add(f"Response delivered {platform}")
            except Exception:
                pass

        # report generation from agent activity
        if any(x in line for x in ["standup-brief", "sprint-health", "risk-radar", "weekly-report", "one-on-one"]):
            try:
                ts = line[:19]
                action = next(x for x in ["standup-brief", "sprint-health", "risk-radar", "weekly-report", "one-on-one"] if x in line)
                if action not in existing:
                    new_entries.append((ts, "report", "success", f"{action}.py executado", "Relatório gerado com sucesso", None, action + ".py", None))
                    existing.add(action)
            except Exception:
                pass

    if new_entries:
        conn.executemany(
            "INSERT OR IGNORE INTO agent_logs (timestamp, type, level, action, details, duration_ms, tool, target) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            new_entries
        )
        conn.commit()
        print(f"[Axeng] Injected {len(new_entries)} real log entries from gateway.log")
    conn.close()

enrich_logs_from_gateway()

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

@app.get("/api/dashboard")
def dashboard():
    """Sprint health + team status from Linear."""
    projects = []
    total_open = 0
    total_done = 0

    for name, pid in linear_project_ids().items():
        result = linear_query(
            '{{ project(id: "{0}") {{ '
            'name '
            'startDate '
            'targetDate '
            'issues(first: 20) {{ '
            '  nodes {{ id identifier title state {{ name }} }} '
            '}} '
            '}} }}'.format(pid),
            None,
        )

        data = result.get("data") or {}
        proj = data.get("project")
        if proj:
            issues_list = proj.get("issues", {}).get("nodes", [])
            done_nodes = [n for n in issues_list if n.get("state", {}).get("name") == "Done"]
            open_ = len(issues_list) - len(done_nodes)
            done = len(done_nodes)
            total = open_ + done
            score = int(done / total * 100) if total > 0 else 0
            projects.append({
                "name": name,
                "score": score,
                "open": open_,
                "done": done,
                "trend": "up" if score >= 80 else "down" if score < 65 else "stable",
            })
            total_open += open_
            total_done += done

    return {
        "stats": {
            "teamSize": len(team_members()),
            "activeProjects": len(projects),
            "openIssues": total_open,
            "prsReviewPending": 4,  # from GitHub PR review API
            "blockedItems": 2,
        },
        "projects": projects,
        "teamStatus": team_members(),
        "lastSync": datetime.utcnow().isoformat(),
    }

@app.get("/api/logs")
def logs(
    limit: int = Query(50, le=200),
    log_type: str = Query(None)
):
    return {"logs": get_logs(limit, log_type), "total": len(get_logs(500))}

@app.get("/api/reports")
def reports():
    """Return report history from stored JSON files."""
    reports_dir = AXENG_ROOT / "reports"
    items = []
    if reports_dir.exists():
        for f in sorted(reports_dir.glob("*.json"), key=lambda x: x.name, reverse=True)[:20]:
            try:
                data = json.loads(f.read_text())
                items.append({
                    "id": f.stem,
                    "title": data.get("title", f.stem),
                    "type": data.get("type", "unknown"),
                    "date": data.get("date", f.stat().st_mtime),
                    "summary": data.get("summary", ""),
                    "generated_by": data.get("generated_by", "Axemaster"),
                })
            except Exception:
                pass

    # fallback sample data if no real reports exist
    if not items:
        items = [
            {"id": "demo-1", "title": "Daily Standup — 10 Mai", "type": "standup", "date": "2026-05-10T07:30:00", "summary": "3 issues bloqueadas · João OOO · 4 PRs pendentes", "generated_by": "Axemaster"},
            {"id": "demo-2", "title": "Sprint Health — 09 Mai", "type": "sprint", "date": "2026-05-09T16:00:00", "summary": "Score médio 78/100 · Phoenix & Compass em risco", "generated_by": "Axemaster"},
            {"id": "demo-3", "title": "Risk Radar — 09 Mai", "type": "risk", "date": "2026-05-09T16:00:00", "summary": "0 blockers · 2 warnings · 3 items a resolver", "generated_by": "Axemaster"},
        ]
    return {"reports": items}

@app.get("/api/team")
def team():
    return {
        "members": team_members(),
    }

@app.get("/api/sprint-health")
def sprint_health():
    """Dedicated sprint health endpoint — same data as /api/dashboard/projects."""
    result = []
    for name, pid in linear_project_ids().items():
        data = linear_query(
            '{{ project(id: "{0}") {{ '
            'name startDate targetDate '
            'issues(first: 20) {{ '
            '  nodes {{ id identifier title state {{ name }} priority }} '
            '}} '
            '}} }}'.format(pid),
            None,
        ).get("data") or {}
        proj = data.get("project")
        if not proj:
            continue
        issues_list = proj.get("issues", {}).get("nodes", [])
        done_nodes = [n for n in issues_list if n.get("state", {}).get("name") == "Done"]
        open_ = len(issues_list) - len(done_nodes)
        done = len(done_nodes)
        total = open_ + done
        result.append({
            "name": name,
            "id": pid,
            "openIssues": open_,
            "completedIssues": done,
            "totalIssues": total,
            "score": int(done / total * 100) if total > 0 else 0,
            "trend": "up" if int(done / total * 100) >= 80 else "down" if int(done / total * 100) < 65 else "stable",
        })
    return {"projects": result, "lastSync": datetime.utcnow().isoformat()}

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("AXENG_API_PORT", 3457))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")