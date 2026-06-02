# Steering Report Generation Rules (CEO Version)

## Objective

The Steering Report is a CEO decision-making document.

It is not a project dashboard, Jira report, GitHub report, engineering report, or activity report.

Its purpose is to answer:

1. What was delivered this week?
2. What changed?
3. Which milestones are most likely to succeed?
4. Which milestones are at risk?
5. Where should leadership focus attention?
6. Which decisions are required?

The report must focus on:

- Outcomes
- Delivery confidence
- Business impact
- Milestone progress
- Leadership decisions

The report must not focus on:

- Ticket hygiene
- Project management mechanics
- Repository activity metrics
- Process metrics without business impact

---

## Audience

The primary audience is the CEO.

Assume the reader has 3–5 minutes.

Every section should help answer:

- What should I celebrate?
- What should I worry about?
- What should I decide?
- Where should I spend attention?

If a section does not help answer those questions, it should not exist.

---

## Data Sources

### Source Priority

#### 1. Linear Issues Completed This Week

**Primary source for "Delivered" section.**

Linear completed issues are the definitive record of shipped work within the sprint/project tracking system.

Use their titles to name what was delivered.

Translate technical issue names into business-readable outcomes.

#### 2. GitHub Issues Closed This Week

**Secondary source for "Delivered" section.**

Closed GitHub issues represent features completed, bugs fixed, and work items resolved.

Group by theme when multiple issues share a topic.

Never report counts without naming what closed.

#### 3. GitHub Pull Requests Merged

**Tertiary source for "Delivered" section.**

Merged PRs confirm code shipped to the codebase.

Use PR titles to name specific capabilities delivered.

Prefer PR titles over raw commit messages — PRs represent reviewed, intentional delivery.

#### 4. GitHub Commits

**Last-resort source for "Delivered" section only.**

Use commit messages only when Linear issues, GitHub issues, and PR titles are all absent.

Commits are the lowest-signal source — they capture implementation steps, not outcomes.

Never use commits as a source for the **Next Week** plan.

#### 5. Linear In-Progress and Focus Issues

**Primary source for "Next Week" plan.**

Issues currently in progress are the most reliable signal for what will ship next week.

High-priority todo issues (focus issues) indicate what starts next.

Do not use commit history to predict next-week work.

#### 6. Granola Transcripts

**Primary source for commitments, decisions, and risks.**

Meeting notes capture explicit team commitments — these belong in Next Week.

Decisions discussed in meetings inform blockers and risks.

Strategic context from Granola supplements quantitative signals.

Granola must not determine project status alone.

---

## Delivered Section — Required Synthesis

### What "Delivered" Must Show

Every project must have a Delivered section that lists what was actually completed this week.

"Delivered" means: features built, bugs fixed, capabilities shipped, milestones reached.

"Delivered" does not mean: commits pushed, issues opened, standups held.

### Synthesis Order

Follow this order strictly:

1. Read Linear issues completed this week → extract titles → translate to business outcomes
2. Read GitHub issues closed this week → extract titles → add any outcomes not already covered
3. Read merged PR titles → extract capabilities → add any not already covered
4. Read commit messages → only if steps 1–3 produced nothing
5. Read Granola transcripts → add any delivery items explicitly confirmed in meetings

### Delivery Bullet Format

Each bullet must name WHAT was done, not how many tickets moved.

**Bad:**
- 14 issues completed
- 23 commits merged
- Development continued on authentication

**Good:**
- Completed provider routing — payments now support multi-currency
- Fixed onboarding flow regression affecting new signups
- Shipped admin dashboard export feature
- Resolved performance bottleneck in data pipeline

### Fallback When Evidence Is Missing

If Linear completed titles, GitHub closed issues, and PR titles are all empty but commits exist:

Write: "Active development underway — commit descriptions insufficient to identify specific outcomes delivered."

If everything is empty:

Write: "No delivery evidence available this week."

Do not invent outcomes. Do not write generic summaries.

---

## Next Week Plan — Required Synthesis

### What "Next Week" Must Show

The Next Week section is a forward-looking commitment, not a projection from past activity.

