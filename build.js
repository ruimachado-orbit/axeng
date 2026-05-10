#!/usr/bin/env node
"use strict";
const PptxGenJS = require("pptxgenjs");

// ── MAIO LABS THEME ───────────────────────────────────────────────────────────
const BG      = "FFFFFF";
const CARD    = "F7F7F7";
const ACCENT  = "D4E815";  // lime green (Maio Labs accent)
const BLACK   = "000000";
const WHITE   = "FFFFFF";
const GRAY    = "666666";
const LGRAY   = "AAAAAA";

// Preset factory (avoids object mutation)
function S(pres) {
  const s = pres.addSlide();
  s.background = { color: BG };
  return s;
}

// Solid black top bar (Maio Labs style)
function topBar(s, h = 0.18) {
  s.addShape("rect", { x: 0, y: 0, w: 10, h, fill: { color: BLACK } });
}

// Full-bleed black footer bar
function footerBar(s, label) {
  s.addShape("rect", { x: 0, y: 5.3, w: 10, h: 0.325, fill: { color: BLACK } });
  s.addText(label, {
    x: 0.3, y: 5.33, w: 9.4, h: 0.28,
    fontSize: 9, color: "AAAAAA", fontFace: "Arial", margin: 0,
  });
}

// Reusable card (light gray bg, lime left border)
function card(s, x, y, w, h) {
  s.addShape("rect", {
    x, y, w, h,
    fill: { color: CARD },
    line: { color: CARD },
  });
  // Lime left accent
  s.addShape("rect", { x, y, w: 0.06, h, fill: { color: ACCENT } });
}

// Plain text helper
function txt(s, text, x, y, w, h, opts = {}) {
  s.addText(text, { x, y, w, h, margin: 0, fontFace: "Arial", ...opts });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 1 — Cover
// ─────────────────────────────────────────────────────────────────────────────
function slide1(pres) {
  const s = S(pres);
  topBar(s, 0.22);

  // Logo wordmark
  s.addText("MAIO LABS", {
    x: 0.3, y: 0.05, w: 2.5, h: 0.16,
    fontSize: 9, bold: true, color: "AAAAAA", fontFace: "Arial",
    charSpacing: 3, margin: 0,
  });

  // Large hero title
  txt(s, "Engineering Manager", 0.3, 1.3, 9.4, 0.85,
    { fontSize: 46, bold: true, color: BLACK, fontFace: "Arial Black" });
  txt(s, "in a Box", 0.3, 2.1, 9.4, 0.85,
    { fontSize: 46, bold: true, color: BLACK, fontFace: "Arial Black" });

  // Lime underline
  s.addShape("rect", { x: 0.3, y: 2.98, w: 2.6, h: 0.09, fill: { color: ACCENT } });

  // Subtitle
  txt(s, "Autonomous AI agent that replaces the need for a PM/EM —", 0.3, 3.2, 9.4, 0.38,
    { fontSize: 15, color: GRAY });
  txt(s, "monitors GitHub, Linear, and team activity, generates briefs and reports.", 0.3, 3.55, 9.4, 0.38,
    { fontSize: 15, color: GRAY });

  // Tag badges
  const badges = [
    ["🤖", "AI-Powered"],
    ["📊", "GitHub + Linear"],
    ["⏰", "24/7 Automated"],
    ["📱", "Telegram-native"],
  ];
  badges.forEach(([icon, label], i) => {
    const bx = 0.3 + i * 2.3;
    s.addShape("rect", { x: bx, y: 4.15, w: 2.1, h: 0.42, fill: { color: CARD } });
    txt(s, `${icon}  ${label}`, bx + 0.1, 4.2, 1.9, 0.32,
      { fontSize: 11, bold: true, color: BLACK, valign: "middle" });
  });

  footerBar(s, "github.com/ruimachado-orbit/axeng  |  Rui Machado @ Maio Labs  |  2025");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 2 — The Problem
// ─────────────────────────────────────────────────────────────────────────────
function slide2(pres) {
  const s = S(pres);
  topBar(s);

  // Section label
  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.5, h: 0.32, fill: { color: BLACK } });
  txt(s, "THE PROBLEM", 0.3, 0.48, 1.5, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "Without a PM or EM, you lose control.", 0.3, 0.9, 9.4, 0.7,
    { fontSize: 30, bold: true, color: BLACK, fontFace: "Arial Black" });

  const problems = [
    ["❌", "Untracked work", "Commits happen, issues stay open. No one knows what's done."],
    ["❌", "Invisible blockers", "PRs stack up for days. No one flags them until the retro."],
    ["❌", "Endless status meetings", "Time spent in syncs = time not building."],
    ["❌", "1:1s without prep", "Walking into reviews with no data on the person's progress."],
    ["❌", "Weekly reports by hand", "Hours every Friday copy-pasting from Linear and GitHub."],
  ];

  problems.forEach(([icon, title, sub], i) => {
    const y = 1.75 + i * 0.62;
    card(s, 0.3, y, 9.4, 0.55);
    txt(s, icon, 0.45, y + 0.08, 0.4, 0.38, { fontSize: 14, color: "CC0000" });
    txt(s, title, 0.9, y + 0.06, 2.0, 0.3, { fontSize: 12, bold: true, color: BLACK });
    txt(s, sub, 0.9, y + 0.28, 8.6, 0.25, { fontSize: 10, color: GRAY });
  });

  footerBar(s, "github.com/ruimachado-orbit/axeng  |  Built by Rui Machado @ Maio Labs");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 3 — Meet Axemaster
// ─────────────────────────────────────────────────────────────────────────────
function slide3(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.8, h: 0.32, fill: { color: BLACK } });
  txt(s, "THE SOLUTION", 0.3, 0.48, 1.8, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "Meet Axemaster", 0.3, 0.9, 9.4, 0.75,
    { fontSize: 36, bold: true, color: BLACK, fontFace: "Arial Black" });
  txt(s, "Your AI Chief of Staff", 0.3, 1.6, 9.4, 0.42,
    { fontSize: 18, bold: true, color: GRAY });

  // Lime rule
  s.addShape("rect", { x: 0.3, y: 2.1, w: 1.8, h: 0.08, fill: { color: ACCENT } });

  const points = [
    ["24/7 Autonomous", "Cron jobs run every morning, afternoon, and week-end. No reminders needed."],
    ["Context-Aware", "Remembers every session via Obsidian. Cross-session continuity."],
    ["Zero Friction", "Talk to it via Telegram. No dashboards to open, no tickets to file."],
    ["Multi-Source", "Pulls from GitHub, Linear, Gmail, Calendar, Google Chat simultaneously."],
  ];

  points.forEach(([title, desc], i) => {
    const y = 2.35 + i * 0.68;
    card(s, 0.3, y, 9.4, 0.62);
    txt(s, title, 0.5, y + 0.06, 2.5, 0.28, { fontSize: 12, bold: true, color: BLACK });
    txt(s, desc, 0.5, y + 0.3, 9.0, 0.28, { fontSize: 11, color: GRAY });
  });

  footerBar(s, "github.com/ruimachado-orbit/axeng  |  Rui Machado @ Maio Labs");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 4 — How It Works
