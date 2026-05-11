# Axeng — Engineering Manager Accelerator 🤖

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18-brightgreen)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)

**Stop managing. Start shipping.**

Autonomous AI chief of staff that monitors GitHub, Linear, your calendar, and team — automatically generates standups, 1:1 pre-reads, sprint reports, risk alerts, team sync, and offboarding.

> Runs 24/7 on a $200 Mac Mini. Built by a CTO who was tired of manually chasing status updates.
>
> **Open source** under GPL-3.0. Free forever, self-hosted, no cloud dependencies.

---

## ⚡ Install in 2 Minutes

### Option A — Homebrew (Recommended) 🍺

```bash
# Install
brew tap ruimachado-orbit/axeng
brew install axeng

# Interactive setup wizard (no manual .env editing!)
axeng configure

# Start chatting with your AI chief of staff
axeng chat

# Or start the web UI
axeng start
open http://localhost:8501
```

**Features:**
- ✨ Interactive configuration wizard
- 🎨 Beautiful terminal UI
- 🔒 Password-masked inputs
- ✅ Auto-generates .env
- 💬 Built-in chat interface

### Option B — Git Clone (Development)

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng

# Prerequisites
brew install node python@3.12 gh git make

# Interactive CLI setup
pip install -r requirements.txt
python3 bin/axeng-cli configure

# Or one-command setup
make quick-start

# Or step by step:
make setup-env      # Create .env and config.yaml from templates
# Edit .env and config/config.yaml with your API keys
make dev            # Start the UI
```

**Open http://localhost:3000** for Next.js UI or http://localhost:8501 for Streamlit

### CLI Commands (After Brew Install)

```bash
axeng configure     # Interactive setup wizard ⭐
axeng chat          # Chat with Axeng
axeng start         # Start the service
axeng stop          # Stop the service
axeng status        # Check if running
axeng logs          # View logs
axeng --help        # Show all commands
```

### Makefile Commands (Git Clone)

```bash
make help           # Show all commands
make dev            # Start UI in dev mode (foreground)
make start          # Start UI (background)
make stop           # Stop all services
make logs           # View logs
make build          # Install/update dependencies
make update         # Pull latest + restart
make setup-google   # Google Workspace setup instructions
make test-google    # Test Google authentication
make free-ports     # Free ports 3000/3457 if blocked
```

---

## ✅ Prerequisites

| What | Why | Where to get it |
|------|-----|-----------------|
| **Node.js 18+** | Runs the Next.js UI | `brew install node` |
| **Python 3.12+** | Backend API + agent scripts | `brew install python@3.12` |
| **LLM API key** | Generates all reports | See [LLM Setup](#-llm-providers) below |
| **GitHub token** | Reads orgs, repos, PRs | `gh auth login` OR [github.com/settings/tokens](https://github.com/settings/tokens) |
| **Linear API key** | Reads/writes issues + projects | [linear.app/settings/api](https://linear.app/settings/api) |
| **Telegram bot** *(optional)* | Receives daily briefings | Talk to [@BotFather](https://t.me/BotFather) on Telegram |
| **Google Calendar** *(optional)* | Detects OOO, 1:1 meetings | [Google Cloud Console](https://console.cloud.google.com/) |
| **Granola API key** *(optional)* | Reads meeting notes, summaries, transcripts | Granola desktop → Settings → Connectors → API keys |
| **Obsidian vault** *(optional)* | Stores 1:1 notes + team memory | [obsidian.md](https://obsidian.md/) |

**That's it.** No Docker, no cloud account, no monthly fee. Everything runs locally on your machine.

---

## 🔑 Setting Up Your API Keys

### 🤖 LLM Providers

Axeng supports **8 LLM providers** with automatic fallback — set one or more API keys:

| Provider | Best For | API Key | Type |
|----------|----------|---------|------|
| **Anthropic Claude** | Best quality + speed | `ANTHROPIC_API_KEY` | Cloud |
| **OpenAI** | o1/o3 reasoning models | `OPENAI_API_KEY` | Cloud |
| **OpenCode AI** | Coding specialist | `OPENCODE_API_KEY` | Cloud |
| **Groq** | Fast free inference | `GROQ_API_KEY` | Cloud |
| **OpenRouter** | Multi-provider aggregation | `OPENROUTER_API_KEY` | Cloud |
| **Google AI** | Gemini 2.0 Flash | `GOOGLE_API_KEY` | Cloud |
| **Ollama** | Local Llama/Mixtral (no key needed) | — | **Local** |
| **LM Studio** | Local GGUF models (no key needed) | — | **Local** |

#### Cloud API Keys

| Provider | Sign up / Console |
|----------|-------------------|
| Anthropic | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| OpenAI | [platform.openai.com](https://platform.openai.com) → API Keys |
| OpenCode | [opencode.ai](https://opencode.ai) — free tier available |
| Groq | [console.groq.com](https://console.groq.com) → API Keys (free tier) |
| OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Google AI | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |

#### 🏠 Local LLM (zero cost — runs on your machine)

**Ollama** (recommended for local):
```bash
brew install ollama         # macOS
# or: curl -fsSL https://ollama.com/install.sh | sh   # Linux

