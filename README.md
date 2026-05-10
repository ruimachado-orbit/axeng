# Axeng — Engineering Manager Accelerator 🤖

**Stop managing. Start shipping.**

Autonomous AI chief of staff that monitors GitHub, Linear, your calendar, and team — then automatically generates standups, 1:1 pre-reads, sprint reports, risk alerts, team sync, and offboarding.

> Runs 24/7 on a $200 Mac Mini. Built by a CTO who was tired of manually chasing status updates.

---

## 🏗️ Two Ways to Run

### Option A — Standalone (Docker only) ← **Recommended for most users**

Axeng runs as a Docker container with its own config. No Hermes needed.

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng

# 1. Configure
cp .env.example .env        # fill in your API keys (see below)
cp config/config.yaml.example config/config.yaml  # fill in your orgs/team

# 2. Start
docker compose -f docker/docker-compose.yml up -d

# 3. Open browser → http://localhost:8501
```

**Homebrew shortcut:**
```bash
brew install ruimachado-orbit/axeng/axeng
# Then manually copy .env + config.yaml and run:
axeng
```

---

### Option B — Integrated with Hermes (for Axemaster users)

Axeng runs as a layer on top of your existing Hermes setup — leverages Hermes' Google Workspace, Calendar, and Obsidian integrations.

**Prerequisites:**
- ✅ Hermes already installed and running (`~/.hermes`)
- ✅ Docker
- ✅ API keys in `~/.hermes/.env`
- ✅ GitHub CLI authenticated (`gh auth login`)
- ✅ Linear API key in `~/.hermes/.env`
- ✅ Google Workspace credentials (`~/.hermes/google_token.json`)

**Setup:**
```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng

# Create a symbolic link so axeng commands are available system-wide
ln -sf "$(pwd)/bin/axeng-start" /usr/local/bin/axeng  # macOS default path
ln -sf "$(pwd)/bin/axeng-stop" /usr/local/bin/axeng-stop
ln -sf "$(pwd)/bin/axeng-logs" /usr/local/bin/axeng-logs
ln -sf "$(pwd)/bin/axeng-update" /usr/local/bin/axeng-update

# Axeng will pick up your .env and Google tokens from ~/.hermes automatically
axeng
```

The docker-compose mounts your `~/.hermes` so the tools inside the container can use the same credentials as your main Hermes agent.

---

## 🔑 Required API Keys

### For Option A (Standalone)
Create `~/.env` with:
```bash
# LLM — pick one
ANTHROPIC_API_KEY=sk-ant-...      # Claude
# OR
OPENAI_API_KEY=sk-...             # GPT-4o

# GitHub
GITHUB_TOKEN=ghp_...              # from github.com/settings/tokens

# Linear
LINEAR_API_KEY=lin_...            # from linear.app/settings/api

# Optional
GOOGLE_API_KEY=...                # for Google Calendar integration
TELEGRAM_BOT_TOKEN=...            # for Telegram notifications
NEWS_API_KEY=...                  # for world news in briefings
```

### For Option B (Hermes Integrated)
Your `~/.hermes/.env` already has most of these. Axeng will read from there.

---

## ⚙️ Configuration

Edit `config/config.yaml`:

```yaml
github:
  orgs: ["your-org"]                    # your GitHub org(s)
  name_map:                             # GitHub login → display name
    "johndoe": "John Doe"
  ex_members: []                        # exclude from reports (ex-employees, bots)

linear:
  project_ids:                          # Linear project name → ID
    "Project Alpha": "xxxxxxxx-xxxx..."
  projects:                             # Linear project → GitHub repos → owner
    "Project Alpha":
      repos: ["your-org/frontend"]
      owner: "John Doe"

email:
  recipients: ["team@example.com"]
  from: "team@example.com"
  gmail_script: "~/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