// ─────────────────────────────────────────────────────────────────────────────
function slide4(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.8, h: 0.32, fill: { color: BLACK } });
  txt(s, "HOW IT WORKS", 0.3, 0.48, 1.8, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "The data flows in. The briefs flow out.", 0.3, 0.9, 9.4, 0.65,
    { fontSize: 28, bold: true, color: BLACK, fontFace: "Arial Black" });

  const flow = [
    { icon: "📅", title: "Linear", sub: "Issues, sprints, projects, priorities" },
    { icon: "🐙", title: "GitHub", sub: "Commits, PRs, reviews, repos" },
    { icon: "📧", title: "Calendar", sub: "Meetings, OOO, 1:1s" },
    { icon: "📬", title: "Gmail", sub: "Threads, decisions, announcements" },
    { icon: "🌐", title: "Chat", sub: "Google Chat rooms + DMs" },
    { icon: "📰", title: "News", sub: "World news for briefings" },
  ];

  const cols = 3;
  flow.forEach((item, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const bx = 0.3 + col * 3.15;
    const by = 1.65 + row * 1.55;

    s.addShape("rect", { x: bx, y: by, w: 2.95, h: 1.35, fill: { color: CARD } });
    // Lime top border
    s.addShape("rect", { x: bx, y: by, w: 2.95, h: 0.07, fill: { color: ACCENT } });

    txt(s, item.icon, bx, by + 0.15, 2.95, 0.45, { fontSize: 26, align: "center" });
    txt(s, item.title, bx + 0.12, by + 0.6, 2.71, 0.28,
      { fontSize: 13, bold: true, color: BLACK, align: "center" });
    txt(s, item.sub, bx + 0.12, by + 0.88, 2.71, 0.38,
      { fontSize: 10, color: GRAY, align: "center" });
  });

  // Arrow to Axemaster
  s.addShape("rect", { x: 4.5, y: 4.78, w: 1.0, h: 0.38, fill: { color: BLACK } });
  txt(s, "→  AXEMASTER", 4.55, 4.8, 0.9, 0.34,
    { fontSize: 9, bold: true, color: ACCENT });

  footerBar(s, "github.com/ruimachado-orbit/axeng  |  Rui Machado @ Maio Labs");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 5 — What It Actually Does
