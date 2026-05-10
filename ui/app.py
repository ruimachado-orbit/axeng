"""
Axeng — Streamlit Web UI
Config, dashboard, and manual report trigger for the EM Accelerator.
"""
import os, sys, json, yaml, subprocess
from pathlib import Path
from datetime import datetime

import streamlit as st

SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR / "src"))
from llm_gateway import status as llm_status, PROVIDERS, get_available_providers

# ── Paths ─────────────────────────────────────────────────────────
CONFIG_FILE = SCRIPT_DIR / "config" / "config.yaml"
VAULT_DIR = SCRIPT_DIR / "vault"
REPORTS_DIR = SCRIPT_DIR / "reports"
SESSIONS_DIR = VAULT_DIR / "Rui" / "sessoes"

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Axeng — EM Accelerator",
    page_icon="🤖",
    layout="wide",
    menu_items={
        "About": "# Axeng\nEngineering Manager Accelerator — autonomous intelligence agent.",
        "Get help": "https://github.com/ruimachado-orbit/axeng",
    },
)

# ── Load / save config ────────────────────────────────────────────
def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f)
    return {}

def save_config(cfg: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

# ── Header ────────────────────────────────────────────────────────
st.title("🤖 Axeng — EM Accelerator")
st.caption(f"Session: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Lisbon time")

# ── Sidebar nav ──────────────────────────────────────────────────
page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "🧠 LLM Settings", "⚙️ Configuration", "📋 Reports", "👥 Team", "🔧 Run Reports"],
    index=0,
)

# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.header("Dashboard")

    # Quick stats row
    col1, col2, col3 = st.columns(3)

    # Sessions last 7 days
    if SESSIONS_DIR.exists():
        sessions = sorted(SESSIONS_DIR.glob("????-??-??.md"))
        recent = [s for s in sessions if True]  # all, already filtered by naming
        col1.metric("Sessions logged", len(recent), help="Last 7 days")
    else:
        col1.metric("Sessions logged", "—", help="No vault connected")

    # Config status
    cfg = load_config()
    if cfg:
        teams = cfg.get("team", [])
        col2.metric("Team members", len(teams) if teams else 0)
        col3.metric("Projects configured", len(cfg.get("linear", {}).get("projects", {})))
    else:
        col2.metric("Team members", "⚠️ Not configured")
        col3.metric("Projects configured", "0")

    st.divider()

    # LLM Provider status
    st.subheader("🧠 LLM Providers")
    with st.container():
        prov_cols = st.columns(min(len(PROVIDERS), 4))
        prov_status = llm_status()
        available_count = sum(1 for v in prov_status.values() if v["available"])
        st.caption(f"{available_count}/{len(prov_status)} providers configured")

        for i, (pid, info) in enumerate(PROVIDERS.items()):
            col = prov_cols[i % len(prov_cols)]
            s = prov_status.get(pid, {})
            icon = "🟢" if s.get("available") else "⚪"
            name = info["name"].split("(")[0].strip()
            local_tag = " (local)" if info.get("is_local") else ""
            if s.get("is_running") and not s.get("has_api_key"):
                subtitle = "● running"
            elif s.get("has_api_key"):
                subtitle = "✓ key set"
            else:
                subtitle = "○ not set"
            with col:
                st.markdown(f"**{icon} {name}{local_tag}**")
                st.caption(subtitle)

    # Recent activity
    st.subheader("📅 Recent Sessions")
    if SESSIONS_DIR.exists():
        for session in sorted(SESSIONS_DIR.glob("????-??-??.md"), reverse=True)[:7]:
            date_str = session.stem
            content = session.read_text()
            # Extract theme
            theme = ""
            for line in content.split("\n"):
                if line.startswith("**Tema:**"):
                    theme = line.replace("**Tema:**", "").strip()
                    break
            # Extract actions count
            actions = [l for l in content.split("\n") if l.startswith("- ") and "✅" not in l]
            with st.expander(f"📅 {date_str}{' — ' + theme if theme else ''}"):
                st.markdown(content)
    else:
        st.info("📂 No vault connected. Set up your vault path in `config/config.yaml`.")

    # Reports summary
    st.subheader("📈 Recent Reports")
    if REPORTS_DIR.exists():
        reports = sorted(REPORTS_DIR.glob("*.html"), reverse=True)[:5]
        if reports:
            for r in reports:
                col_date, col_size = st.columns([3, 1])
                with col_date:
                    st.write(f"📄 `{r.name}`")
                with col_size:
                    size = r.stat().st_size // 1024
                    st.caption(f"{size} KB")
        else:
            st.info("No reports generated yet. Run a report to see them here.")
    else:
        st.info("Reports directory not found. Configure `output_dir` in `config/config.yaml`.")