It must be grounded in intent and in-flight work.

### Source Priority for Next Week

Use only these sources:

1. **Granola meeting commitments** — explicit team promises made in meetings this week
2. **Linear issues currently in progress** — work already started, highest delivery confidence
3. **Linear high-priority focus issues** — what starts next
4. **Upcoming milestones** — deadline context for what must land

**Do not use commits or commit messages for next-week planning.**

Commits are evidence of past work. They do not indicate future intent.

### Next Week Bullet Format

Each bullet is a specific deliverable or commitment:

**Bad:**
- Continue development
- Work on issues in progress
- Maintain momentum

**Good:**
- Complete authentication provider integration (in progress)
- Ship customer-facing onboarding wizard
- Hit MVP milestone by [date]
- Resolve payment gateway blocker (committed in Monday standup)

---

## CEO Translation Layer

The CEO should never need to open GitHub to understand progress.

Before writing any accomplishment ask:

- What changed?
- Why does it matter?
- What milestone moved forward?
- What is now possible?

**Bad:**
- 43 commits merged
- 27 issues completed
- Development continued

**Good:**
- Implemented onboarding workflow improvements.
- Completed production readiness work.
- Finalized portal authentication capabilities.
- Increased confidence in MVP launch.

The report should describe outcomes, not activities.

---

## Delivery Narrative

Every project must generate a delivery narrative.

Combine:

- Linear completed issues
- GitHub closed issues
- Merged PRs
- Milestone movement
- Meeting-confirmed deliveries

into 3–6 concise bullets.

Focus on:

- What changed?
- Why does it matter?
- What happens next?

Activity is evidence.

Delivery is the outcome.

Always prefer outcomes.

---

## Accomplishment Quality Check

Every accomplishment must pass this test:

Can a CEO understand what was delivered without opening GitHub?

If not, rewrite it.

Reject statements such as:

- Closed 23 issues
- Merged 43 commits
- Development continued
- Progress was made
- Work is ongoing

Prefer:

- Completed onboarding workflow implementation
- Added provider routing capabilities
- Finalized rollout readiness work
- Improved production observability

Issue counts and commit counts may appear only as supporting evidence.

They must never be the accomplishment itself.

---

## Project Classification

Projects must be classified as:

- On Track
- Monitor
- At Risk
- Blocked
- Inactive
- Discovery
- Planning
- Early Execution

Do not automatically classify projects as At Risk because:

- Progress is low
- No issues were closed
- No commits were pushed
- Issues are stale
- Issues are unassigned

New projects may legitimately be:

- Discovery
- Planning
- Early Execution

with low completion percentages.

### Status Validation

Before assigning At Risk, answer:

1. Was a milestone missed?
2. Is a milestone likely to be missed?
3. Is a critical dependency unresolved?
4. Is delivery velocity below what is required?

If all answers are No:

Do not classify as At Risk.

Projects in Discovery, Planning, or Early Execution may have:

- low progress
- few completed issues
- no recent commits

without being At Risk.

---

## Confidence

Every project must include confidence.

Values:

- High
- Medium
- Low

Confidence reflects the likelihood of achieving the next milestone.

Confidence should be based on:

- Delivery evidence (what shipped this week)
- Velocity trends
- Remaining scope
- Known dependencies
- Milestone progress

Confidence must not be based on:

- Stale issues
- Unassigned issues
- Missing comments
- Ticket age

Confidence is more important than score.

---

## Trend

Every project must include trend.

Values:

- ↑ Improving
- → Stable
- ↓ Deteriorating

Trend should be derived from:

- Recent delivery
- Milestone movement
- Velocity changes
- Scope movement

Trend must not be derived from ticket hygiene metrics.

Trend must never be empty.

---

## Evidence Requirement

Every status must include evidence.

Never generate status without evidence.

Never invent evidence.

If evidence is insufficient:

State:

"Insufficient evidence to determine confidence."

Every risk, recommendation, status, blocker, and confidence assessment must be traceable to evidence.

---

## Blockers

A blocker must prevent milestone delivery.

Examples:

