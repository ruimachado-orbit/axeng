# Axeng — Engineering Manager Accelerator 🤖

**Stop managing. Start shipping.**

Axeng is an open-source autonomous agent that acts as your AI chief of staff — monitors GitHub, Linear, your calendar, and team, then automatically generates standups, 1:1 pre-reads, sprint reports, risk alerts, team sync, and offboarding.

> Built by a CTO who was tired of manually chasing status updates. Now runs 24/7 on a $200 Mac Mini.

---

## ⚡ One-Command Setup

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng
cp .env.example .env    # fill in your API keys
cp config/config.yaml.example config/config.yaml
docker compose up      # open http://localhost:8501
```

That's it. 3 commands, 2 minutes, and you have a running system.

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
- Roadmap contribution analysis per repo

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
- Linear issues with due dates in the past

### 🔄 Team Sync (daily, configurable)
GitHub activity → Obsidian vault, keeping your personal knowledge base up to date automatically
- Fetches commits, PRs, and issue activity per team member
- Writes structured notes to Obsidian per team member
- Tracks last sync timestamp to avoid duplicates

### 🧳 Vacation Tracker (ongoing)
Team vacation calendar managed via Linear issues with the Vacation label
- `add_vacation <name> <start> <end> [note]` — create a vacation issue
- `update_vacation <issue_id> <start> <end> [note]` — update dates
- `delete_vacation <issue_id>` — remove vacation
- `list_vacations` — show upcoming vacations
- Weekly digest posted to Linear every Monday

### 🛡️ Offboarding (on-demand, any time)
Remove a collaborator's access from all GitHub orgs AND Linear workspace in one command
```bash
python3 src/tools/offboarding.py <github_login>          # real execution
python3 src/tools/offboarding.py <github_login> --dry-run  # preview first
python3 src/tools/offboarding.py <github_login> --skip-linear  # GitHub only
```
- Scans all GitHub orgs (except excluded: `mynort`, `remynd`, `my-north-ai`, `remynd-me`)
- Removes collaborator from every repo where they appear
- Cancels pending repository invitations
- Finds the user in Linear by email/name + archives them + removes from all teams

---

## 🖥️ Web UI (Streamlit)

```
streamlit run ui/app.py
# → http://localhost:8501
```

Dashboard with session history, team overview, report viewer, manual report triggers, and config editor.

---

## 🔐 Your Keys Stay With You

- All credentials in `.env` — **never committed to git**
- `.env` is in `.gitignore` by default
- API keys never leave your machine (self-hosted)
- Works fully offline once configured

---

## ⚙️ What You Need to Configure

```yaml
# config/config.yaml — takes 10 minutes to set up
github:
  orgs: ["your-org"]
linear:
  projects:
    "My Project":
      repos: ["your-org/frontend"]
      owner: "John Doe"
email:
  recipients: ["manager@company.com"]
team:
  - name: "John Doe"
    github: "johndoe"
    email: "john@company.com"
```

---

## 📁 Project Structure

```
axeng/
├── .env.example              ← copy to .env (gitignored!)
├── config/
│   └── config.yaml.example  ← copy to config.yaml
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
│   ├── standup-brief.py     ← daily brief
│   ├── one-on-one-pre-read.py
│   ├── weekly_report.py     ← team report
│   ├── sprint-health.py
│   ├── risk-radar.py
│   ├── team_sync.py
│   ├── orchestrator.py
│   └── tools/               ← Linear, GitHub, Calendar integrations
├── ui/
│   └── app.py               ← Streamlit dashboard
├── LICENSE                  ← MIT
├── CONTRIBUTING.md
└── README.md
```

---

## 🐳 Docker

```bash
# Start (background)
docker compose up -d

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose build && docker compose up -d

# Stop
docker compose down
```

---

## 🔧 Requirements

- Python 3.11+
- [GitHub CLI](https://cli.github.com/) (`gh auth login`) or `GITHUB_TOKEN`
- [Linear](https://linear.app) API key
- An LLM API key (Anthropic Claude, OpenAI GPT-4, Google Gemini, Groq — any)

---

## 🎤 For Conference Talks / Keynotes

See the [release assets](https://github.com/ruimachado-orbit/axeng/releases) for keynote slides:
- `axeng-keynote-combined.pptx` — full 13-slide deck (5 intro + 8 tech deep-dive)
- `axeng-keynote-tech.pptx` — 8 technical slides only

---

## 🤝 Contributing

1. Fork it
2. Create your branch: `git checkout -b feat/your-feature`
3. Run it locally (`streamlit run ui/app.py`)
4. Open a PR — see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

---

## 📄 License

MIT — use it, fork it, build on it. No strings attached.