# ═══════════════════════════════════════════════════════════════
# LLM SETTINGS
# ═══════════════════════════════════════════════════════════════
elif page == "🧠 LLM Settings":
    st.header("🧠 LLM Provider Settings")
    st.markdown("Configure which LLM providers to use. Axeng auto-detects running local servers.")

    prov_status = llm_status()
    available = get_available_providers()
    available_ids = [p[0] for p in available]

    # Env instructions
    with st.expander("📄 How to get API keys + set up local providers"):
        st.markdown("""
**Cloud Providers:**
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com) → API Keys
- **OpenAI**: [platform.openai.com](https://platform.openai.com) → API Keys
- **OpenCode**: Sign up at [opencode.ai](https://opencode.ai)
- **Groq**: [console.groq.com](https://console.groq.com) → API Keys (free tier)
- **OpenRouter**: [openrouter.ai](https://openrouter.ai/keys) → API Keys
- **Google AI**: [aistudio.google.com](https://aistudio.google.com/app/apikey)

**Local Providers (no API key needed):**
- **Ollama**: `brew install ollama` → `ollama serve` → runs on `localhost:11434`
- **LM Studio**: Download from [lmstudio.ai](https://lmstudio.ai) → run the app → API server on `localhost:1234`
""")

    # Provider status table
    st.subheader("Provider Status")
    data = []
    for pid, info in PROVIDERS.items():
        s = prov_status.get(pid, {})
        if s.get("has_api_key"):
            key_status = "✅ Key set"
        elif s.get("is_running"):
            key_status = "🟢 Server running"
        else:
            key_status = "○ Not configured"
        data.append({
            "Provider": info["name"],
            "Type": "Local" if info.get("is_local") else "Cloud",
            "Default Model": info.get("default_model", ""),
            "Status": key_status,
        })
    st.dataframe(data, use_container_width=True, hide_index=True)

    st.divider()

    # Test LLM call
    st.subheader("🧪 Test LLM")
    test_col1, test_col2 = st.columns([3, 1])
    with test_col1:
        test_prompt = st.text_area(
            "Test prompt",
            value="Say hello in 3 words",
            height=60,
            label_visibility="collapsed",
        )
    with test_col2:
        test_provider = st.selectbox(
            "Provider",
            options=list(PROVIDERS.keys()),
            index=0,
            format_func=lambda p: PROVIDERS[p]["name"],
        )
        test_btn = st.button("▶️ Send", use_container_width=True)

    if test_btn and test_prompt:
        with st.spinner(f"Calling {PROVIDERS[test_provider]['name']}..."):
            from llm_gateway import call
            result = call(test_prompt, provider=test_provider)
            if result.get("ok"):
                st.success(f"✅ {result.get('provider', '')}/{result.get('model', '')} → {result['text'][:200]}")
                with st.expander("Full response"):
                    st.markdown(result["text"])
            else:
                st.error(f"❌ {result.get('error', 'Unknown error')}")

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════
elif page == "⚙️ Configuration":
    st.header("⚙️ Configuration")
    st.info("💡 Edit `config/config.yaml` directly or use the fields below.")

    cfg = load_config()

    with st.form("config_editor"):
        st.subheader("📧 Email")
        email_recipients = st.text_input(
            "Recipients (comma-separated)",
            value=", ".join(cfg.get("email", {}).get("recipients", [])),
        )
        email_from = st.text_input(
            "From address",
            value=cfg.get("email", {}).get("from", ""),
        )

        st.subheader("🐙 GitHub")
        gh_orgs = st.text_area(
            "Organizations (one per line)",
            value="\n".join(cfg.get("github", {}).get("orgs", [])),
        )
        gh_repos = st.text_area(
            "Additional repos (org/repo format, one per line)",
            value="\n".join(cfg.get("github", {}).get("repos", [])),
        )

        st.subheader("🔗 Linear")
        linear_projects_raw = cfg.get("linear", {}).get("projects", {})
        linear_ids_raw = cfg.get("linear", {}).get("project_ids", {})

        st.write("**Projects configured:**")
        for proj, info in linear_projects_raw.items():
            st.code(f"{proj} → owner: {info.get('owner', '?')}, repos: {info.get('repos', [])}")

        st.caption("💡 To add Linear projects, edit `config/config.yaml` directly. "
                   "Get project IDs from Linear URL: `app.linear.app/<workspace>/project/<slug>/<id>`")

        st.subheader("👥 Team")
        team = cfg.get("team", [])
        if team:
            for member in team:
                st.markdown(f"- **{member.get('name', '?')}** — `{member.get('github', '?')}`")
        else:
            st.info("No team members configured.")

        st.warning("⚠️ This form saves to `config/config.yaml`. Back up your file first!",
                   icon="⚠️")

        if st.form_submit_button("💾 Save Configuration"):
            new_cfg = {
                "email": {
                    "recipients": [r.strip() for r in email_recipients.split(",") if r.strip()],
                    "from": email_from,
                },
                "github": {
                    "orgs": [o.strip() for o in gh_orgs.split("\n") if o.strip()],
                    "repos": [r.strip() for r in gh_repos.split("\n") if r.strip()],
                    "name_map": cfg.get("github", {}).get("name_map", {}),
                    "ex_members": cfg.get("github", {}).get("ex_members", []),
                },
                "linear": {
                    "projects": linear_projects_raw,
                    "project_ids": linear_ids_raw,
                    "issues_per_project": 50,
                },
                "reporting": cfg.get("reporting", {}),
            }
            save_config(new_cfg)
            st.success("✅ Configuration saved to `config/config.yaml`!")

