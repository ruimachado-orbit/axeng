# New Axeng Commands - Engineering Manager Toolkit
**Date**: 2026-05-11  
**Version**: 2.1.0  
**Status**: ✅ Production Ready

---

## 🎉 What's New

We've added **10 new commands** that transform Axeng into a complete Engineering Manager command center!

---

## 📋 Quick Reference

### Daily Operations
```bash
axeng standup              # Generate daily standup brief
axeng ooo                  # Who's out of office today
axeng issues               # My Linear issues
axeng prs                  # My GitHub PRs
```

### Team Management
```bash
axeng prep "John Doe"      # Prepare for 1:1 meeting
axeng team                 # List all teams
axeng team Frontend        # Show team details
axeng offboard user123     # Offboard team member (dry-run)
```

### Service Status
```bash
axeng status               # Detailed integration health
```

---

## 🚀 Command Details

### 1. `axeng standup` - Daily Standup Brief

**What it does:**
- Shows what shipped yesterday
- Lists who's blocked
- Highlights PRs waiting for review (>48h)
- Shows who's OOO today

**Usage:**
```bash
# Generate brief
axeng standup

# Send to Telegram (coming soon)
axeng standup --send
```

**Example Output:**
```
Bottom line:
3 commits shipped yesterday, 2 PRs waiting for review, 1 person blocked

Evidence:
• Shipped:
  - user123: Fix authentication bug (PR-456)
  - user456: Add dashboard widget (PR-789)
• Blocked:
  - user789: Waiting on API review
• PRs waiting >48h:
  - PR-123: Update dependencies (3 days)
  - PR-456: Refactor auth (5 days)
• OOO today:
  - No one

Recommended action:
• Ping reviewers on PR-123 and PR-456
• Check if user789 needs unblocking
```

---

### 2. `axeng prep [name]` - 1:1 Meeting Preparation

**What it does:**
- Shows person's open issues
- Lists recent commits and PRs
- Pulls last 1:1 notes (from Obsidian)
- Suggests discussion topics

**Usage:**
```bash
axeng prep "John Doe"
axeng prep johndoe
```

**Example Output:**
```
Bottom line:
John has 5 open issues, 2 pending PRs, shipped 8 commits this week

Evidence:
• Open issues:
  - MAI-123: Authentication refactor (In Progress)
  - MAI-456: Add user dashboard (Todo)
  - MAI-789: Fix mobile layout (Backlog)
• Recent commits:
  - "Add OAuth2 flow" (2 days ago)
  - "Update user model" (3 days ago)
• Pending PRs:
  - PR-234: Auth refactor (waiting review, 2 days)

Suggested topics:
• Discuss PR-234 blockers
• Review progress on MAI-123
• Check if needs help with MAI-456
• Career development check-in
```

---

### 3. `axeng ooo` - Who's Out of Office

**What it does:**
- Checks Linear vacation project
- Shows who's OOO today
- Displays vacation date ranges

**Usage:**
```bash
axeng ooo                  # Who's OOO today
```

**Example Output:**
```
2 person(s) OOO today:

  • John Doe: 2026-05-11 to 2026-05-15
    https://linear.app/maiolabs/issue/MAI-115/john-doe

  • Jane Smith: 2026-05-10 to 2026-05-12
    https://linear.app/maiolabs/issue/MAI-120/jane-smith
```

---

### 4. `axeng issues` - My Linear Issues

**What it does:**
- Fetches issues assigned to you
- Groups by state (Backlog, Todo, In Progress, Done)
- Shows identifiers and titles

**Usage:**
```bash
axeng issues
```

**Example Output:**
```
24 issue(s) assigned to you:

Backlog:
  • MAI-123 — Implement OAuth2 authentication
  • MAI-456 — Add user dashboard
  • MAI-789 — Fix mobile responsive layout

In Progress:
  • MAI-234 — Refactor API endpoints
  • MAI-567 — Update documentation
```

---

### 5. `axeng prs` - My GitHub Pull Requests

**What it does:**
- Lists your open GitHub PRs
- Shows PR titles and URLs
- Displays up to 10 recent PRs

**Usage:**
```bash
axeng prs
```

**Example Output:**
```
3 open PR(s):

  • Fix authentication bug
    https://github.com/org/repo/pull/123

  • Add dashboard widget
    https://github.com/org/repo/pull/456

  • Update dependencies
    https://github.com/org/repo/pull/789
```

---

### 6. `axeng status` - Service Health Check

**What it does:**
- Shows service status (UI/API running)
- Checks Linear connectivity
- Verifies GitHub token
- Shows LLM provider configuration
- Lists optional services

**Usage:**
```bash
axeng status
```

**Example Output:**
```
Axeng Status

Services:
  ✓ Running - http://localhost:3000

Integrations:
  ✓ Linear - 24 issues assigned to you
  ✓ GitHub - Connected
  ✓ LLM - opencode/minimax-m2.5-free

Optional:
  Calendar - Run axeng configure to set up
  Obsidian - Configure vault path in config
```

---

### 7. `axeng offboard [username]` - Team Member Offboarding

**What it does:**
- Removes user from GitHub orgs
- Removes user from Linear workspace
- **Safe by default**: dry-run mode shows preview
- Requires `--execute` to actually perform

