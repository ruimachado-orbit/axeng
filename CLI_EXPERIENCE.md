# Axeng CLI Experience

**Interactive configuration and chat interface inspired by OpenCode**

---

## Overview

Axeng now includes a beautiful, interactive CLI experience similar to OpenCode:

- 🎨 **Rich terminal UI** with colors and formatting
- 💬 **Interactive configuration** wizard
- 🤖 **Chat interface** for talking to Axeng
- ⚡ **Quick commands** for common operations

---

## Installation

### Via Homebrew (Recommended)

```bash
brew tap ruimachado-orbit/axeng
brew install axeng

# Interactive setup
axeng configure

# Start chatting
axeng chat
```

### Via Git

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng
pip install -r requirements.txt

# Use the CLI
./bin/axeng-cli configure
```

---

## Commands

### Main Commands

```bash
axeng                 # Show help
axeng configure       # Interactive setup wizard
axeng chat           # Chat with Axeng
axeng start          # Start the service
axeng stop           # Stop the service
axeng status         # Check service status
axeng logs           # View logs
axeng update         # Update to latest
```

---

## Interactive Configuration

### `axeng configure`

Beautiful, step-by-step configuration wizard:

```
╔══════════════════════════════════════════════════════════════╗
║              Axeng Configuration Wizard                      ║
║          Let's set up your AI chief of staff                 ║
╚══════════════════════════════════════════════════════════════╝

Step 1: Choose your LLM provider
Axeng needs an AI model to generate reports and insights.

Which provider would you like to use?
  [1] opencode  (Free models available!)
  [2] anthropic (Best quality)
  [3] openai    (Most compatible)
  [4] groq      (Fast & free)
  
> 1

OpenCode Zen - Free models available!
Get your API key at: https://opencode.ai/

OpenCode API key: ●●●●●●●●●●●●●●●●

Model:
  [1] minimax-m2.5-free    (FREE)
  [2] deepseek-v4-flash-free (FREE)
  [3] big-pickle            (FREE)
  
> 1

✓ LLM provider configured

Step 2: GitHub integration
Connect to GitHub to track repos, PRs, and issues.

GitHub token (or press Enter to use 'gh' CLI): ●●●●●●●●●●

✓ GitHub configured

Step 3: Linear integration
Connect to Linear to manage issues and projects.
Get your API key at: https://linear.app/settings/api

Linear API key: ●●●●●●●●●●

✓ Linear configured

Step 4: Optional services

Set up Telegram notifications? [y/N]: y

Talk to @BotFather on Telegram to create a bot

Telegram bot token: ●●●●●●●●●●
Telegram chat ID: 123456789

✓ Telegram configured

Set up Google Calendar integration? [y/N]: n

╔══════════════════════════════════════════════════════════════╗
║              ✓ Configuration complete!                       ║
║                                                               ║
║  Config saved to: ~/.axeng/config.json                       ║
║  Environment: ~/.axeng/.env                                  ║
║                                                               ║
║  Next steps:                                                 ║
║    axeng start    - Start the service                        ║
║    axeng chat     - Chat with Axeng                          ║
║    axeng status   - Check service status                     ║
╚══════════════════════════════════════════════════════════════╝
```

#### Features:
- ✅ Interactive prompts with defaults
- ✅ Password masking for sensitive data
- ✅ Choice menus with descriptions
- ✅ Validates configuration
- ✅ Saves to `~/.axeng/config.json`
- ✅ Generates `.env` file automatically
- ✅ Beautiful terminal formatting

---

## Chat Interface

### `axeng chat`

Interactive chat session with Axeng:

```
╔══════════════════════════════════════════════════════════════╗
║                      Axeng Chat                              ║
║    Ask me about your team, projects, or engineering metrics  ║
╚══════════════════════════════════════════════════════════════╝

Type 'exit' or 'quit' to end the chat

You: What PRs are waiting for review?

Axeng: Let me check GitHub for open pull requests...

