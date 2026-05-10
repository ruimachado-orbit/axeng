# Axeng — Engineering Manager Accelerator 🤖

**Stop managing. Start shipping.**

Axeng is an open-source autonomous agent that acts as your AI chief of staff — monitors GitHub, Linear, and your team, generates daily briefs, 1:1 pre-reads, and weekly reports — automatically, every day.

> Built by a CTO who was tired of manually chasing status updates. Now runs 24/7 on a $200 Mac Mini.

---

## ⚡ One-Command Setup

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng
cp .env.example .env    # fill in your API keys
cp config/config.yaml.example config/config.yaml
docker compose up        # open http://localhost:8501
```

That's it. 3 commands, 2 minutes, and you have a running system.

---

## 💡 What It Does

### 🏃 Daily Standup Brief (Mon–Fri 07:30)
What shipped yesterday, who's blocked, PRs waiting >48h, who's OOO → **sent to Telegram**

### 📋 1:1 Pre-reads (auto before every meeting)
对方的 open issues, their commits this week, pending PRs, last 1:1 notes → **ready before you walk in**

### 📊 Weekly Team Report (Friday 17:00)
Per-project status, MVP of the week (scored), commit breakdown, roadmap analysis → **posted to Linear + email**

### 📈 Sprint Health (Friday 16:00)
Health scores (0–100) per project — stale issues, scope creep, overdue → **flagged before it becomes a crisis**

### 🔭 Risk Radar (Friday 16:00)
Quiet repos (no commits 10d+), overloaded members, orphaned PRs, stalled projects → **proactive, not reactive**

### 🤖 "Low-PM" Mode
Every repetitive PM task (triage, prioritization, 1:1 prep, status updates, blocker escalation) → **automated through Hermes → Axemaster → Cron scripts**

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