ollama pull llama3.3         # or any model: mistral, codellama, qwen2.5
ollama serve                # starts on http://localhost:11434/v1
```

**LM Studio** (GUI + API server):
1. Download from [lmstudio.ai](https://lmstudio.ai)
2. Download a model (GGUF format)
3. Click **→ Local Server** tab → Start server
4. Axeng auto-detects it at `http://localhost:1234/v1`

#### How fallback works

Axeng tries providers in this order until one succeeds:
```
Anthropic → OpenAI → OpenCode → Groq → OpenRouter → Google → Ollama → LM Studio
```

Override the order in `.env`:
```bash
LLM_PROVIDER_ORDER=ollama,anthropic,openai,groq
```

### GitHub & Linear

```bash
# GitHub — option A: token
GITHUB_TOKEN=***

# OR option B: CLI auth (no token needed)
gh auth login

# Linear — get from linear.app/settings/api
LINEAR_API_KEY=***

# === OPTIONAL ===

# Telegram (for briefings)
TELEGRAM_BOT_TOKEN=80|TEL..._ID=

# Google Calendar (for OOO + 1:1 detection)
GOOGLE_CLIENT_SECRET=~/.hermes/secrets/google_client_secret.json
GOOGLE_TOKEN_PATH=~/.hermes/secrets/google_token.json

# Granola (for meeting notes, summaries, and transcripts)
GRANOLA_API_KEY=***

# World news in daily briefings
NEWS_API_KEY=***

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

## 📅 Google Workspace Setup (Optional)

To enable Google Calendar and Gmail integration for OOO detection, 1:1 meeting insights, and email reports:

### 1. Get OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable APIs:
   - Go to "APIs & Services" → "Library"
   - Search and enable: **Google Calendar API**
   - Search and enable: **Gmail API**
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Configure OAuth consent screen (if prompted):
     - Choose "External"
     - Add app name, support email
     - Add scopes: `calendar.readonly`, `gmail.readonly`
     - Add your email as test user
   - Application type: **Desktop app**
   - Download the JSON file

### 2. Save Client Secret

```bash
mkdir -p ~/.hermes/secrets
mv ~/Downloads/client_secret_*.json ~/.hermes/secrets/google_client_secret.json
```

### 3. Authenticate (Generate Token)

The Google API script handles OAuth automatically:

```bash
# Test authentication (opens browser)
make test-google

# Or directly:
python3 ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py auth test
```

This will:
- Open your browser
- Ask you to sign in to Google
- Request Calendar and Gmail permissions
- Save the token to `~/.hermes/secrets/google_token.json`

### 4. Verify

```bash
# List calendar events
python3 ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py calendar list

# List recent emails
python3 ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail list --max 5
```

**That's it!** Axeng will now use Google Calendar for OOO detection and 1:1 meeting insights.

---

## 🧠 Skills + System Prompt

Axeng ships with workflow skills so it knows not just which tool to call, but how to operate like an Engineering Manager:

- `granola-api` — Granola notes, summaries, transcripts, exports.
- `linear-operations` — issues, projects, CRM leads, vacations, blockers.
- `weekly-team-report` — weekly report generation, validation, delivery.
- `github-team-intelligence` — PRs, reviews, stale work, repo signals.
- `calendar-meeting-prep` — 1:1s, agendas, OOO, meeting pre-reads.
- `team-sync-obsidian` — Obsidian-backed team memory and sync.
- `chat-action-items` — chat-to-Linear action item extraction.
- `offboarding` — GitHub + Linear access removal with dry-run safety.

The LLM synthesis layer uses `prompts/engineering-manager-code-act.md`: a direct Engineering Manager system prompt with code-act behavior, evidence-first answers, ownership, delivery risk, and concrete next actions.

---

## 🎯 All Features

### 🏃 Daily Standup Brief (Mon–Fri 07:30)
What shipped yesterday, who's blocked, PRs waiting >48h, who's OOO → **sent to Telegram**

### 📋 1:1 Pre-reads (auto before every meeting)
对方的 open issues, their commits, pending PRs, last 1:1 notes → **ready before you walk in**

### 🎙️ Granola Meeting Intelligence
List recent Granola notes, fetch summaries/transcripts, and export meetings to Markdown for follow-ups, 1:1 memory, and action-item extraction.

```bash
python3 src/tools/granola_tool.py notes --days 7 --limit 10
python3 src/tools/granola_tool.py latest --days 30 --transcript
python3 src/tools/granola_tool.py note not_xxxxxxxxxxxxxx --transcript
python3 src/tools/granola_tool.py export --days 30
```

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
│   ├── llm_gateway.py         # 🤖 Unified LLM client (8 providers + fallback)
│   ├── standup-brief.py       # Daily brief (07:30 Mon–Fri)
│   ├── one-on-one-pre-read.py # 1:1 pre-read generator
│   ├── sprint-health.py       # Sprint health (Fri 16:00)
│   ├── risk-radar.py          # Risk radar (Fri 16:00)
│   ├── team_sync.py           # GitHub → Obsidian sync
│   ├── orchestrator.py         # NL query router + LLM synthesis
│   ├── project_map.py         # Linear ↔ GitHub mapping
│   └── tools/
│       ├── linear_tool.py
│       ├── github_activity.py
│       ├── calendar_insights.py
│       ├── team_query.py
│       ├── offboarding.py     # 🛡️ Offboarding tool
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