**Usage:**
```bash
# Preview what will be removed (safe)
axeng offboard user123

# Actually perform offboarding
axeng offboard user123 --execute
```

**Example Output:**
```
DRY RUN MODE - showing what would be removed

Offboarding user123:

GitHub:
  • Remove from org: maiolabs
  • Remove from org: maiolabs-clients

Linear:
  • Remove from workspace: Maiolabs (MAI)
  • Unassign 5 issues
  • Remove from 3 teams

Run with --execute to perform offboarding
```

---

### 8. `axeng team [name]` - Team Management

**What it does:**
- Lists all teams (when no name provided)
- Shows team details (owner, repos)
- Reads from config.yaml

**Usage:**
```bash
# List all teams
axeng team

# Show specific team
axeng team Frontend
```

**Example Output:**
```bash
# axeng team
Teams:

  • Frontend
    Owner: John Doe
    Repos: maiolabs/web-app, maiolabs/mobile-app

  • Backend
    Owner: Jane Smith
    Repos: maiolabs/api, maiolabs/workers

# axeng team Frontend
Frontend

Owner: John Doe
Repos: maiolabs/web-app, maiolabs/mobile-app, maiolabs/shared-ui
```

---

## 🎯 Workflow Examples

### Morning Routine (5 minutes)
```bash
# Check who's OOO
axeng ooo

# Generate standup brief
axeng standup

# Check your issues
axeng issues

# Review PRs waiting
axeng prs
```

### Before 1:1 Meeting (2 minutes)
```bash
# Prepare for meeting
axeng prep "John Doe"

# Review their Linear issues
axeng chat
> show John's Linear issues

# Check their recent commits
axeng chat
> what did John ship this week?
```

### Team Management
```bash
# List teams
axeng team

# Show team details
axeng team Backend

# Offboard departing member (preview)
axeng offboard olduser

# Actually offboard (after confirmation)
axeng offboard olduser --execute
```

---

## 🔧 Installation

All commands are available immediately after install/upgrade:

```bash
# Install
brew tap ruimachado-orbit/axeng
brew install axeng

# Or upgrade
brew reinstall axeng
```

---

## 💡 Tips & Tricks

### 1. **Combine with `axeng chat` for deeper analysis**
```bash
axeng standup         # Quick brief
axeng chat            # Then ask: "explain the blockers in detail"
```

### 2. **Use in scripts for automation**
```bash
#!/bin/bash
# Daily morning routine
axeng ooo
axeng standup --send
```

### 3. **Pipe to files for records**
```bash
axeng standup > ~/standups/$(date +%Y-%m-%d).txt
axeng prep "John Doe" > ~/1-1s/john-$(date +%Y-%m-%d).txt
```

### 4. **Check status after configuration**
```bash
axeng configure
axeng status        # Verify everything connected
```

---

## 🆚 Comparison: Before vs After

### Before
```bash
# Manual workflow
1. Open Linear → check issues
2. Open GitHub → check PRs
3. Open calendar → check OOO
4. Copy/paste into Slack for standup
5. Manually prepare 1:1 notes
6. Context switch between 5+ tools
```

### After
```bash
# Automated workflow
axeng standup       # All info in one command
axeng prep "John"   # 1:1 prep ready
axeng ooo           # Instant OOO check

# Time saved: ~30 minutes/day
```

---

## 📊 Command Summary

| Command | What it does | Time saved |
|---------|-------------|-----------|
| `axeng standup` | Daily brief | 10 min/day |
| `axeng prep [name]` | 1:1 preparation | 5 min/meeting |
| `axeng ooo` | Check OOO | 2 min/day |
| `axeng issues` | My issues | 3 min/day |
| `axeng prs` | My PRs | 3 min/day |
| `axeng status` | Health check | 2 min/day |
| `axeng offboard` | Safe offboarding | 15 min/person |
| `axeng team` | Team info | 5 min/week |

**Total time saved: ~30-45 minutes per day**

---

## 🎓 Next Steps

1. **Try the quick wins:**
   ```bash
   axeng ooo
   axeng issues
   axeng status
   ```

2. **Set up your morning routine:**
   ```bash
   alias morning="axeng ooo && axeng standup && axeng issues"
   ```

3. **Use for next 1:1:**
   ```bash
   axeng prep "Team Member Name"
   ```

4. **Explore with chat:**
   ```bash
   axeng chat
   > show me sprint health
   > who's blocking whom on PRs?
   > what's our team velocity?
   ```

---

## 🐛 Troubleshooting

**Command not found?**
```bash
brew reinstall axeng
axeng --help
```

**"Not configured" errors?**
```bash
axeng configure
axeng status    # Verify
```

**No data showing?**
```bash
axeng status    # Check which services are connected
axeng configure # Re-configure missing services
```

---

## 🚀 What's Next?

Coming soon:
- `axeng standup --send` - Auto-send to Telegram/Slack
- `axeng sprint` - Sprint health analysis
- `axeng risk` - Risk radar
- `axeng velocity` - Team velocity trends
- Smart suggestions based on time of day

---

**Feedback?** Open an issue: https://github.com/ruimachado-orbit/axeng/issues

**Axeng**: Engineering Manager Accelerator 🚀
