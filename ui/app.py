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


def ensure_config_shape(cfg: dict) -> dict:
    cfg = cfg or {}
    cfg.setdefault("email", {})
    cfg["email"].setdefault("recipients", [])
    cfg["email"].setdefault("from", "")
    cfg.setdefault("github", {})
    cfg["github"].setdefault("orgs", [])
    cfg["github"].setdefault("repos", [])
    cfg["github"].setdefault("name_map", {})
    cfg["github"].setdefault("ex_members", [])
    cfg.setdefault("linear", {})
    cfg["linear"].setdefault("projects", {})
    cfg["linear"].setdefault("project_ids", {})
    cfg.setdefault("team", [])
    cfg.setdefault("reporting", {})
    return cfg

def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

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
    st.caption("First-time setup and editable config — no YAML hand-editing required.")

    cfg = ensure_config_shape(load_config())

    # Setup Wizard
    missing_team = len(cfg.get("team", [])) == 0
    missing_github = len(cfg.get("github", {}).get("orgs", [])) == 0 and len(cfg.get("github", {}).get("repos", [])) == 0
    missing_linear = len(cfg.get("linear", {}).get("projects", {})) == 0

    with st.expander("🚀 Setup Wizard — First-time setup", expanded=(missing_team or missing_github or missing_linear)):
        st.markdown("Configure the minimum needed for Axeng to become useful:")
        c1, c2, c3 = st.columns(3)
        c1.metric("Team members", len(cfg.get("team", [])), "✅" if not missing_team else "missing")
        c2.metric("GitHub sources", len(cfg.get("github", {}).get("orgs", [])) + len(cfg.get("github", {}).get("repos", [])), "✅" if not missing_github else "missing")
        c3.metric("Linear projects", len(cfg.get("linear", {}).get("projects", {})), "✅" if not missing_linear else "optional")
        st.info("Recommended path: add team members → add GitHub org/repos → map Linear projects → save.")

    tab_team, tab_github, tab_linear, tab_email, tab_raw = st.tabs([
        "👥 Team Members", "🐙 GitHub", "🔗 Linear Projects", "📧 Email/Reports", "🧩 Advanced: Raw YAML"
    ])

    # Team editor
    with tab_team:
        st.subheader("👥 Team Members")
        st.caption("Add everyone Axeng should track. GitHub login is required for activity reports.")

        team = cfg.get("team", [])
        if team:
            st.dataframe(team, use_container_width=True, hide_index=True)
        else:
            st.info("No team members yet. Add the first one below.")

        with st.form("add_team_member", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name", placeholder="Jane Developer")
            github = c2.text_input("GitHub login", placeholder="janedev")
            c3, c4 = st.columns(2)
            role = c3.text_input("Role", placeholder="Senior Engineer")
            email = c4.text_input("Email", placeholder="jane@company.com")
            submitted = st.form_submit_button("➕ Add Team Member", use_container_width=True)
            if submitted:
                if not name or not github:
                    st.error("Name and GitHub login are required.")
                else:
                    cfg["team"].append({"name": name, "github": github, "role": role, "email": email})
                    cfg["github"].setdefault("name_map", {})[github] = name
                    save_config(cfg)
                    st.success(f"Added {name}")
                    rerun()

        if team:
            remove_options = [f"{m.get('name','?')} — {m.get('github','?')}" for m in team]
            idx = st.selectbox("Remove selected member", list(range(len(remove_options))), format_func=lambda i: remove_options[i])
            if st.button("🗑️ Remove selected member", use_container_width=True):
                removed = cfg["team"].pop(idx)
                gh = removed.get("github")
                if gh:
                    cfg["github"].get("name_map", {}).pop(gh, None)
                save_config(cfg)
                st.success(f"Removed {removed.get('name', gh)}")
                rerun()

    # GitHub editor
    with tab_github:
        st.subheader("🐙 GitHub Sources")
        with st.form("github_editor"):
            gh_orgs = st.text_area("Organizations — one per line", value="\n".join(cfg["github"].get("orgs", [])), placeholder="my-company")
            gh_repos = st.text_area("Additional repos — org/repo, one per line", value="\n".join(cfg["github"].get("repos", [])), placeholder="my-company/web-app")
            ex_members = st.text_area("Exclude members/bots — one GitHub login per line", value="\n".join(cfg["github"].get("ex_members", [])), placeholder="dependabot[bot]")
            if st.form_submit_button("💾 Save GitHub Config", use_container_width=True):
                cfg["github"]["orgs"] = [x.strip() for x in gh_orgs.splitlines() if x.strip()]
                cfg["github"]["repos"] = [x.strip() for x in gh_repos.splitlines() if x.strip()]
                cfg["github"]["ex_members"] = [x.strip() for x in ex_members.splitlines() if x.strip()]
                save_config(cfg)
                st.success("GitHub config saved.")
                rerun()

    # Linear editor
    with tab_linear:
        st.subheader("🔗 Linear Projects")
        projects = cfg["linear"].get("projects", {})
        project_ids = cfg["linear"].get("project_ids", {})
        if projects:
            rows = []
            for name, info in projects.items():
                rows.append({
                    "Project": name,
                    "Project ID": project_ids.get(name, ""),
                    "Owner": info.get("owner", ""),
                    "Repos": ", ".join(info.get("repos", [])),
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No Linear projects mapped yet.")

        with st.form("add_linear_project", clear_on_submit=True):
            c1, c2 = st.columns(2)
            project_name = c1.text_input("Project name", placeholder="Frontend")
            project_id = c2.text_input("Project ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
            c3, c4 = st.columns(2)
            owner = c3.text_input("Owner", placeholder="Jane Developer")
            repos = c4.text_input("Repos — comma-separated", placeholder="my-company/web-app, my-company/ui")
            if st.form_submit_button("➕ Add Linear Project", use_container_width=True):
                if not project_name:
                    st.error("Project name is required.")
                else:
                    cfg["linear"].setdefault("projects", {})[project_name] = {
                        "owner": owner,
                        "repos": [r.strip() for r in repos.split(",") if r.strip()],
                    }
                    if project_id:
                        cfg["linear"].setdefault("project_ids", {})[project_name] = project_id
                    save_config(cfg)
                    st.success(f"Added project {project_name}")
                    rerun()

        if projects:
            names = list(projects.keys())
            rm = st.selectbox("Remove Linear project", names)
            if st.button("🗑️ Remove selected project", use_container_width=True):
                cfg["linear"].get("projects", {}).pop(rm, None)
                cfg["linear"].get("project_ids", {}).pop(rm, None)
                save_config(cfg)
                st.success(f"Removed {rm}")
                rerun()

    # Email/reporting editor
    with tab_email:
        st.subheader("📧 Email & Reports")
        with st.form("email_editor"):
            recipients = st.text_area("Recipients — one email per line", value="\n".join(cfg["email"].get("recipients", [])), placeholder="engineering@company.com")
            from_email = st.text_input("From address", value=cfg["email"].get("from", ""), placeholder="axeng@company.com")
            output_dir = st.text_input("Reports output directory", value=cfg.get("reporting", {}).get("output_dir", "reports"))
            if st.form_submit_button("💾 Save Email/Reports Config", use_container_width=True):
                cfg["email"]["recipients"] = [x.strip() for x in recipients.splitlines() if x.strip()]
                cfg["email"]["from"] = from_email
                cfg.setdefault("reporting", {})["output_dir"] = output_dir
                save_config(cfg)
                st.success("Email/reporting config saved.")
                rerun()

    # Raw YAML escape hatch
    with tab_raw:
        st.subheader("🧩 Advanced: Raw YAML")
        st.warning("Use this if you need full control. Invalid YAML will not be saved.")
        raw = st.text_area("config/config.yaml", value=yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), height=500)
        c1, c2 = st.columns(2)
        if c1.button("💾 Save Raw YAML", use_container_width=True):
            try:
                parsed = yaml.safe_load(raw) or {}
                save_config(ensure_config_shape(parsed))
                st.success("Raw YAML saved.")
                rerun()
            except Exception as e:
                st.error(f"Invalid YAML: {e}")
        if c2.button("⬇️ Download YAML", use_container_width=True):
            st.download_button("Download config.yaml", raw, file_name="config.yaml", mime="text/yaml")

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

    cfg = ensure_config_shape(load_config())
    team = cfg.get("team", [])

    if not team:
        st.info("No team members configured yet.")
        st.markdown("Go to **⚙️ Configuration → Team Members** to add people directly from the UI.")
        if st.button("⚙️ Open Configuration", use_container_width=True):
            st.session_state["nav_hint"] = "configuration"
            st.toast("Use the sidebar: ⚙️ Configuration")
    else:
        cols = st.columns(min(len(team), 3))
        for i, member in enumerate(team):
            with cols[i % len(cols)]:
                st.container(border=True).markdown(
                    f"### {member.get('name', '?')}\n"
                    f"**GitHub:** `{member.get('github', '?')}`  \n"
                    f"**Role:** {member.get('role', '—')}  \n"
                    f"**Email:** {member.get('email', '—')}"
                )

    st.divider()
    st.subheader("🔗 Linear ↔ GitHub Project Map")
    projects = cfg.get("linear", {}).get("projects", {})
    project_ids = cfg.get("linear", {}).get("project_ids", {})
    if projects:
        data = []
        for name, info in projects.items():
            repos = ", ".join(info.get("repos", []))
            data.append({
                "Project": name,
                "Project ID": project_ids.get(name, ""),
                "Owner": info.get("owner", "?"),
                "Repos": repos,
            })
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info("No projects configured yet. Add them in **⚙️ Configuration → Linear Projects**.")

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