# Axeng — Engineering Manager Accelerator 🤖

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)

**Stop managing. Start shipping.**

Autonomous AI chief of staff that monitors GitHub, Linear, your calendar, and team — automatically generates standups, 1:1 pre-reads, sprint reports, risk alerts, and team insights.

> Runs 24/7 on a $200 Mac Mini. Built by a CTO who was tired of manually chasing status updates.
>
> **Open source** under GPL-3.0. Free forever, self-hosted, no cloud dependencies.

---

## ⚡ Quick Install

```bash
pip install git+https://github.com/ruimachado-orbit/axeng.git

# Interactive setup wizard
axeng configure

# All commands work in demo mode (no API keys needed!)
axeng standup
axeng status
```

### Or clone for development

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng
pip install -e .
axeng configure
```

---

## 🎭 Demo Mode

Axeng works **immediately after install** — no API keys required. When no credentials are configured, it runs in **demo mode** with realistic mock data:

```
$ axeng standup
╭─ Daily Standup Brief ─────────────────────────────────╮
│                                                        │
│  Yesterday:                                            │
│  • Alice Dev merged "Add user auth" (2 reviews)       │
│  • Bob Chen shipped "API rate limiting"               │
│                                                        │
│  Blocked:                                              │
│  • Charlie Wilson — waiting on design review           │
│                                                        │
│  PRs waiting >48h:                                     │
│  • "Refactor payment flow" — waiting on Bob Chen       │
│                                                        │
│  OOO today:                                            │
│  • Diana Prince (until 2026-05-20)                     │
╰────────────────────────────────────────────────────────╯
```

To use **real data**, set your API keys:

| Variable | Where to get it |
|----------|----------------|
| `LINEAR_API_KEY` | [linear.app/settings/api](https://linear.app/settings/api) |
| `GITHUB_TOKEN` | `gh auth login` or [tokens](https://github.com/settings/tokens) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / etc. | See [LLM Providers](#-llm-providers) |

---

## 📋 Commands

```
Usage: axeng [OPTIONS] COMMAND [ARGS]...

╭─ Core ──────────────────────────────────────────────╮
│ configure   Interactive configuration wizard        │
│ chat        Interactive chat with Axeng             │
│ status      Check all integrations health           │
│ start       Start Axeng service                     │
│ stop        Stop Axeng service                      │
│ logs        View Axeng logs                         │
│ update      Update Axeng to latest version          │
├─────────────────────────────────────────────────────┤
│ ╭─ Daily Operations ──────────────────────────╮     │
│ │ ooo       Who's out of office today         │     │
│ │ standup   Generate daily standup brief      │     │
│ │ issues    Show my Linear issues             │     │
│ │ prs       Show my GitHub pull requests      │     │
│ │ pr-health Analyze PR health & bottlenecks   │     │
│ ├─────────────────────────────────────────────┤     │
│ │ ╭─ Team Management ────────────────────╮   │     │
│ │ │ prep [name]  1:1 meeting prep       │   │     │
│ │ │ team         List teams or details   │   │     │
│ │ │ offboard     Offboarding (dry-run ✓) │   │     │
│ │ ╰──────────────────────────────────────╯   │     │
│ ├─────────────────────────────────────────────┤     │
│ │ ╭─ Analytics ─────────────────────────╮    │     │
│ │ │ sprint     Sprint health & velocity │    │     │
│ │ │ dora       DORA metrics dashboard  │    │     │
│ │ │ report     Generate reports        │    │     │
│ │ ╰──────────────────────────────────────╯    │     │
╰─────────────────────────────────────────────────────╯
```

### Example Workflow

```bash
# Morning routine (saves 20 min/day)
alias morning="axeng ooo && axeng standup && axeng issues"

# Before 1:1 (saves 5 min/meeting)
axeng prep "John Doe"

# End of sprint (saves 15 min)
axeng sprint --velocity
```

---

## ✅ Prerequisites

| What | Why | How |
|------|-----|-----|
| **Python 3.11+** | Runs all Axeng commands | `brew install python@3.12` |
| **LLM API key** | Generates reports & chat | At least one [provider](#-llm-providers) |
| **GitHub token** | Reads repos & PRs | `gh auth login` |
| **Linear API key** | Reads/writes issues | [linear.app/settings/api](https://linear.app/settings/api) |
| **Google Calendar** *(optional)* | OOO + 1:1 detection | [Google Cloud Console](https://console.cloud.google.com/) |
| **News API key** *(optional)* | World news in briefings | [newsapi.org](https://newsapi.org/) |

**That's it.** No Docker, no cloud account, no monthly fee. Everything runs locally.

---

## 🔑 LLM Providers

Axeng supports multiple LLM providers with automatic fallback:

| Provider | Env Variable | Best For |
|----------|-------------|----------|
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | Best quality + speed |
| **OpenAI** | `OPENAI_API_KEY` | o1/o3 reasoning models |
| **OpenRouter** | `OPENROUTER_API_KEY` | Multi-provider aggregation |
| **Groq** | `GROQ_API_KEY` | Fast free inference |
| **Google AI** | `GOOGLE_API_KEY` | Gemini models |
| **Ollama** | _(local)_ | Free local LLMs |
| **LM Studio** | _(local)_ | Free local GGUF models |

```bash
# Set your keys
export ANTHROPIC_API_KEY=sk-ant-...
export LINEAR_API_KEY=lin-...

