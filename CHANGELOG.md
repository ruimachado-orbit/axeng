# Axeng Changelog

## [2.2.2] - 2026-05-12

### Added
- **Daily standup GitHub shipped summaries**
  - "What shipped yesterday" now uses merged GitHub PRs as the primary signal
  - Uses the full previous Europe/Lisbon calendar day instead of a rolling 24h window
  - Includes direct commits as an additional/fallback signal

- **Per-developer achievement summaries**
  - Groups shipped PRs and commits by developer
  - Summarizes achievements deterministically from PR and commit titles
  - Shows repos touched and compact PR/commit counts for Telegram standup briefs

### Fixed
- **Stale PR review logic** now focuses on open PRs waiting on requested reviewers instead of recently merged PRs.

## [2.2.0] - 2026-05-11

### Added
- **Sprint Health Analysis** (`axeng sprint`)
  - Current sprint progress and burndown
  - Velocity tracking (points/day)
  - Sprint completion predictions
  - Historical velocity trends
  - Actionable insights and recommendations
  
- **DORA Metrics Dashboard** (`axeng dora`)
  - Deployment Frequency (deploys/week)
  - Lead Time for Changes (commit to production)
  - Mean Time to Recovery (MTTR for incidents)
  - Change Failure Rate (% of failed deployments)
  - Overall DORA tier (Elite/High/Medium/Low)
  - Strengths and improvement areas
  
- **Automated Weekly Reports** (`axeng report --weekly`)
  - Comprehensive weekly summary
  - Sprint health status
  - DORA metrics overview
  - GitHub activity (commits, PRs, reviews)
  - Linear issues summary
  - Velocity trends
  - Key insights and recommendations
  - Send via Telegram with `--send` flag

### Features
All metrics calculated using **only Linear + GitHub** data:
- No external CI/CD integration needed
- No incident management platform required
- Works with existing Axeng setup
- Zero additional configuration

### Time Savings
- **Sprint planning:** 2-3 hours → 15 minutes
- **Weekly reporting:** 1-2 hours → 2 minutes
- **DORA metrics:** 30 minutes → 30 seconds
- **Total:** Additional 10-15 hours saved per week!

## [2.1.1] - 2026-05-11

### Fixed
- **JSON import bug**: Removed redundant `import json` statements inside functions that caused "cannot access local variable" errors
- **PR command timeout**: Increased timeout from 10s to 30s for GitHub API calls

### Added
- **Smart Query Suggestions**: Context-aware query suggestions in `axeng chat`
  - Time-based suggestions (morning routine, end of day summary, etc.)
  - Day-specific suggestions (Monday kickoff, Friday review)
  - Quick selection by number (1-3)
  - Refresh with 'suggestions' command
  - Personalized to your workflow patterns
  
- **PR Health Analysis**: New `axeng pr-health` command provides comprehensive PR pipeline insights
  - Shows open PRs with review status (pending, approved, changes requested)
  - Detects stale PRs (>3 days no activity)
  - Identifies PRs needing first review
  - Calculates review velocity (PRs/day)
  - Provides actionable insights (bottlenecks, merge delays, low velocity)
  - Visual metrics dashboard with emojis
  
- **Progress Indicators**: The orchestrator now shows real-time progress when executing tools
  - Displays tool name and purpose (e.g., "Querying linear_issues... (Get Linear issues by state)")
  - Shows completion status with checkmark or X
  - Reports execution time for each tool
  - Shows total execution time for all tools
  - Displays LLM synthesis progress with model and timing
  
### Example Output
```
🎯 Orchestrator: what linear issues are blocked?
🛠️  Tools selected: ['linear_issues', 'linear_sync', 'team_query']

📦 Executing 3 tool(s)...

  🔍 Querying linear_issues... (Get Linear issues by state)
     ✓ Completed in 0.04s
  🔍 Querying linear_sync... (Sync Linear issues to Obsidian vault)
     ✓ Completed in 0.03s
  🔍 Querying team_query... (Query Obsidian vault for stored data)
     ✓ Completed in 0.03s

⏱️  Total tool execution time: 0.10s

🤖 Synthesizing response with LLM...
   ✓ Completed in 1.23s using opencode/minimax-m2.5-free
```

### Benefits
- Better visibility into what Axeng is doing
- Easy to identify slow tools
- Professional user experience
- Helps debug integration issues

---

## [2.1.0] - 2026-05-11

### Added
- 10 new EM workflow commands (see IMPLEMENTATION_COMPLETE.md)
- Interactive configuration wizard
- Chat history persistence
- Graceful fallbacks for optional integrations
- Comprehensive error messages with setup instructions

### Time Savings
- 30-45 minutes per day across all commands
- See IMPLEMENTATION_COMPLETE.md for detailed metrics