// ─────────────────────────────────────────────────────────────────────────────
function slide5(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.8, h: 0.32, fill: { color: BLACK } });
  txt(s, "CAPABILITIES", 0.3, 0.48, 1.8, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "What it actually does", 0.3, 0.9, 9.4, 0.65,
    { fontSize: 28, bold: true, color: BLACK, fontFace: "Arial Black" });

  const feats = [
    { icon: "🏃", title: "Daily Standup Brief", time: "Mon–Fri 07:30",
      desc: "What shipped, blockers, PRs >48h, who's OOO → Telegram" },
    { icon: "📋", title: "1:1 Pre-reads", time: "Before every 1:1",
      desc: "对方的 issues, commits, pending PRs, last notes → ready in seconds" },
    { icon: "📊", title: "Weekly Team Report", time: "Friday 17:00",
      desc: "Per-project status, MVP of the week, roadmap analysis → Email + Linear" },
    { icon: "📈", title: "Sprint Health", time: "Friday 16:00",
      desc: "Health scores (0–100), scope creep detection, burn rate → Telegram" },
    { icon: "🔭", title: "Risk Radar", time: "Friday 16:00",
      desc: "Quiet repos, overloaded members, overdue issues → proactive alerts" },
    { icon: "🔄", title: "Vault Sync", time: "Daily",
      desc: "GitHub activity → Obsidian. Team profiles, session logs, context" },
  ];

  const cols = 2;
  feats.forEach((f, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const bx = 0.3 + col * 4.85;
    const by = 1.65 + row * 1.22;

    s.addShape("rect", { x: bx, y: by, w: 4.65, h: 1.1, fill: { color: CARD } });
    s.addShape("rect", { x: bx, y: by, w: 4.65, h: 0.06, fill: { color: ACCENT } });
    txt(s, f.icon, bx + 0.12, by + 0.12, 0.55, 0.42, { fontSize: 20 });
    txt(s, f.title, bx + 0.72, by + 0.1, 3.7, 0.28,
      { fontSize: 12, bold: true, color: BLACK });
    txt(s, f.time, bx + 0.72, by + 0.34, 3.7, 0.22,
      { fontSize: 9, bold: true, color: ACCENT });
    txt(s, f.desc, bx + 0.72, by + 0.56, 3.8, 0.48,
      { fontSize: 10, color: GRAY });
  });

  footerBar(s, "github.com/ruimachado-orbit/axeng  |  Rui Machado @ Maio Labs");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 6 — Section Divider: Under the Hood
