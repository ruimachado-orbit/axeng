# Axeng UI Setup Guide

## Quick Start

You have **two UI options**:

### 🎯 Next.js UI (Recommended — Production Ready)

Modern, fast, beautiful dashboard with real-time data.

```bash
cd ui/nextjs

# First time setup
./setup.sh

# Start everything
./start.sh
```

Open **http://localhost:3000**

### 📊 Streamlit UI (Legacy — Simple)

Basic UI for configuration and reports.

```bash
make dev
# or
make start
```

Open **http://localhost:8501**

---

## Next.js UI — Detailed Setup

### Prerequisites

```bash
# Install Node.js if you don't have it
brew install node

# Verify
node --version  # Should be 18+
npm --version
```

### Step-by-Step

**1. Navigate to the UI directory:**

```bash
cd ui/nextjs
```

**2. Run setup (first time only):**

```bash
./setup.sh
```

This installs all npm dependencies (~2-3 minutes).

**3. Start the stack:**

```bash
./start.sh
```

This starts:
- FastAPI backend on port **3457**
- Next.js UI on port **3000**

**4. Open your browser:**

```
http://localhost:3000
```

### What You'll See

- **Dashboard** — Sprint health scores, team status, recent activity
- **Team** — Team member overview
- **Projects** — Linear project tracking
- **Logs** — Real-time agent activity
- **Reports** — Generated reports

---

## Alternative: Development Mode

If you want to see live output (useful for debugging):

```bash
cd ui/nextjs
./dev.sh
```

This runs both API and UI in foreground with live logs.

---

## Alternative: Manual Start

**Terminal 1 — API Backend:**

```bash
cd ui/nextjs
python3 api_server.py
```

API will run on **http://localhost:3457**

**Terminal 2 — Next.js UI:**

```bash
cd ui/nextjs
npm run dev
```

UI will run on **http://localhost:3000**

---

## Makefile Shortcuts

From the root `axeng` directory:

```bash
make ui-setup    # Install dependencies
make ui-dev      # Start in development mode
make ui-start    # Start in production mode
make ui-stop     # Stop all UI processes
```

---

## Troubleshooting

### "Port 3000 is already in use"

```bash
lsof -ti:3000 | xargs kill -9
```

### "Port 3457 is already in use"

```bash
lsof -ti:3457 | xargs kill -9
```

### API not connecting to Linear/GitHub

1. Check your `.env` file has:
   ```
   LINEAR_API_KEY=your_key_here
   GITHUB_TOKEN=your_token_here
   ```

2. Verify the keys work:
   ```bash
   make test-services
   ```

### Dependencies failing to install

```bash
cd ui/nextjs
rm -rf node_modules package-lock.json
npm install
```

### "module not found" errors

The UI uses Next.js 15 with new conventions. If you see import errors:

1. Check the file exists in `src/`
2. Paths use `@/` alias (e.g., `@/components/ui/button`)
3. Try restarting the dev server

---

## What's Running?

When you start the Next.js UI, you get:

1. **FastAPI Backend** (`api_server.py`)
   - Port: **3457**
   - Provides: `/api/dashboard`, `/api/logs`, `/api/team`, etc.
   - Connects to: Linear, GitHub, local SQLite DB

2. **Next.js Frontend**
   - Port: **3000**
   - Server-side rendering
   - Fetches data from FastAPI backend

3. **Data Sources:**
   - **Linear API** — Projects, issues, sprint data
   - **GitHub API** — Repos, PRs, commits
   - **Local DB** — `~/.hermes/axeng-logs.db` (agent activity logs)

---

## Configuration

### Environment Variables

Create/edit `~/.hermes/.env`:

```bash
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxx
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
```

### Team & Projects

Edit `config/config.yaml`:

```yaml
team:
  - name: Jane Developer
    github: janedev
    role: Senior Engineer
    email: jane@company.com

linear:
  projects:
    Frontend:
      owner: Jane Developer
      repos:
        - my-company/web-app

  project_ids:
    Frontend: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

github:
  orgs:
    - my-company
  repos:
    - my-company/web-app
```

---

## Next Steps

Once the UI is running:

1. **Configure your team** — Add team members in the dashboard
2. **Connect Linear** — Add project IDs
3. **Connect GitHub** — Add orgs/repos
4. **Run reports** — Use the "Run Reports" page to generate standups, sprint health, etc.

---

## Architecture

```
┌──────────────────────────────────────┐
│   Browser (localhost:3000)           │
│   Next.js 15 + React + Tailwind      │
└──────────────┬───────────────────────┘
               │ HTTP requests
               ▼
┌──────────────────────────────────────┐
│   FastAPI (localhost:3457)           │
│   Python backend + SQLite            │
└──────────────┬───────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌───────┐  ┌───────┐  ┌─────────┐
│ Linear│  │GitHub │  │ Local   │
│  API  │  │  API  │  │ Logs DB │
└───────┘  └───────┘  └─────────┘
```

---

## Comparison: Next.js vs Streamlit

| Feature                | Next.js UI       | Streamlit UI     |
|------------------------|------------------|------------------|
| **Speed**              | ⚡ Fast          | 🐌 Slower        |
| **Design**             | 🎨 Modern        | 📊 Basic         |
| **Real-time updates**  | ✅ Yes           | ⚠️ Manual refresh|
| **Mobile-friendly**    | ✅ Responsive    | ❌ Not optimized |
| **Setup complexity**   | Medium (Node.js) | Low (Python only)|
| **Production-ready**   | ✅ Yes           | ⚠️ Dev tool      |

**Recommendation:** Use **Next.js UI** for daily use. Use **Streamlit** only for quick config edits if needed.

---

## Need Help?

- Next.js UI docs: `ui/nextjs/README.md`
- Main Axeng docs: `README.md`
- Issues: https://github.com/ruimachado-orbit/axeng/issues