```

---

## 🎯 All Features

### 🏃 Daily Standup Brief (Mon–Fri 07:30)
What shipped yesterday, who's blocked, PRs waiting >48h, who's OOO → **sent to Telegram**
- Fetches yesterday's commits across all GitHub orgs
- Detects stale PRs (open >48h without review)
- Pulls unassigned/low-priority issues from Linear
- Checks Google Calendar for OOO events today

### 📋 1:1 Pre-reads (auto before every meeting)
The other person's open issues, their commits this week, pending PRs, last 1:1 notes from Obsidian → **ready before you walk in**
- Identifies 1:1 meetings from your Google Calendar
- Fetches their GitHub commits and Linear activity
- Reads past 1:1 notes from Obsidian vault
- Generates suggested talking points

### 📊 Weekly Team Report (Friday 17:00)
Per-project status, MVP of the week (scored), commit breakdown, roadmap analysis → **posted to Linear + email**
- Covers Sat–Fri week
- MVP podium (top 3 contributors by impact + commits)
- Per-project card: activity, issues opened/closed, owner

### 📈 Sprint Health (Friday 16:00)
Health scores (0–100) per project — velocity, scope creep, stale issues, overdue → **flagged before it becomes a crisis**
- Velocity vs. last sprint (issues completed)
- Scope creep: issues added mid-sprint
- At-risk items: no updates in 5+ days
- Burn chart estimate (open vs. closed)

### 🔭 Risk Radar (Friday 16:00)
Quiet repos, overloaded members, orphaned PRs, stalled projects → **proactive, not reactive**
- Repos with no commits in 10+ days
- Linear projects with >3 in-progress issues and no movement
- Team members with >5 open issues and low throughput
- PRs open >7 days with no review requests

### 🔄 Team Sync (daily)
GitHub activity → Obsidian vault, keeping your personal knowledge base up to date

### 🧳 Vacation Tracker (ongoing)
Team vacation calendar managed via Linear issues with the Vacation label

### 🛡️ Offboarding (on-demand)
```bash
python3 src/tools/offboarding.py <github_login> --dry-run  # preview
python3 src/tools/offboarding.py <github_login>            # execute
```

---

## 🖥️ Web UI

Streamlit dashboard at `http://localhost:8501` — session history, team overview, report viewer, manual triggers, config editor.

---

## 🔐 Your Keys Stay With You

- All credentials in `.env` — **never committed to git**
- `.env` is in `.gitignore` by default
- API keys never leave your machine (self-hosted)

---

## 📁 Project Structure

```
axeng/
├── bin/                    # Convenience scripts (axeng-start/stop/logs/update)
│   ├── axeng-start
│   ├── axeng-stop
│   ├── axeng-logs
│   └── axeng-update
├── src/
│   ├── standup-brief.py    # Daily brief (07:30 Mon–Fri)
│   ├── one-on-one-pre-read.py
│   ├── sprint-health.py
│   ├── risk-radar.py
│   ├── team_sync.py
│   ├── orchestrator.py
│   └── tools/              # Linear, GitHub, Calendar, Offboarding
├── ui/
│   └── app.py              # Streamlit dashboard (port 8501)
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   └── config.yaml.example
├── .env.example
└── README.md
```

---

## 🐳 Docker Commands

```bash
axeng          # Start (docker compose up -d)
axeng-stop     # Stop (docker compose down)
axeng-logs     # View live logs (docker compose logs -f)
axeng-update   # Pull latest + rebuild + restart
```

---

## 🎤 Conference Talks

Keynote slides at [github.com/ruimachado-orbit/axeng/releases](https://github.com/ruimachado-orbit/axeng/releases):
- `axeng-keynote-combined.pptx` — 13-slide full deck
- `axeng-keynote-tech.pptx` — 8 technical slides only

---

## 🤝 Contributing

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng
cp .env.example .env && cp config/config.yaml.example config/config.yaml
streamlit run ui/app.py  # develop locally
git checkout -b feat/your-feature
# open PR
```

---

## 📄 License

MIT — use it, fork it, build on it.