# Or set provider order
export LLM_PROVIDER_ORDER=ollama,anthropic,openai,groq
```

---

## ⚙️ Configuring Teams & Projects

Edit `config/config.yaml` (created by `axeng configure`):

```yaml
github:
  orgs: ["my-company"]
  name_map:
    "johndoe": "John Doe"

linear:
  project_ids:
    "Frontend": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  projects:
    "Frontend":
      repos: ["my-company/web-app"]
      owner: "John Doe"

email:
  recipients: ["engineering@mycompany.com"]
  from: "axeng@mycompany.com"
```

---

## 📅 Google Workspace Setup (Optional)

### 1. Get OAuth Credentials

1. [Google Cloud Console](https://console.cloud.google.com/) → New project
2. Enable **Google Calendar API** and **Gmail API**
3. Create OAuth 2.0 credentials → **Desktop app**
4. Download JSON

### 2. Authenticate

```bash
mkdir -p ~/.axeng/secrets
mv ~/Downloads/client_secret_*.json ~/.axeng/secrets/google_client_secret.json

# Test authentication
python3 -m axeng.tools.google_api auth test
```

This opens your browser for Google sign-in, then saves the token to `~/.axeng/secrets/google_token.json`.

---

## 🧠 Engineering Manager Behavior

Axeng ships with an **Engineering Manager system prompt** (`prompts/engineering-manager-code-act.md`) that defines its behavior:

- **Evidence-first** — every recommendation cites specific data points
- **Ownership-oriented** — named owners, concrete next actions
- **Delivery-focused** — identifies stale PRs, blocked issues, overloaded contributors
- **Bilingual** — responds in English or Portuguese

The LLM synthesis layer uses this prompt across all commands — standups, 1:1 pre-reads, sprint reports, and chat.

---

## 📁 Project Structure

```
axeng/
├── axeng/                        # Python package
│   ├── cli.py                    # CLI entry point (Typer)
│   ├── config.py                 # Configuration loader
│   ├── llm_gateway.py            # Unified LLM client (8 providers)
│   ├── orchestrator.py           # NL query router + LLM synthesis
│   ├── demo_data.py              # Mock data for demo mode
│   ├── smart_suggestions.py      # Context-aware command suggestions
│   ├── standup-brief.py          # Daily standup generator
│   ├── one-on-one-pre-read.py    # 1:1 meeting pre-read
│   ├── sprint-health.py          # Sprint health analysis
│   ├── risk-radar.py             # Risk alerts
│   ├── team_sync.py              # GitHub activity sync
│   ├── project_map.py            # Linear ↔ GitHub mapping
│   ├── chat-action-items.py      # Chat-to-Linear extraction
│   ├── api_server.py             # FastAPI backend for UI
│   └── tools/
│       ├── linear_tool.py        # Linear API client
│       ├── github_activity.py    # GitHub API client
│       ├── calendar_insights.py  # Google Calendar client
│       ├── google_api.py         # Google OAuth + API
│       ├── granola_tool.py       # Granola meeting notes
│       ├── dora_metrics.py       # DORA metrics
│       ├── team_query.py         # Team membership queries
│       ├── sprint_health.py      # Sprint scoring engine
│       ├── weekly_report.py      # Report generation
│       ├── vacations.py          # Vacation management
│       ├── offboarding.py        # Offboarding (dry-run + exec)
│       └── linear_vacations.sh   # Vacation bash helpers
├── ui/nextjs/                    # Next.js dashboard (port 3000)
├── config/
│   └── config.yaml.example       # Configuration template
├── prompts/
│   └── engineering-manager-code-act.md  # Axeng persona prompt
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── bin/                          # Helper scripts
├── .env.example                  # Environment template
├── pyproject.toml                # Python package config
├── Makefile                      # Dev convenience targets
└── README.md
```

---

## 🐳 Docker

```bash
# Start
docker compose -f docker/docker-compose.yml up -d

# Logs
docker compose -f docker/docker-compose.yml logs -f

# Stop
docker compose -f docker/docker-compose.yml down
```

Or use the built-in helpers:
```bash
axeng start
axeng logs
axeng stop
```

---

## 🔐 Security

- All credentials in `.env` — **never committed to git**
- `.env` and `config/config.yaml` are gitignored
- API keys never leave your machine (fully self-hosted)
- No cloud dependency, no telemetry, no data collection
- Works offline once configured

---

## ❓ FAQ

**Q: Does this need an expensive server?**
A: No. Runs on any machine with Python 3.11+ — including a $200 Mac Mini.

**Q: Is this a SaaS product?**
A: No. Self-hosted. You only pay for your LLM API calls (~$0.02–0.10/day).

**Q: Can I use it without any API keys?**
A: Yes! Axeng works in demo mode with realistic mock data. `axeng configure` detects missing keys and enables demo mode automatically.

**Q: How do I get the Linear project ID?**
A: Open the project in Linear → the ID is the last part of the URL.

**Q: Can I add custom reports?**
A: Yes. Add a Python script and wire it to `axeng.cli` or run it directly from `python3 -m axeng.tools.your_script`.

**Q: Does it work on Linux/Windows?**
A: Yes. Python 3.11+ on any OS.

---

## 🤝 Contributing

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng
pip install -e .
git checkout -b feat/your-feature
# make changes...
git push -u origin HEAD
# open a pull request
```

---

## 📄 License

GPL-3.0 — use it, fork it, build on it. Keep it open.
