# Axeng — Engineering Manager Accelerator 🤖

**Stop managing. Start shipping.**

Autonomous AI chief of staff that monitors GitHub, Linear, your calendar, and team — automatically generates standups, 1:1 pre-reads, sprint reports, risk alerts, team sync, and offboarding.

> Runs 24/7 on a $200 Mac Mini. Built by a CTO who was tired of manually chasing status updates.

---

## ⚡ Install in 2 Minutes

### Option A — Git Clone (fastest)

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng

# 1. Configure
cp .env.example .env         # ← fill in your API keys (see section below)
cp config/config.yaml.example config/config.yaml  # ← fill in your orgs/team

# 2. Start
docker compose -f docker/docker-compose.yml up -d

# 3. Open
open http://localhost:8501
```

### Option B — Homebrew

```bash
brew install ruimachado-orbit/axeng/axeng
cp $(brew --prefix)/opt/axeng/.env.example $(brew --prefix)/opt/axeng/.env
# Edit .env with your API keys, then:
axeng
open http://localhost:8501
```

---

## ✅ Prerequisites

| What | Why | Where to get it |
|------|-----|-----------------|
| **Docker** | Runs the agent container | [docker.com](https://docs.docker.com/get-docker/) |
| **LLM API key** | Generates all reports | [Anthropic](https://console.anthropic.com/) (Claude) or [OpenAI](https://platform.openai.com/) (GPT-4o) |
| **GitHub token** | Reads orgs, repos, PRs | `gh auth login` OR [github.com/settings/tokens](https://github.com/settings/tokens) |
| **Linear API key** | Reads/writes issues + projects | [linear.app/settings/api](https://linear.app/settings/api) |
| **Telegram bot** *(optional)* | Receives daily briefings | Talk to [@BotFather](https://t.me/BotFather) on Telegram |
| **Google Calendar** *(optional)* | Detects OOO, 1:1 meetings | [Google Cloud Console](https://console.cloud.google.com/) |
| **Obsidian vault** *(optional)* | Stores 1:1 notes + team memory | [obsidian.md](https://obsidian.md/) |

**That's it.** No server, no cloud account, no monthly fee. Everything runs on your own machine.

---

## 🔑 Setting Up Your API Keys

Edit the `.env` file in the axeng directory:

```bash
# === REQUIRED ===

# LLM — pick one (Claude recommended)
ANTHROPIC_API_KEY=sk-ant-...      # anthropic.com — get from Console

# GitHub — option A: token
GITHUB_TOKEN=ghp_...
# OR option B: CLI auth (no token needed)
# Run: gh auth login

# Linear — get from linear.app/settings/api
LINEAR_API_KEY=lin_...

# === OPTIONAL ===

# Telegram (for briefings)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Google Calendar (for OOO + 1:1 detection)
GOOGLE_CLIENT_SECRET=~/.hermes/google_client_secret.json
GOOGLE_TOKEN_PATH=~/.hermes/google_token.json

# World news in daily briefings
NEWS_API_KEY=

# Obsidian vault (for 1:1 notes + team sync)
OBSIDIAN_VAULT_PATH=~/Documents/Obsidian\ Vault
```

---

## ⚙️ Configuring Teams & Projects

Edit `config/config.yaml`:

```yaml
github:
  orgs: ["my-company"]                    # your GitHub org(s)
  name_map:                                # GitHub login → friendly name
    "johndoe": "John Doe"
    "janedev": "Jane Developer"
  ex_members: []                           # bots, ex-employees (exclude from reports)

linear:
  project_ids:                            # project name → Linear ID
    "Frontend":     "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    "Backend":      "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    "Infrastructure": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  projects:
    "Frontend":
      repos: ["my-company/web-app", "my-company/shared-ui"]
      owner: "John Doe"
    "Backend":
      repos: ["my-company/api", "my-company/workers"]
      owner: "Jane Developer"

email:
  recipients: ["engineering@mycompany.com"]
  from: "axeng@mycompany.com"
  gmail_script: "~/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
```

---

## 🎯 All Features

### 🏃 Daily Standup Brief (Mon–Fri 07:30)
What shipped yesterday, who's blocked, PRs waiting >48h, who's OOO → **sent to Telegram**

### 📋 1:1 Pre-reads (auto before every meeting)
对方的 open issues, their commits, pending PRs, last 1:1 notes → **ready before you walk in**

### 📊 Weekly Team Report (Friday 17:00)
Per-project status, MVP podium, commit breakdown, roadmap analysis → **posted to Linear + email**

### 📈 Sprint Health (Friday 16:00)
Health scores (0–100) per project — velocity, scope creep, stale issues, overdue

### 🔭 Risk Radar (Friday 16:00)
Quiet repos, overloaded members, orphaned PRs, stalled projects → **proactive alerts**

### 🔄 Team Sync (daily)
GitHub activity → Obsidian vault → your personal knowledge base stays fresh

### 🧳 Vacation Tracker
Team vacations as Linear issues — `add_vacation`, `list_vacations`, `delete_vacation`

### 🛡️ Offboarding (on-demand)
```bash
# Preview what will be removed
python3 src/tools/offboarding.py <github_login> --dry-run

