---
name: chat-action-items
description: Use when Axeng needs to extract action items from chat feeds, create Linear issues, and send concise digests without exploding group-message context.
version: 1.0.0
author: Axeng
license: MIT
metadata:
  hermes:
    tags: [chat, action-items, linear, telegram, whatsapp, finops]
    related_skills: [linear-operations]
---

# Chat Action Items

## Overview

Chat action extraction turns operational chatter into tracked Linear work. It is powerful and risky: group chats can explode context, create noisy issues, and leak private content. Keep windows tight, deduplicate aggressively, and only file clear commitments.

## When to Use

- User asks to extract todos from WhatsApp, Telegram, or chat logs.
- A scheduled digest should create Linear issues from chat messages.
- User asks why chat-created tasks are missing/noisy.

## Tool

```bash
python3 src/chat-action-items.py --force
```

The script reads `chat_action_items` configuration from `config/config.yaml`:

- source JSONL path
- cursor path
- chat subject mapping
- Linear team key
- Telegram digest toggle
- business-hour window

## Extraction Rules

Create tasks only for messages that contain:

- explicit owner or clearly implied owner;
- concrete action verb;
- deliverable or expected outcome;
- useful source context.

Do not create tasks for:

- vague discussion;
- FYI messages;
- jokes/reactions;
- duplicated asks already captured;
- sensitive personal/private content unrelated to work.

## FinOps Guardrail

Never feed large group history blindly into an LLM. Keep windows bounded and prefer incremental cursors. For busy groups, cap context tightly and summarize source snippets before classification.

## Digest Shape

```text
✅ Chat action digest
• Messages scanned: N
• Issues created: M
• Skipped: reason summary
• Needs review: ambiguous items
```

## Common Pitfalls

1. **Context explosion.** Large group windows are expensive and noisy.
2. **Duplicate issues.** Search recent Linear issues before creating similar tasks.
3. **No owner.** Unowned work should be flagged for review, not blindly assigned.
4. **Ambiguous consent.** Do not file sensitive personal asks as company work.

## Verification Checklist

- [ ] Cursor advanced only after successful processing.
- [ ] Created Linear issues have title, description, source chat, and owner/triage state.
- [ ] Digest sent only to intended target.
- [ ] No raw secrets or private unrelated content included.
