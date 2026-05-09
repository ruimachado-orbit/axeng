# Team Intel Agent 🤖

**Autonomous engineering intelligence agent** — monitors GitHub, Linear, and team activity, generates weekly reports, and syncs to Obsidian.

Built for engineering leaders who want to know what's shipping, who's blocked, and where the roadmap stands — without asking.

---

## Features

- 📊 **Weekly Team Report** — HTML email every Friday with:
  - Per-project roadmap status (from Linear)
  - MVP of the week (F1 podium scoring)
  - Per-person commit breakdown with estimated hours
  - Roadmap contribution analysis
  - Business summary per Linear project

- 🔄 **Daily Sync** — fetches GitHub activity → stores in Obsidian vault
- 🧠 **Query Engine** — ask questions about your team in natural language:
  - "Who's been touching the backend repo this week?"
  - "Show me the last PRs from João"
  - "What blockers do we have in Linear?"
- 📋 **Linear Integration** — sync issues, post weekly updates to projects
- 🤖 **Idempotent writes** — running the report twice produces one clean update

---

## Quick Start

### 1. Clone / install

```bash
git clone https://github.com/ruimachado-orbit/team-intel.git
cd team-intel
pip install -r requirements.txt
```

### 2. Configure

```bash
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