// ─────────────────────────────────────────────────────────────────────────────
function slide6(pres) {
  const s = S(pres);

  // Full black background for impact
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 5.625, fill: { color: BLACK } });

  s.addText("MAIO LABS", {
    x: 0.3, y: 0.3, w: 2.5, h: 0.25,
    fontSize: 10, bold: true, color: "555555", fontFace: "Arial",
    charSpacing: 4, margin: 0,
  });

  s.addShape("rect", { x: 0.3, y: 0.85, w: 0.8, h: 0.06, fill: { color: ACCENT } });

  s.addText("Under the Hood", {
    x: 0.3, y: 1.1, w: 9.4, h: 1.1,
    fontSize: 52, bold: true, color: WHITE, fontFace: "Arial Black", margin: 0,
  });

  s.addText("Full architecture, cron jobs, and automation logic", {
    x: 0.3, y: 2.3, w: 7.5, h: 0.45,
    fontSize: 16, color: "888888", fontFace: "Arial", margin: 0,
  });

  // Mini flow preview
  const items = ["Linear", "GitHub", "Gmail", "Calendar", "Chat"];
  items.forEach((item, i) => {
    const bx = 0.3 + i * 1.9;
    s.addShape("rect", { x: bx, y: 3.1, w: 1.7, h: 0.42, fill: { color: "1A1A1A" } });
    txt(s, item, bx, 3.14, 1.7, 0.34,
      { fontSize: 10, bold: true, color: "888888", align: "center" });
    if (i < items.length - 1)
      txt(s, "→", bx + 1.7, 3.12, 0.2, 0.34, { fontSize: 14, color: ACCENT, align: "center" });
  });

  s.addShape("rect", { x: 0.3, y: 3.7, w: 1.7, h: 0.05, fill: { color: ACCENT } });
  txt(s, "→ AXEMASTER", 0.3, 3.8, 1.7, 0.32,
    { fontSize: 10, bold: true, color: ACCENT, align: "center" });

  s.addText("github.com/ruimachado-orbit/axeng", {
    x: 0.3, y: 5.15, w: 9.4, h: 0.3,
    fontSize: 11, color: "555555", fontFace: "Arial", margin: 0,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 7 — 24/7 Autonomous Operation
// ─────────────────────────────────────────────────────────────────────────────
function slide7(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.8, h: 0.32, fill: { color: BLACK } });
  txt(s, "AUTOMATION", 0.3, 0.48, 1.8, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "24/7 Autonomous Operation", 0.3, 0.9, 9.4, 0.65,
    { fontSize: 28, bold: true, color: BLACK, fontFace: "Arial Black" });

  // Morning
  s.addShape("rect", { x: 0.3, y: 1.65, w: 1.2, h: 0.32, fill: { color: ACCENT } });
  txt(s, "☀️  MORNING", 0.3, 1.68, 1.2, 0.28,
    { fontSize: 9, bold: true, color: BLACK, align: "center" });

  const morning = [
    ["07:30", "Daily Standup Brief", "What shipped, blockers, PRs >48h, who's OOO → Telegram"],
    ["07:30", "TL;DR", "Quick snapshot of the day ahead → Telegram"],
    ["08:00", "Email Briefing", "Calendar, Linear actions, CI failures, world news → Inbox"],
  ];
  morning.forEach(([time, name, desc], i) => {
    const y = 2.05 + i * 0.52;
    card(s, 0.3, y, 9.4, 0.46);
    txt(s, time, 0.45, y + 0.08, 0.8, 0.28, { fontSize: 9, bold: true, color: BLACK });
    txt(s, name, 1.3, y + 0.06, 2.2, 0.26, { fontSize: 11, bold: true, color: BLACK });
    txt(s, desc, 1.3, y + 0.28, 8.2, 0.22, { fontSize: 9, color: GRAY });
  });

  // Afternoon
  s.addShape("rect", { x: 0.3, y: 3.68, w: 1.5, h: 0.32, fill: { color: BLACK } });
  txt(s, "🌙  AFTERNOON", 0.3, 3.71, 1.5, 0.28,
    { fontSize: 9, bold: true, color: ACCENT, align: "center" });

  const afternoon = [
    ["Every 5min", "Pre-meeting Brief", "10–20 min before every calendar event → Telegram"],
    ["18:00", "End-of-day Digest", "Day summary, tomorrow preview, pending PRs → Telegram"],
  ];
  afternoon.forEach(([time, name, desc], i) => {
    const y = 4.08 + i * 0.52;
    card(s, 0.3, y, 9.4, 0.46);
    txt(s, time, 0.45, y + 0.08, 1.1, 0.28, { fontSize: 9, bold: true, color: BLACK });
    txt(s, name, 1.6, y + 0.06, 2.2, 0.26, { fontSize: 11, bold: true, color: BLACK });
    txt(s, desc, 1.6, y + 0.28, 8.0, 0.22, { fontSize: 9, color: GRAY });
  });

  footerBar(s, "⏰ LaunchAgents on Mac Mini M1  •  No LLM in cron path  •  Idempotent — safe to re-run");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 8 — Low-PM Structure
// ─────────────────────────────────────────────────────────────────────────────
function slide8(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 2.0, h: 0.32, fill: { color: BLACK } });
  txt(s, "FOUNDATION LAYER", 0.3, 0.48, 2.0, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "The Low-PM Structure", 0.3, 0.9, 9.4, 0.65,
    { fontSize: 28, bold: true, color: BLACK, fontFace: "Arial Black" });
  txt(s, "How Hermes became the chief of staff that replaces the need for a PM/EM",
    0.3, 1.52, 9.4, 0.3, { fontSize: 12, color: GRAY });

  // Left column
  txt(s, "What a PM/EM typically does", 0.3, 1.95, 4.2, 0.28,
    { fontSize: 10, bold: true, color: LGRAY });

  const pm_tasks = [
    "Triage and prioritize incoming requests",
    "Track progress across projects",
    "Prepare 1:1s and performance reviews",
    "Write specs, PRDs, and status updates",
    "Coordinate across teams and timezones",
    "Flag blockers and escalate when needed",
  ];
  pm_tasks.forEach((task, i) => {
    txt(s, `✗  ${task}`, 0.3, 2.28 + i * 0.38, 4.2, 0.32,
      { fontSize: 11, color: LGRAY });
  });

  // Arrow
  s.addShape("rect", { x: 4.55, y: 2.9, w: 0.45, h: 1.15, fill: { color: CARD } });
  txt(s, "→", 4.55, 2.95, 0.45, 1.05,
    { fontSize: 24, bold: true, color: ACCENT, align: "center", valign: "middle" });

  // Right column
  s.addShape("rect", { x: 5.15, y: 1.95, w: 4.55, h: 3.2, fill: { color: CARD } });
  s.addShape("rect", { x: 5.15, y: 1.95, w: 4.55, h: 0.06, fill: { color: ACCENT } });
  txt(s, "What Hermes does instead", 5.3, 2.05, 4.2, 0.28,
    { fontSize: 10, bold: true, color: BLACK });

  const hermes_tasks = [
    ["🤖", "Screens every request via Telegram"],
    ["📋", "Owns Linear + GitHub as live tracker"],
    ["📅", "Auto-preps 1:1s from calendar events"],
    ["✍️", "Generates briefs, reports, and digests"],
    ["🔔", "Alerts on blockers, CI failures, velocity"],
    ["🧠", "Remembers everything via Obsidian"],
  ];
  hermes_tasks.forEach(([icon, text], i) => {
    txt(s, `${icon}  ${text}`, 5.3, 2.4 + i * 0.4, 4.3, 0.35,
      { fontSize: 11, color: BLACK, valign: "middle" });
  });

  // Bottom note
  s.addShape("rect", { x: 0.3, y: 5.05, w: 9.4, h: 0.18, fill: { color: CARD } });
  txt(s, "⚡  Low-PM model: every repetitive PM task is automated through Hermes → Axemaster → Cron scripts",
    0.4, 5.07, 9.2, 0.14, { fontSize: 9, color: GRAY });

  footerBar(s, "github.com/ruimachado-orbit/axeng  |  Rui Machado @ Maio Labs");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 9 — Linear Integration