# ═══════════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════════
elif page == "📋 Reports":
    st.header("📋 Generated Reports")

    REPORTS_DIR.mkdir(exist_ok=True)
    reports = sorted(REPORTS_DIR.glob("*.html"), reverse=True)

    if not reports:
        st.info("No reports yet. Run a report from the 'Run Reports' page.")
    else:
        for r in reports:
            with st.expander(f"📄 {r.name}"):
                with open(r) as f:
                    st.html(f.read())

# ═══════════════════════════════════════════════════════════════
# TEAM
# ═══════════════════════════════════════════════════════════════
elif page == "👥 Team":
    st.header("👥 Team Overview")

    cfg = load_config()
    team = cfg.get("team", [])

    if not team:
        st.info("No team members in config. Add them to `config/config.yaml`.")
    else:
        cols = st.columns(min(len(team), 3))
        for i, member in enumerate(team):
            with cols[i % len(cols)]:
                st.markdown(f"### {member.get('name', '?')}")
                st.write(f"**GitHub:** `{member.get('github', '?')}`")
                st.write(f"**Role:** {member.get('role', '—')}")
                st.write(f"**Email:** {member.get('email', '—')}")

    st.divider()
    st.subheader("🔗 Linear ↔ GitHub Project Map")
    projects = cfg.get("linear", {}).get("projects", {})
    if projects:
        data = []
        for name, info in projects.items():
            repos = ", ".join(info.get("repos", []))
            data.append({"Project": name, "Owner": info.get("owner", "?"), "Repos": repos})
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info("No projects configured.")