# Execute — removes from all GitHub orgs + Linear workspace
python3 src/tools/offboarding.py <github_login>
```

---

## 🖥️ Web Dashboard

At `http://localhost:8501` — Streamlit UI with:
- Report history (standups, weekly reports, sprint health)
- Team overview (commits, issues, PR activity)
- Manual report triggers (run any report on demand)
- Config editor (update teams/projects without editing YAML manually)

---

## 🔐 Your Keys Stay With You

- All credentials in `.env` — **never committed to git**
- `.env` and `config/config.yaml` are gitignored
- API keys never leave your machine (fully self-hosted)
- Works offline once configured

---

## 🐳 Docker Commands

```bash
axeng           # Start (docker compose up -d)
axeng-stop      # Stop (docker compose down)
axeng-logs      # Live logs (docker compose logs -f)
axeng-update    # Pull latest + rebuild + restart
```

Or directly with Docker:
```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml logs -f
docker compose -f docker/docker-compose.yml down
```

---

## 🏗️ Two Running Modes

### Standalone (default)
Axeng has its own `.env` and `config/config.yaml`. No Hermes needed. Everything is self-contained in the axeng directory.

### Integrated with Hermes (for Axemaster users)
If you already have Hermes running at `~/.hermes`, the docker-compose mounts your `~/.hermes` into the container. Axeng reuses your existing Google tokens, Linear credentials, and Obsidian vault — no duplicate config needed.

```bash
# Link axeng commands system-wide
ln -sf $(pwd)/bin/axeng-start /usr/local/bin/axeng
ln -sf $(pwd)/bin/axeng-stop  /usr/local/bin/axeng-stop
ln -sf $(pwd)/bin/axeng-logs  /usr/local/bin/axeng-logs
ln -sf $(pwd)/bin/axeng-update /usr/local/bin/axeng-update
```

---

## ❓ FAQ

**Q: Does this need an expensive server?**
A: No. Runs on any machine with Docker — including a $200 Mac Mini M1. That's how it was built.

**Q: Is this a SaaS product? Do I pay a subscription?**
A: No. Self-hosted. You only pay for your LLM API calls (~$0.02–0.10/day at Claude rates).

**Q: How is this different from Hermes/Axemaster?**
A: Axemaster is the AI agent itself (what you talk to). Axeng is a set of automated report scripts that run on a schedule — standups, weekly reports, sprint health. They can run independently or together.

**Q: Can I run it without Docker?**
A: Yes — `pip install -r requirements.txt` + `streamlit run ui/app.py`. The Docker path is the easiest and most reproducible.

**Q: How do I get the Linear project ID?**
A: Open the project in Linear. The ID is the last part of the URL:
`app.linear.app/workspace/PROJECT_SLUG/PROJECT_ID` → copy the ID at the end.

**Q: Can I add custom reports?**
A: Yes. Add a new Python script in `src/`, wire it to a cron job in `~/.hermes/scripts/`, done.

**Q: Does it work on Linux/Windows?**
A: Yes — Docker works on both. Homebrew works on macOS and Linux.

---

## 📁 Project Structure

```
axeng/
├── bin/
│   ├── axeng-start    # docker compose up -d
│   ├── axeng-stop     # docker compose down
│   ├── axeng-logs     # docker compose logs -f
│   └── axeng-update   # git pull + rebuild + restart
├── src/
│   ├── standup-brief.py     # Daily brief (07:30 Mon–Fri)
│   ├── one-on-one-pre-read.py
│   ├── sprint-health.py      # Sprint health (Fri 16:00)
│   ├── risk-radar.py         # Risk radar (Fri 16:00)
│   ├── team_sync.py          # GitHub → Obsidian sync
│   ├── orchestrator.py       # NL query router
│   ├── project_map.py        # Linear ↔ GitHub mapping
│   └── tools/
│       ├── linear_tool.py
│       ├── github_activity.py
│       ├── calendar_insights.py
│       ├── team_query.py
│       ├── offboarding.py    # 🛡️ Offboarding tool
│       └── linear_vacations.sh
├── ui/
│   └── app.py          # Streamlit dashboard (port 8501)
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   └── config.yaml.example
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🎤 For Conference Talks

Keynote slides available at [github.com/ruimachado-orbit/axeng/releases](https://github.com/ruimachado-orbit/axeng/releases):
- `axeng-keynote-combined.pptx` — 13-slide full deck (5 intro + 8 tech)
- `axeng-keynote-tech.pptx` — 8 technical slides only

---

## 🤝 Contributing

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng
cp .env.example .env && cp config/config.yaml.example config/config.yaml
streamlit run ui/app.py  # run locally
git checkout -b feat/your-feature && git push && open PR
```

---

## 📄 License

MIT — use it, fork it, build on it. No strings attached.