# ✅ Next.js UI is Ready!

Your production-ready Next.js UI has been set up and is ready to use.

## 🚀 Quick Start

```bash
cd ui/nextjs
./start.sh
```

Then open: **http://localhost:3000**

---

## 📁 What Was Created

✅ **package.json** — Dependencies configured (Next.js 15, React 19, Tailwind, etc.)
✅ **tsconfig.json** — TypeScript configuration
✅ **tailwind.config.ts** — Tailwind CSS with custom design tokens
✅ **setup.sh** — One-command dependency installer
✅ **start.sh** — Production-like startup (runs API + UI)
✅ **dev.sh** — Development mode with live output
✅ **README.md** — Comprehensive documentation (updated)

## ✨ What You Get

### Dashboard Features
- 📊 **Sprint Health** — Real-time project scores from Linear
- 👥 **Team Status** — Who's active, who's OOO
- 📝 **Agent Activity Logs** — Live feed of what Axeng is doing
- 📈 **Stats Cards** — Team size, open issues, PRs, blockers
- 🌙 **Dark Mode** — Automatic light/dark theme

### Technical Stack
- **Next.js 15** — Latest React framework with App Router
- **TypeScript** — Full type safety
- **Tailwind CSS** — Modern utility-first styling
- **FastAPI Backend** — Python API (port 3457)
- **SQLite** — Local agent logs database

---

## 🎯 Usage

### Option 1: Production Mode (Recommended)

```bash
cd ui/nextjs
./start.sh
```

- Runs in background
- Logs to `/tmp/axeng-*.log`
- Press Ctrl+C to stop

### Option 2: Development Mode

```bash
cd ui/nextjs
./dev.sh
```

- Shows live output
- Hot reload on file changes
- Better for debugging

### Option 3: Manual (Two Terminals)

**Terminal 1:**
```bash
cd ui/nextjs
npm run api
```

**Terminal 2:**
```bash
cd ui/nextjs
npm run dev
```

---

## 🔧 Makefile Shortcuts

From the root `axeng` directory:

```bash
make ui-setup    # Install dependencies
make ui-dev      # Start in dev mode
make ui-start    # Start production mode
make ui-stop     # Stop all processes
```

---

## 📋 Quick Checklist

Before using the UI, ensure:

- [x] ✅ Dependencies installed (`npm install` completed)
- [ ] 🔑 API keys configured in `~/.hermes/.env`:
  - `LINEAR_API_KEY=lin_api_xxxxx`
  - `GITHUB_TOKEN=ghp_xxxxx`
- [ ] 👥 Team configured in `config/config.yaml`
- [ ] 🔗 Linear projects added (project IDs)
- [ ] 🐙 GitHub orgs/repos added

---

## 🌐 URLs

| Service        | URL                                      |
|----------------|------------------------------------------|
| **UI**         | http://localhost:3000                    |
| **API**        | http://localhost:3457                    |
| **API Health** | http://localhost:3457/api/health         |
| **Dashboard**  | http://localhost:3457/api/dashboard      |
| **Logs**       | http://localhost:3457/api/logs           |

---

## 🎨 UI Pages

Once running, you'll see:

1. **Dashboard** (`/`) — Main overview, sprint health, team status
2. **Team** (`/team`) — Team member details
3. **Projects** (`/projects`) — Linear project tracking
4. **Logs** (`/logs`) — Agent activity feed
5. **Reports** (`/reports`) — Generated reports

---

## 🔍 Troubleshooting

### Port conflicts

```bash
# Free port 3000 (UI)
lsof -ti:3000 | xargs kill -9

# Free port 3457 (API)
lsof -ti:3457 | xargs kill -9
```

### API not connecting

1. Check `.env` has API keys
2. Test API: `curl http://localhost:3457/api/health`
3. View logs: `tail -f /tmp/axeng-api.log`

### Dependencies issues

```bash
cd ui/nextjs
rm -rf node_modules package-lock.json
npm install
```

---

## 📚 Documentation

- **Next.js UI**: `ui/nextjs/README.md`
- **Setup Guide**: `UI_SETUP.md`
- **Main Docs**: `README.md`

---

## 🎉 Next Steps

1. **Start the UI**: `cd ui/nextjs && ./start.sh`
2. **Open browser**: http://localhost:3000
3. **Configure team**: Add members in the dashboard
4. **Connect services**: Add Linear projects and GitHub repos
5. **Run reports**: Use the "Run Reports" page

---

## 📞 Need Help?

- Read `ui/nextjs/README.md` for detailed docs
- Check `UI_SETUP.md` for troubleshooting
- Open an issue: https://github.com/ruimachado-orbit/axeng/issues

---

**Enjoy your new modern UI! 🚀**
