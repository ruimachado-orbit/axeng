# Axeng Next.js UI

Modern, production-grade dashboard for Axeng — the autonomous Engineering Manager Accelerator.

## Features

- 🎨 **Beautiful UI** — Glass morphism, smooth animations, responsive design
- 📊 **Real-time Dashboard** — Sprint health, team status, agent activity logs
- 🔌 **FastAPI Backend** — Connects to Linear, GitHub, and local logs
- 🌙 **Dark Mode** — Automatic dark/light theme switching
- ⚡ **Fast** — Server-side rendering with Next.js 15

## Quick Start

### Prerequisites

- Node.js 18+ (`brew install node`)
- Python 3.12+ (for the API backend)
- Configured `.env` with API keys (see main Axeng docs)

### Setup

```bash
# 1. Run setup (installs dependencies)
./setup.sh

# 2. Start both API and UI
./start.sh
```

The UI will open at **http://localhost:3000**

### Alternative: Development Mode

```bash
# Runs with live output (useful for debugging)
./dev.sh
```

### Manual Start (separate terminals)

**Terminal 1 - API Backend:**
```bash
npm run api
# or
python3 api_server.py
```

**Terminal 2 - Next.js UI:**
```bash
npm run dev
```

## Architecture

```
┌─────────────────┐
│   Next.js UI    │  Port 3000
│  (Frontend)     │
└────────┬────────┘
         │
         │ HTTP
         ▼
┌─────────────────┐
│  FastAPI Server │  Port 3457
│   (Backend)     │
└────────┬────────┘
         │
         ├─────► Linear API
         ├─────► GitHub API
         └─────► Local SQLite logs (~/.hermes/axeng-logs.db)
```

## API Endpoints

The FastAPI backend provides:

- `GET /api/health` — Health check
- `GET /api/dashboard` — Sprint health + team status
- `GET /api/logs` — Agent activity logs
- `GET /api/reports` — Generated reports
- `GET /api/team` — Team members
- `GET /api/sprint-health` — Detailed sprint metrics

## Configuration

The UI reads configuration from:

1. **Environment Variables:**
   - `AXENG_API_BASE` — API URL (default: `http://localhost:3457`)

2. **API Configuration** (via Python backend):
   - `~/.hermes/.env` — API keys (LINEAR_API_KEY, GITHUB_TOKEN)
   - `config/config.yaml` — Team members, projects, repos

## Tech Stack

- **Next.js 15** — React framework with App Router
- **TypeScript** — Type safety
- **Tailwind CSS** — Utility-first styling
- **Radix UI** — Accessible components
- **Lucide Icons** — Beautiful icons
- **FastAPI** — Python backend
- **SQLite** — Local logs database

## Project Structure

```
ui/nextjs/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── (main)/       # Main layout group
│   │   │   ├── page.tsx  # Dashboard
│   │   │   └── layout.tsx
│   │   ├── layout.tsx    # Root layout
│   │   └── globals.css   # Global styles
│   └── components/       # Reusable UI components
│       ├── sidebar.tsx
│       └── ui/           # shadcn/ui components
├── public/               # Static assets
├── api_server.py         # FastAPI backend
├── setup.sh              # Setup script
├── start.sh              # Production start
├── dev.sh                # Development start
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── tailwind.config.ts    # Tailwind config
└── next.config.ts        # Next.js config
```

## Development

### Adding a New Page

1. Create a new directory in `src/app/(main)/your-page/`
2. Add `page.tsx` with your component
3. Update the sidebar navigation in `src/components/sidebar.tsx`

### Styling

The project uses Tailwind CSS with custom design tokens defined in `globals.css`:

- Color system based on OKLCH
- Glass morphism effects (`.glass`, `.glass-hover`)
- Gradient utilities (`.gradient-text`, `.gradient-bg`)
- Custom animations (`.animate-fade-in-up`, `.animate-pulse-glow`)

### API Integration

Fetch data from the backend:

```typescript
const data = await fetch('http://localhost:3457/api/dashboard')
  .then(res => res.json())
```

Or use the helper:

```typescript
async function getJson<T>(path: string, fallback: T): Promise<T> {
  const API_BASE = process.env.AXENG_API_BASE || 'http://localhost:3457'
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
  return res.ok ? await res.json() : fallback
}
```

## Troubleshooting

### Port 3000 already in use

```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9
```

### Port 3457 (API) already in use

```bash
lsof -ti:3457 | xargs kill -9
```

### Dependencies not installing

```bash
# Clear npm cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### API not connecting

1. Check `.env` has required keys: `LINEAR_API_KEY`, `GITHUB_TOKEN`
2. Verify API is running: `curl http://localhost:3457/api/health`
3. Check API logs: `tail -f /tmp/axeng-api.log`

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Radix UI](https://www.radix-ui.com/)

## License

Part of the Axeng project.
