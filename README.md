# Axeng — Engineering Manager Accelerator 🤖

**Open source autonomous engineering intelligence agent** — monitors GitHub, Linear, and team activity, generates daily briefs, and keeps your team in sync.

Built for engineering leaders who want to know what's shipping, who's blocked, and where the roadmap stands — without asking.

---

## ⚡ Quick Start (Docker)

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng

# 1. Copy and fill in your environment variables
cp .env.example .env
nano .env   # add your API keys

# 2. Copy and configure
cp config/config.yaml.example config/config.yaml
nano config/config.yaml   # add your team, repos, Linear project IDs

# 3. Run
docker compose up
```

Open **http://localhost:8501** — you'll see the dashboard and can trigger reports from the UI.

---

## ⚡ Quick Start (Local / Dev)

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng

pip install -r requirements.txt

cp .env.example .env
cp config/config.yaml.example config/config.yaml

streamlit run ui/app.py
```

---

## ✨ Features

### 🏃 Daily Standup Brief (Mon–Fri 07:30)
- What shipped yesterday
- Unassigned / stale Linear issues (blockers)
- PRs waiting >48h for review
- Who's OOO today

### 📋 1:1 Pre-reads (before each 1:1)
-对方的 open Linear issues + priority
- Their commits this week
- Pending PRs awaiting their review
- Last 1:1 notes from Obsidian
- Suggested talking points
- Sprint velocity (14-day)

### 📊 Weekly Team Report (Friday 17:00)
- Per-project roadmap status (from Linear)
- MVP of the week (F1 podium scoring)
- Per-person commit breakdown with estimated hours
- Roadmap contribution analysis
- Business summary posted to each Linear project

### 🔄 Daily Vault Sync
- Fetches GitHub activity → stores in Obsidian vault
- Builds team member profiles over time

### 📈 Sprint Health (Friday 16:00)
- Per-project health score (0–100) with deductions for stale, at-risk, silent
- Burn rate: closed vs. active issues
- Scope creep detection: issues added mid-sprint

### 🔭 Risk Radar (Friday 16:00)
- Quiet repos: no commits in 10+ days
- Stalled projects: >3 in-progress with no update in 5+ days
- Overloaded members: 5+ open issues, <2 completed in 14d
- Overdue issues: past due date
- Orphaned PRs: open >7 days, no reviewers assigned

---

## 🌐 Web UI (Streamlit)

The built-in Streamlit UI provides:

- **📊 Dashboard** — recent sessions, team status, report history
- **⚙️ Configuration** — edit `config.yaml` from the browser
- **📋 Reports** — view generated HTML reports
- **👥 Team** — team member cards and project map
- **🔧 Run Reports** — trigger any report on-demand

```
streamlit run ui/app.py   # starts at http://localhost:8501
```

---

## 🔐 Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key (or use `OPENAI_API_KEY`, etc.) |
| `GITHUB_TOKEN` | GitHub PAT (or use `gh auth login`) |
| `LINEAR_API_KEY` | Linear API key |
| `GOOGLE_API_KEY` | For Gmail/Calendar |
| `NEWS_API_KEY` | For world news in daily briefing |
| `TELEGRAM_BOT_TOKEN` | For bot notifications |

> **Never commit `.env`** — it's in `.gitignore`. Use `.env.example` as the template.

---

## ⚙️ Configuration

All settings in `config/config.yaml`:

| Section | What it does |
|---------|--------------|
| `email.recipients` | Who gets the weekly report |
| `github.orgs` | GitHub orgs to scan |
| `linear.projects` | Map project names → repos + owner |
| `team` | Team members + GitHub handles |
| `reporting` | Weekday, timezone, output dir |

---

## 📁 Project Structure

```
axeng/
├── .env.example              # ← copy to .env (gitignored!)
├── .gitignore
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   └── config.yaml.example   # ← copy to config.yaml
├── src/
│   ├── config.py
│   ├── weekly_report.py
│   ├── standup-brief.py
│   ├── one-on-one-pre-read.py
│   ├── sprint-health.py
│   ├── risk-radar.py
│   ├── team_sync.py
│   ├── orchestrator.py
│   ├── project_map.py
│   └── tools/
├── ui/
│   └── app.py                # Streamlit web UI
├── vault/                    # (optional) Obsidian vault
├── reports/                  # generated HTML reports
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 🐳 Docker

```bash
# Build
docker compose build

# Run
docker compose up

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

Volume mounts:
- `./config` → `/app/config` (ro)
- `./.env` → `/app/.env` (ro)
- `./vault` → `/app/vault` (optional, Obsidian)
- `./reports` → `/app/reports` (generated output)

---

## ⏰ Scheduling

Run via cron (local) or trigger from the Streamlit UI:

```bash
# Every Friday at 17:00 Lisbon
0 17 * * 5 cd /path/to/axeng && python src/weekly_report.py >> var/log/axeng.log 2>&1

# Daily standup brief
30 7 * * 1-5 cd /path/to/axeng && python src/standup-brief.py >> var/log/axeng.log 2>&1
```

---

## 🔧 Requirements

- Python 3.11+
- `gh` CLI (optional — `gh auth login` for GitHub)
- API keys: Linear, GitHub, (optionally) Anthropic/OpenAI

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Run tests (coming soon)
4. Open a PR

See `CONTRIBUTING.md` for details.

---

## 📄 License

MIT — use it, hack it, ship it.