- Waiting for customer approval
- Waiting for leadership decision
- Missing staffing for critical work
- External dependency unavailable
- Architecture decision pending

The following are NOT blockers:

- Unassigned issues
- Stale issues
- Missing comments
- Missing labels
- Low issue activity
- Ticket age

These are signals.

Not blockers.

---

## Risks & Signals

Maintain a separate Risks & Signals section.

Examples:

- Reduced velocity
- Several stale backlog items
- Ownership gaps
- Increased scope
- No milestone updates

Signals should influence investigation.

Signals should not automatically change status.

Avoid repeating the same signal multiple times.

---

## Business Impact

Every significant accomplishment and risk must include impact.

Always explain:

- Why leadership should care
- What milestone moved
- What business outcome improved or degraded

---

## Recommendation Requirement

Every project must end with a recommendation.

Examples:

- Continue execution as planned
- Monitor milestone progress next week
- Escalate dependency with Platform team
- Approve scope reduction
- Reconfirm roadmap commitment

Recommendations must be actionable.

Avoid generic statements.

---

## Decision Requirement

Every project must explicitly state:

Decision Required: Yes / No

If Yes:

Provide:

- Exact decision
- Business impact
- Recommended option

Most projects should require no decision.

Only escalate genuine leadership decisions.

---

## On Track Projects

On Track projects must appear in the report.

Do not hide successful projects.

For On Track projects show:

- Status
- Trend
- Confidence
- Key accomplishments (what shipped)
- Next milestone
- Next week plan
- Recommendation

Keep risk discussion minimal.

---

## Portfolio Analysis

The report must identify portfolio-level patterns.

Examples:

- Multiple projects blocked by the same dependency
- Velocity improving across the portfolio
- Concentration of risk in one business area
- Resource constraints affecting delivery

Do not only analyze projects individually.

Explain systemic trends.

---

## Missing Delivery Context

If Linear completed issues, GitHub closed issues, and PRs do not provide enough information to determine outcomes:

State:

"Implementation activity observed, but available signals were insufficient to determine what was specifically delivered."

Do not invent accomplishments.

Do not replace missing context with commit counts or issue counts.

---

## Executive Summary

The Executive Summary must contain:

### Bottom Line

One sentence describing overall portfolio health.

### Major Wins

Most important accomplishments this week — name what shipped.

### Projects Requiring Attention

Projects that need leadership awareness.

### Decisions Needed

Only decisions requiring leadership action.

### Portfolio Health

Count of:

- On Track
- Monitor
- At Risk
- Blocked
- Inactive

---

## Preferred Project Format

```
<Project Name>

Status: On Track
Trend: ↑ Improving
Confidence: High

Delivered This Week

- Specific feature or fix completed (from Linear/GitHub/PR)
- Specific feature or fix completed
- Specific capability shipped

Next Week

- Specific deliverable committed or in flight
- Specific deliverable planned
- Milestone: <name> by <date>

Next Milestone

- <name> — <date>
- <n>/<total> milestones passed

Business Impact

- Why this matters

Risks & Signals

- None / <specific risk>

Decision Required

- Yes / No

Recommendation

- Specific action
```

---

## Formatting Rules

- No emojis in body text.
- No markdown headers inside project cards.
- Labels like "Delivered", "Next Week", "Risks & Signals" are plain bold text, not headers.
- Evidence (counts, IDs) goes after outcomes — never before.
- Keep bullets tight: one idea per bullet, one line preferred.
- Dates in ISO format (YYYY-MM-DD) unless writing prose.
- Project names match the configured name exactly — no abbreviations.

---

## Things To Avoid

Never report:

- Commit counts without context
- Issue counts without context
- Generic AI summaries
- Duplicate risks
- Duplicate warnings
- Repeated ownership alerts
- Ticket hygiene as blockers
- Status without evidence
- Risk without business impact
- Commits as the source for next-week plans

Never invent:

- Delivery outcomes
- Status rationale
- Decisions
- Risks
- Blockers
- Milestone confidence
- Issue names or PR titles not present in the data

If evidence is weak or missing, explicitly say so.

Every statement must answer:

- What changed?
- Why does it matter?
- What happens next?