// ─────────────────────────────────────────────────────────────────────────────
function slide9(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.8, h: 0.32, fill: { color: BLACK } });
  txt(s, "LINEAR", 0.3, 0.48, 1.8, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "Bidirectional Linear Integration", 0.3, 0.9, 9.4, 0.65,
    { fontSize: 28, bold: true, color: BLACK, fontFace: "Arial Black" });
  txt(s, "Cross-referencing GitHub commits with Linear issues — track real progress, not just intentions",
    0.3, 1.52, 9.4, 0.3, { fontSize: 12, color: GRAY });

  const steps = [
    { icon: "📥", title: "FETCH", sub: "GraphQL → issues, sprints, projects, team members\nTeam: maiolabs | API Key: MAI" },
    { icon: "🔍", title: "ANALYZE", sub: "GitHub commits → Linear keywords\nIn-progress? Blocked? Scope creep?" },
    { icon: "📤", title: "UPDATE", sub: "Sprint health → Linear desc\nWeekly summary → each project\nIdempotent writes" },
    { icon: "📊", title: "REPORT", sub: "Per-project commit cards\nRoadmap state → Email + Obsidian" },
  ];

  const boxW = 2.2;
  const boxH = 2.0;
  const startX = 0.3;
  const startY = 1.95;
  const gap = 0.28;

  steps.forEach((step, i) => {
    const bx = startX + i * (boxW + gap);
    s.addShape("rect", { x: bx, y: startY, w: boxW, h: boxH, fill: { color: CARD } });
    s.addShape("rect", { x: bx, y: startY, w: boxW, h: 0.06, fill: { color: ACCENT } });
    txt(s, step.icon, bx, startY + 0.15, boxW, 0.5, { fontSize: 26, align: "center" });
    txt(s, step.title, bx, startY + 0.65, boxW, 0.32,
      { fontSize: 12, bold: true, color: BLACK, align: "center" });
    txt(s, step.sub, bx + 0.1, startY + 1.0, boxW - 0.2, 0.92,
      { fontSize: 9, color: GRAY, valign: "top" });
    if (i < steps.length - 1)
      txt(s, "→", bx + boxW + 0.02, startY + boxH / 2 - 0.2, gap - 0.04, 0.4,
        { fontSize: 16, color: ACCENT, align: "center", valign: "middle" });
  });

  footerBar(s, "github.com/ruimachado-orbit/axeng  |  Rui Machado @ Maio Labs");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 10 — 1:1 Pre-reads