Found 3 PRs awaiting review:
• frontend-redesign (#142) - Opened 3 days ago by @alice
  Awaiting review from @bob, @charlie
  
• api-optimization (#139) - Opened 5 days ago by @david
  Awaiting review from @alice
  
• security-patch (#145) - Opened 1 day ago by @eve
  🔴 High priority - security fix needed

You: Show me sprint health

Axeng: Analyzing current sprint...

Sprint Health Score: 78/100

📊 Velocity: On track (85%)
📈 Scope: 3 new issues added
⚠️  Risk: 2 blockers detected
✅ Completion: 12/15 issues done

Details: http://localhost:8501/sprint-health

You: exit

Goodbye! 👋
```

#### Features:
- ✅ Natural language queries
- ✅ Real-time responses
- ✅ Rich formatting (colors, emojis)
- ✅ Links to web dashboard
- ✅ Context-aware suggestions
- ✅ Graceful exit

---

## Quick Commands

### `axeng start`

Start Axeng service:

```bash
$ axeng start
Starting Axeng...
✓ Docker check passed
✓ Port 8501 available
✓ Starting containers...
✓ Axeng started

Open: http://localhost:8501
```

### `axeng status`

Check service status:

```bash
$ axeng status
✓ Axeng is running
Web UI: http://localhost:8501
```

### `axeng stop`

Stop the service:

```bash
$ axeng stop
Stopping Axeng...
✓ Containers stopped
✓ Axeng stopped
```

---

## Configuration Storage

### File Locations

**Homebrew installation:**
```
~/.axeng/config.json          # Main configuration
~/.axeng/.env                 # Environment variables
$(brew --prefix)/var/axeng/   # Service data
```

**Git installation:**
```
<repo>/.axeng/config.json     # Main configuration
<repo>/.env                   # Environment variables
```

### Configuration Format

`~/.axeng/config.json`:
```json
{
  "llm_provider": "opencode",
  "opencode_api_key": "sk-...",
  "opencode_model": "minimax-m2.5-free",
  "github_token": "ghp_...",
  "linear_api_key": "lin_...",
  "telegram_bot_token": "...",
  "telegram_chat_id": "...",
  "google_enabled": false
}
```

The CLI automatically generates `.env` from this configuration.

---

## Comparison with OpenCode

### Similar Features ✅

| Feature | OpenCode | Axeng |
|---------|----------|-------|
| **Interactive setup** | ✅ `/connect` | ✅ `axeng configure` |
| **Beautiful UI** | ✅ Rich TUI | ✅ Rich terminal |
| **Configuration wizard** | ✅ Yes | ✅ Yes |
| **Model selection** | ✅ `/models` | ✅ Included in setup |
| **Chat interface** | ✅ Built-in | ✅ `axeng chat` |
| **Service control** | ✅ TUI | ✅ CLI commands |

### Axeng Additions 🎯

- ✅ **Multiple services** - GitHub, Linear, Telegram, Google
- ✅ **Team management** - Track multiple team members
- ✅ **Web dashboard** - Full UI at http://localhost:8501
- ✅ **Automated reports** - Daily standups, weekly reports
- ✅ **Persistent config** - Survives restarts

---

## Usage Examples

### First Time Setup

```bash
# Install via Homebrew
brew install axeng

# Run interactive configuration
axeng configure

# Follow the prompts to set up:
# 1. Choose LLM provider (OpenCode, Anthropic, etc.)
# 2. Enter API keys
# 3. Configure GitHub
# 4. Configure Linear
# 5. Optional: Telegram, Google

# Start the service
axeng start

# Start chatting!
axeng chat
```

### Daily Usage

```bash
# Check status
axeng status

# Chat about your team
axeng chat
> What's my team working on?
> Show me blocked PRs
> Sprint health check

# View detailed reports
open http://localhost:8501

# View logs
axeng logs
```

### Reconfiguration

```bash
# Re-run configuration wizard
axeng configure

# Make changes to specific settings
# (keeps existing values as defaults)
```

---

## Technical Details

### Dependencies

```python
typer>=0.9.0    # CLI framework
rich>=13.0.0    # Terminal formatting
```

Auto-installed on first run if missing.

### Architecture

```
bin/axeng-cli
  ↓
src/cli.py (Typer app)
  ↓
  ├─ configure() → Interactive wizard
  ├─ chat() → Chat interface
  ├─ start() → Runs 'make start'
  ├─ stop() → Runs 'make stop'
  └─ status() → Checks HTTP endpoint
```

### Configuration Flow

```
User runs: axeng configure
  ↓
Typer prompts for each setting
  ↓
Saves to: ~/.axeng/config.json
  ↓
Generates: ~/.axeng/.env
  ↓
Ready for: axeng start
```

---

## Roadmap

### v1.0 (Current) ✅
- [x] Interactive configuration wizard
- [x] Basic chat interface
- [x] Service control commands
- [x] Rich terminal UI

### v1.1 (Planned) 🚧
- [ ] Enhanced chat with LLM integration
- [ ] Inline report previews in terminal
- [ ] Auto-completion for commands
- [ ] Configuration validation

### v2.0 (Future) 🎯
- [ ] TUI mode (full terminal UI like OpenCode)
- [ ] Real-time updates in chat
- [ ] Multi-user support
- [ ] Voice commands

---

## Contributing

Want to improve the CLI experience?

```bash
git clone https://github.com/ruimachado-orbit/axeng.git
cd axeng

# Edit the CLI
vim src/cli.py

# Test locally
./bin/axeng-cli configure
./bin/axeng-cli chat

# Submit PR
```

---

## Troubleshooting

### CLI not found after install

```bash
# Check installation
which axeng

# If not found, try
brew link axeng

# Or run directly
/opt/homebrew/bin/axeng
```

### Configuration not saving

```bash
# Check permissions
ls -la ~/.axeng/

# Recreate directory
rm -rf ~/.axeng
axeng configure
```

### Chat not connecting

```bash
# Check service status
axeng status

# If not running
axeng start

# Check logs
axeng logs
```

---

## Screenshots

### Configuration Wizard
```
   ╔══════════════════════════════════════════════════════════════╗
   ║              Axeng Configuration Wizard                      ║
   ║          Let's set up your AI chief of staff                 ║
   ╚══════════════════════════════════════════════════════════════╝

   Step 1: Choose your LLM provider
   [Rich formatted prompts with colors and selections]
```

### Chat Interface
```
   ╔══════════════════════════════════════════════════════════════╗
   ║                      Axeng Chat                              ║
   ╚══════════════════════════════════════════════════════════════╝

   You: Show me sprint health
   
   Axeng: [Formatted response with emojis and colors]
```

---

## Summary

Axeng CLI provides an **OpenCode-like experience** for configuration and interaction:

✅ **Easy setup** - Interactive wizard, no manual .env editing  
✅ **Beautiful UI** - Rich terminal formatting with colors  
✅ **Chat interface** - Natural language queries  
✅ **Quick commands** - start, stop, status, logs  
✅ **Persistent config** - Saves between sessions  

**Get started:** `brew install axeng && axeng configure`

---

**Created:** 2026-05-11  
**Version:** 1.0  
**Status:** ✅ Production Ready