# ═══════════════════════════════════════════════════════════════
# RUN REPORTS
# ═══════════════════════════════════════════════════════════════
elif page == "🔧 Run Reports":
    st.header("🔧 Run Reports Manually")

    st.markdown("Run any Axeng report on-demand. Configure credentials in `.env` first.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Weekly Report")
        st.markdown("Per-project commits, MVP podium, roadmap analysis. "
                    "Also posts to Linear.")
        if st.button("▶️ Run Weekly Report", type="primary", use_container_width=True):
            with st.spinner("Running weekly report..."):
                result = subprocess.run(
                    ["python3", str(SCRIPT_DIR / "src" / "weekly_report.py")],
                    capture_output=True, text=True, cwd=str(SCRIPT_DIR),
                )
                if result.returncode == 0:
                    st.success("✅ Weekly report complete!")
                    st.markdown(f"```\n{result.stdout[-1000:]}\n```")
                else:
                    st.error(f"❌ Error:\n{result.stderr[-500:]}")

        st.divider()

        st.subheader("🏃 Standup Brief")
        st.markdown("Daily standup: what shipped, blockers, PRs, OOO.")
        if st.button("▶️ Run Standup Brief", use_container_width=True):
            with st.spinner("Running standup brief..."):
                result = subprocess.run(
                    ["python3", str(SCRIPT_DIR / "src" / "standup-brief.py")],
                    capture_output=True, text=True, cwd=str(SCRIPT_DIR),
                )
                if result.returncode == 0:
                    st.success("✅ Standup brief complete!")
                    st.markdown(f"```\n{result.stdout[-1000:]}\n```")
                else:
                    st.error(f"❌ Error:\n{result.stderr[-500:]}")

    with col2:
        st.subheader("📈 Sprint Health")
        st.markdown("Per-project health scores (0–100), burn rate, scope creep.")
        if st.button("▶️ Run Sprint Health", use_container_width=True):
            with st.spinner("Running sprint health..."):
                result = subprocess.run(
                    ["python3", str(SCRIPT_DIR / "src" / "sprint-health.py")],
                    capture_output=True, text=True, cwd=str(SCRIPT_DIR),
                )
                if result.returncode == 0:
                    st.success("✅ Sprint health complete!")
                    st.markdown(f"```\n{result.stdout[-1000:]}\n```")
                else:
                    st.error(f"❌ Error:\n{result.stderr[-500:]}")

        st.divider()

        st.subheader("🔭 Risk Radar")
        st.markdown("Quiet repos, overloaded members, overdue issues, orphaned PRs.")
        if st.button("▶️ Run Risk Radar", use_container_width=True):
            with st.spinner("Running risk radar..."):
                result = subprocess.run(
                    ["python3", str(SCRIPT_DIR / "src" / "risk-radar.py")],
                    capture_output=True, text=True, cwd=str(SCRIPT_DIR),
                )
                if result.returncode == 0:
                    st.success("✅ Risk radar complete!")
                    st.markdown(f"```\n{result.stdout[-1000:]}\n```")
                else:
                    st.error(f"❌ Error:\n{result.stderr[-500:]}")

    st.divider()
    st.subheader("🔄 Sync Vault")
    st.markdown("Fetch latest GitHub activity → Obsidian vault.")
    if st.button("▶️ Sync Vault", use_container_width=True):
        with st.spinner("Syncing vault..."):
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "src" / "team_sync.py")],
                capture_output=True, text=True, cwd=str(SCRIPT_DIR),
            )
            if result.returncode == 0:
                st.success("✅ Vault synced!")
                st.markdown(f"```\n{result.stdout[-500:]}\n```")
            else:
                st.error(f"❌ Error:\n{result.stderr[-500:]}")

    st.divider()
    st.subheader("📋 1:1 Pre-read Generator")
    person = st.text_input("Person name (as in config)", placeholder="e.g. João Silva")
    if st.button("▶️ Generate 1:1 Pre-read", use_container_width=True):
        if not person:
            st.warning("Enter a person name first.")
        else:
            with st.spinner(f"Generating 1:1 pre-read for {person}..."):
                result = subprocess.run(
                    ["python3", str(SCRIPT_DIR / "src" / "one-on-one-pre-read.py"),
                     "--title", f"1:1 with {person}", "--dry"],
                    capture_output=True, text=True, cwd=str(SCRIPT_DIR),
                )
                if result.returncode == 0:
                    st.success(f"✅ Pre-read for {person}!")
                    st.markdown(f"```\n{result.stdout[-1500:]}\n```")
                else:
                    st.error(f"❌ Error:\n{result.stderr[-500:]}")