// ─────────────────────────────────────────────────────────────────────────────
function slide10(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.8, h: 0.32, fill: { color: BLACK } });
  txt(s, "1:1 AUTOMATION", 0.3, 0.48, 1.8, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "1:1 Pre-reads — Fully Automated", 0.3, 0.9, 9.4, 0.65,
    { fontSize: 28, bold: true, color: BLACK, fontFace: "Arial Black" });
  txt(s, "Calendar event detected → \"1:1\" / \"sync\" in title → AI prepares everything",
    0.3, 1.52, 9.4, 0.3, { fontSize: 12, color: GRAY });

  // Left: what it fetches
  s.addShape("rect", { x: 0.3, y: 1.95, w: 4.4, h: 3.2, fill: { color: CARD } });
  s.addShape("rect", { x: 0.3, y: 1.95, w: 4.4, h: 0.06, fill: { color: ACCENT } });
  txt(s, "📥  WHAT IT FETCHES", 0.45, 2.06, 4.1, 0.32,
    { fontSize: 11, bold: true, color: BLACK });

  const fetches = [
    "Open Linear issues + priority tags for the person",
    "GitHub commits this week from that person",
    "PRs authored waiting for review",
    "Last 1:1 notes from Obsidian vault",
    "14-day sprint velocity (completed issues)",
  ];
  fetches.forEach((item, i) => {
    s.addShape("rect", { x: 0.45, y: 2.45 + i * 0.48, w: 0.06, h: 0.3, fill: { color: ACCENT } });
    txt(s, item, 0.6, 2.48 + i * 0.48, 4.0, 0.38, { fontSize: 10, color: BLACK });
  });

  // Right: what it generates
  s.addShape("rect", { x: 5.3, y: 1.95, w: 4.4, h: 3.2, fill: { color: CARD } });
  s.addShape("rect", { x: 5.3, y: 1.95, w: 4.4, h: 0.06, fill: { color: BLACK } });
  txt(s, "📤  WHAT IT GENERATES", 5.45, 2.06, 4.1, 0.32,
    { fontSize: 11, bold: true, color: BLACK });

  const outputs = [
    { icon: "🎯", title: "Talking Points", sub: "Auto-generated from issues + commits" },
    { icon: "⚠️", title: "Blockers", sub: "PRs stale >48h, silent issues" },
    { icon: "📊", title: "Velocity", sub: "14-day burn rate vs. sprint average" },
    { icon: "📝", title: "Notes Summary", sub: "Last 1:1 + open thread count" },
  ];
  outputs.forEach((o, i) => {
    txt(s, o.icon, 5.45, 2.48 + i * 0.62, 0.4, 0.4, { fontSize: 16 });
    txt(s, o.title, 5.88, 2.46 + i * 0.62, 3.7, 0.26, { fontSize: 11, bold: true, color: BLACK });
    txt(s, o.sub, 5.88, 2.68 + i * 0.62, 3.7, 0.24, { fontSize: 9, color: GRAY });
  });

  footerBar(s, "github.com/ruimachado-orbit/axeng  |  Rui Machado @ Maio Labs");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 11 — Long-term Memory (Obsidian)
