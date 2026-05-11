# Axeng Changelog

## [2.1.1] - 2026-05-11

### Added
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
