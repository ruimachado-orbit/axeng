# Axeng — Engineering Manager Accelerator 🤖

**Autonomous engineering intelligence agent** — monitors GitHub, Linear, and team activity, generates daily briefs, and keeps your Obsidian vault in sync.

Built for engineering leaders who want to know what's shipping, who's blocked, and where the roadmap stands — without asking.

---

## Features

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

### 🧠 Query Engine
- "Who's been touching the backend repo this week?"
- "Show me the last PRs from João"
- "What blockers do we have in Linear?"

### 🔧 Linear Integration
- Sync issues, post weekly updates to projects
- Idempotent writes — running the report twice produces one clean update

### 📈 Sprint Health (Friday 16:00)
- Per-project health score (0–100) with deductions for stale, at-risk, silent
- Burn rate: closed vs. active issues
- Scope creep detection: issues added mid-sprint
- Stale issue list across all projects

### 🔭 Risk Radar (Friday 16:00)
- Quiet repos: no commits in 10+ days
- Stalled projects: >3 in-progress with no update in 5+ days
- Overloaded members: 5+ open issues, <2 completed in 14d
- Overdue issues: past due date
- Orphaned PRs: open >7 days, no reviewers assigned

---

## Quick Start
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your team, repos, and credentials
```

### 3. Run

```bash
python src/weekly_report.py
```

Add a cron job (recommended):

```bash
# Every Friday at 17:00 Lisbon
0 17 * * 5 cd /path/to/team-intel && python src/weekly_report.py >> /var/log/team-intel.log 2>&1
```

---

## Configuration

All settings live in `config/config.yaml`. The agent reads:

| Field | What it does |
|---|---|
| `github.orgs` | GitHub orgs to monitor |
| `github.repos` | Specific repos to include |
| `linear.workspace` | Linear workspace name |
| `linear.project_ids` | Map project names to Linear IDs |
| `team` | Team members + GitHub handles |
| `email.recipients` | Who gets the weekly report |
| `email.from` | Sender address |

---

## Architecture

```
team-intel/
├── config/
│   └── config.yaml.example    # Configuration (copy to config.yaml)
├── src/
│   ├── config.py              # Config loader
│   ├── weekly_report.py       # Weekly report + Linear updates (main entry)
│   ├── standup-brief.py       # Daily standup brief (07:30 Mon-Fri)
│   ├── one-on-one-pre-read.py # 1:1 pre-read generator
│   ├── sprint-health.py       # Sprint health scores (Friday)
│   ├── risk-radar.py          # Risk radar scan (Friday)
│   ├── team_sync.py           # Daily sync engine → Obsidian
│   ├── orchestrator.py         # Natural language query router
│   ├── tools/
│   │   ├── github_activity.py  # GitHub data fetcher
│   │   ├── linear_tool.py     # Linear API client
│   │   ├── calendar_insights.py
│   │   └── team_query.py      # Obsidian vault queries
│   └── project_map.py          # Linear ↔ GitHub repo mapping
├── reports/                    # Generated HTML reports
├── tests/
│   └── test_weekly_report.py
├── README.md
├── requirements.txt
├── setup.sh                    # Interactive setup script
└── CONTRIBUTING.md
```

---

## Requirements

- Python 3.11+
- `gh` CLI (GitHub auth: `gh auth login`)
- GitHub API token (via `gh auth` or `GITHUB_TOKEN` env var)
- Linear API key (`LINEAR_API_KEY` env var or `config.yaml`)
- Optional: Obsidian vault for daily sync

---

## License

MIT