// ─────────────────────────────────────────────────────────────────────────────
function slide11(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.8, h: 0.32, fill: { color: BLACK } });
  txt(s, "MEMORY", 0.3, 0.48, 1.8, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "Long-term Memory — Obsidian Integration", 0.3, 0.9, 9.4, 0.65,
    { fontSize: 28, bold: true, color: BLACK, fontFace: "Arial Black" });
  txt(s, "Every session logged. Context never lost. Cross-session continuity guaranteed.",
    0.3, 1.52, 9.4, 0.3, { fontSize: 12, color: GRAY });

  // Layer 1
  s.addShape("rect", { x: 0.3, y: 1.95, w: 9.4, h: 1.4, fill: { color: CARD } });
  s.addShape("rect", { x: 0.3, y: 1.95, w: 9.4, h: 0.06, fill: { color: ACCENT } });
  txt(s, "💬  Layer 1 — Session Logger", 0.45, 2.06, 4, 0.3,
    { fontSize: 12, bold: true, color: BLACK });
  txt(s, "After every action during conversation", 5.5, 2.06, 4.2, 0.3,
    { fontSize: 10, bold: true, color: GRAY });
  const l1 = [
    "• Decision made during session",
    "• File created or altered",
    "• Task opened or closed",
    "• Command executed with result",
  ];
  l1.forEach((t, i) => {
    txt(s, t, 0.5, 2.42 + i * 0.22, 9.1, 0.22, { fontSize: 10, color: BLACK });
  });
  s.addShape("rect", { x: 0.3, y: 3.4, w: 0.06, h: 0.3, fill: { color: ACCENT } });
  txt(s, "path: sessoes/YYYY-MM-DD.md", 0.45, 3.42, 9.0, 0.22,
    { fontSize: 9, bold: true, color: BLACK });

  // Layer 2
  s.addShape("rect", { x: 0.3, y: 3.65, w: 9.4, h: 1.2, fill: { color: CARD } });
  s.addShape("rect", { x: 0.3, y: 3.65, w: 9.4, h: 0.06, fill: { color: BLACK } });
  txt(s, "📅  Layer 2 — 7-Day Rolling Detail", 0.45, 3.76, 5, 0.3,
    { fontSize: 12, bold: true, color: BLACK });
  txt(s, "Incremental writes, no end-of-session needed", 5.5, 3.76, 4.2, 0.3,
    { fontSize: 10, bold: true, color: GRAY });
  const l2 = [
    "• Last 7 days as full detailed logs",
    "• Automatic append on new actions",
    "• Obsidian → Cross-session context window",
  ];
  l2.forEach((t, i) => {
    txt(s, t, 0.5, 4.1 + i * 0.22, 9.0, 0.22, { fontSize: 10, color: BLACK });
  });

  footerBar(s, "github.com/ruimachado-orbit/axeng  |  Rui Machado @ Maio Labs");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 12 — Complete System Architecture
// ─────────────────────────────────────────────────────────────────────────────
function slide12(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.8, h: 0.32, fill: { color: BLACK } });
  txt(s, "ARCHITECTURE", 0.3, 0.48, 1.8, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "Complete System Architecture", 0.3, 0.9, 9.4, 0.65,
    { fontSize: 28, bold: true, color: BLACK, fontFace: "Arial Black" });
  txt(s, "From data sources to autonomous intelligence — every component explained",
    0.3, 1.52, 9.4, 0.3, { fontSize: 12, color: GRAY });

  // Sources row
  const sources = ["📅 Linear", "🐙 GitHub", "📧 Gmail", "📬 Calendar", "🌐 Chat", "📰 News"];
  sources.forEach((src, i) => {
    const bx = 0.3 + i * 1.58;
    s.addShape("rect", { x: bx, y: 1.95, w: 1.48, h: 0.42, fill: { color: CARD } });
    txt(s, src, bx, 1.98, 1.48, 0.36,
      { fontSize: 9, bold: true, color: BLACK, align: "center", valign: "middle" });
  });

  // Arrows down
  sources.forEach((_, i) => {
    const bx = 0.3 + i * 1.58;
    txt(s, "↓", bx + 0.64, 2.4, 0.2, 0.22, { fontSize: 12, color: ACCENT, align: "center" });
  });

  // Axemaster core
  s.addShape("rect", { x: 1.5, y: 2.65, w: 7.0, h: 1.55, fill: { color: BLACK } });
  s.addShape("rect", { x: 1.5, y: 2.65, w: 7.0, h: 0.06, fill: { color: ACCENT } });
  txt(s, "🤖  AXEMASTER", 1.65, 2.76, 3, 0.42,
    { fontSize: 16, bold: true, color: ACCENT });
  txt(s, "AI Chief of Staff", 4.7, 2.84, 3.7, 0.28, { fontSize: 10, color: "888888" });

  const inputProcs = [
    ["github_activity.py", "Commits, PRs, repos"],
    ["linear_tool.py", "Issues, sprints, projects"],
    ["calendar_insights.py", "Events, OOO, meetings"],
    ["email_intel.py", "Inbox, threads, decisions"],
  ];
  inputProcs.forEach(([name, desc], i) => {
    const px = 1.65 + i * 1.72;
    txt(s, name, px, 3.22, 1.62, 0.24, { fontSize: 8, bold: true, color: WHITE });
    txt(s, desc, px, 3.44, 1.62, 0.24, { fontSize: 8, color: "888888" });
  });
  txt(s, "↓", 4.75, 4.22, 0.2, 0.18, { fontSize: 11, color: ACCENT, align: "center" });

  // Output destinations
  const dests = ["📱 Telegram", "📧 Email", "💾 Obsidian", "🖥️ Streamlit"];
  const destW = 2.2;
  const destStartX = 0.55;
  dests.forEach((dest, i) => {
    const dx = destStartX + i * (destW + 0.14);
    txt(s, "↓", dx + destW / 2 - 0.1, 4.42, 0.2, 0.18, { fontSize: 9, color: ACCENT });
    s.addShape("rect", { x: dx, y: 4.62, w: destW, h: 0.38, fill: { color: CARD } });
    txt(s, dest, dx, 4.65, destW, 0.32,
      { fontSize: 9, bold: true, color: BLACK, align: "center", valign: "middle" });
  });

  footerBar(s, "🔀 orchestrator.py routes natural language → correct tool  •  LLM for reasoning, not data fetching");
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 13 — Screenshots / What It Looks Like
// ─────────────────────────────────────────────────────────────────────────────
function slide13(pres) {
  const s = S(pres);
  topBar(s);

  s.addShape("rect", { x: 0.3, y: 0.45, w: 1.8, h: 0.32, fill: { color: BLACK } });
  txt(s, "DEMO", 0.3, 0.48, 1.8, 0.28,
    { fontSize: 8, bold: true, color: ACCENT, charSpacing: 2, align: "center" });

  txt(s, "What It Looks Like in Practice", 0.3, 0.9, 9.4, 0.65,
    { fontSize: 28, bold: true, color: BLACK, fontFace: "Arial Black" });
  txt(s, "Real outputs from the system — screenshots from Telegram, email, and Streamlit",
    0.3, 1.52, 9.4, 0.3, { fontSize: 12, color: GRAY });

  const screens = [
    { label: "Screenshot 1", sub: "Telegram Standup Brief", hint: "Daily brief — what shipped, blockers, PRs" },
    { label: "Screenshot 2", sub: "Weekly HTML Report", hint: "Per-project commits, MVP podium, roadmap" },
    { label: "Screenshot 3", sub: "Streamlit Web UI", hint: "Dashboard, config, run reports" },
    { label: "Screenshot 4", sub: "Obsidian Vault", hint: "Team profiles, sessions, team overview" },
  ];

  const boxW = 4.4;
  const boxH = 1.7;
  const starts = [[0.3, 1.95], [5.3, 1.95], [0.3, 3.82], [5.3, 3.82]];

  screens.forEach((scr, i) => {
    const [sx, sy] = starts[i];
    s.addShape("rect", {
      x: sx, y: sy, w: boxW, h: boxH,
      fill: { color: CARD },
      line: { color: LGRAY, width: 1 },
    });
    // Dashed effect (multiple small rects)
    s.addShape("rect", {
      x: sx + 0.8, y: sy + boxH / 2 - 0.3, w: boxW - 1.6, h: 0.01,
      fill: { color: LGRAY },
    });
    txt(s, scr.label, sx, sy + 0.12, boxW, 0.3,
      { fontSize: 12, bold: true, color: BLACK, align: "center" });
    txt(s, scr.sub, sx, sy + 0.45, boxW, 0.28,
      { fontSize: 11, color: GRAY, align: "center" });
    txt(s, scr.hint, sx, sy + 0.75, boxW, 0.25,
      { fontSize: 9, color: LGRAY, align: "center" });
    txt(s, ["📱", "📊", "🌐", "📓"][i], sx, sy + 1.1, boxW, 0.42,
      { fontSize: 22, align: "center", color: LGRAY });
    txt(s, "800 × 450 px", sx, sy + boxH - 0.25, boxW, 0.2,
      { fontSize: 8, color: LGRAY, align: "center" });
  });

  footerBar(s, "💡 Tip: Take screenshots from Telegram, email client, and Streamlit at localhost:8501");
}

// ─────────────────────────────────────────────────────────────────────────────
// BUILD
// ─────────────────────────────────────────────────────────────────────────────
const pres = new PptxGenJS();
pres.layout = "LAYOUT_16x9";

slide1(pres);
slide2(pres);
slide3(pres);
slide4(pres);
slide5(pres);
slide6(pres);
slide7(pres);
slide8(pres);
slide9(pres);
slide10(pres);
slide11(pres);
slide12(pres);
slide13(pres);

pres.writeFile({ fileName: "/tmp/axeng-maiolabs.pptx" })
  .then(() => console.log("✅ /tmp/axeng-maiolabs.pptx"))
  .catch(e => console.error("ERROR:", e));
