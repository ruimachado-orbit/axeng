#!/usr/bin/env python3
"""
Team Intel — Daily GitHub→Obsidian Sync
Config-driven: fetches from GitHub orgs/repos, writes to Obsidian vault.
"""
import json, os, sys, subprocess
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from config import get, vault_path, github_orgs, github_repos, github_name_map, ex_members

LAST_SYNC = Path.home() / ".hermes" / "scripts" / "team-intel" / "last-sync.json"


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def write_json(path, data):
    LAST_SYNC.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def write_md(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}


# === GitHub ===

def fetch_github_activity() -> dict:
    result = {"pulls": [], "reviews": [], "contributors": {}, "repos_work": {}}

    days_ago = get("sync.days_range", 30)
    since_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

    all_repos = set()

    # Fetch repos from configured orgs
    for org in github_orgs():
        try:
            cmd = f'gh api orgs/{org}/repos --paginate --jq ".[].full_name"'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=30)
            if isinstance(output, bytes):
                output = output.decode('utf-8')
            for line in output.strip().split('\n'):
                if line.strip():
                    all_repos.add(line.strip())
        except:
            pass

    # Add configured repos
    for repo in github_repos():
        all_repos.add(repo)

    print(f"   Fetching from {len(all_repos)} repos...")

    for repo in all_repos:
        try:
            cmd = f'gh api repos/{repo}/pulls?state=closed&per_page=50'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=20)
            if isinstance(output, bytes):
                output = output.decode('utf-8')

            try:
                prs = json.loads(output)
            except:
                prs = []

            if not isinstance(prs, list):
                prs = []

            for pr in prs[:20]:
                if not pr.get('merged_at'):
                    continue

                user = pr.get("user", {})
                if isinstance(user, dict):
                    user = user.get("login", "unknown")
                elif not isinstance(user, str):
                    user = "unknown"

                # Skip excluded members
                if user in ex_members():
                    continue

                result["repos_work"].setdefault(repo, {"prs": 0, "people": set()})
                result["repos_work"][repo]["prs"] += 1
                result["repos_work"][repo]["people"].add(user)

                result["contributors"].setdefault(user, {"prs": 0, "repos": set()})
                result["contributors"][user]["prs"] += 1
                result["contributors"][user]["repos"].add(repo)

        except Exception:
            pass

    result["contributors"] = {
        k: {"prs": v["prs"], "repos": list(v["repos"])}
        for k, v in result["contributors"].items()
    }
    for repo in result["repos_work"]:
        result["repos_work"][repo]["people"] = list(result["repos_work"][repo]["people"])

    return result


# === Calendar ===

def fetch_calendar_insights() -> dict:
    result = {"today": [], "this_week": [], "upcoming_1on1s": [], "team_meetings": []}

    try:
        GAPI = get("calendar.gapi_script", "python3 ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py")
        start = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
        end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT23:59:59Z")

        cmd = f'{GAPI} calendar list --start {start} --end {end}'
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=30)
        events = json.loads(output) if output.strip() else []

        today = datetime.now().date()

        for event in events:
            summary = event.get("summary", "No title")
            start_time = event.get("start", "")

            try:
                if "T" in str(start_time):
                    event_date = datetime.fromisoformat(str(start_time).replace("Z", "+00:00")).date()
                else:
                    event_date = today
            except:
                event_date = today

            event_info = {"title": summary, "start": start_time, "attendees": event.get("attendees", [])}

            if event_date == today:
                result["today"].append(event_info)

            if today <= event_date <= today + timedelta(days=7):
                result["this_week"].append(event_info)

            lower_title = summary.lower()
            if any(kw in lower_title for kw in ["1:1", "one-on-one", "synch"]):
                result["upcoming_1on1s"].append(event_info)
            elif any(kw in lower_title for kw in ["standup", "daily", "planning", "retro", "review"]):
                result["team_meetings"].append(event_info)

    except Exception as e:
        print(f"Calendar fetch error: {e}", file=sys.stderr)

    return result


# === Email ===

def fetch_email_intel() -> dict:
    result = {"unread_count": 0, "decisions": [], "important_threads": []}

    try:
        GAPI = get("calendar.gapi_script", "python3 ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py")

        try:
            cmd = f'{GAPI} gmail search "is:unread newer_than:2d" --max 20'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=30)
            emails = json.loads(output) if output.strip() else []
            result["unread_count"] = len(emails)
        except:
            pass

        try:
            cmd = f'{GAPI} gmail search "subject:(decision OR approved OR rejected) newer_than:7d" --max 10'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=30)
            decisions = json.loads(output) if output.strip() else []
            result["decisions"] = decisions[:5]
        except:
            pass

    except Exception as e:
        print(f"Email fetch error: {e}", file=sys.stderr)

    return result


# === Obsidian Writers ===

def update_person_profile(person: dict, activity: dict, calendar: dict, vault: str):
    name_slug = person["name"].lower().replace(" ", "-")
    github = person.get("github", "")

    repos_html = ""
    if github in activity.get("contributors", {}):
        data = activity["contributors"][github]
        repos = data.get("repos", [])
        pr_count = data.get("prs", 0)
        if repos:
            repos_list = ", ".join([f"[[{r}|{r.split('/')[-1]}]]" for r in repos])
            repos_html = f"\n\n**Repositórios recentes:** {repos_list}\n"
            repos_html += f"**PRs mergeados:** {pr_count}"

    meetings_html = ""
    person_email = person.get("email", "").lower()
    upcoming_1on1s = [
        e for e in calendar.get("upcoming_1on1s", [])
        if any(
            person_email in str(a).lower() or person["name"].lower() in str(e.get("title", "")).lower()
            for a in e.get("attendees", [])
        )
    ]
    if upcoming_1on1s:
        titles = ", ".join([f"**{e['title']}**" for e in upcoming_1on1s[:3]])
        meetings_html = f"\n\n**Próximos 1:1s:** {titles}"

    content = f"""# {person['name']}

> Role: {person.get('role', 'Unknown')}
> Email: {person.get('email', 'N/A')}
> GitHub: [[https://github.com/{github}|@{github}]]

## Resumo de Atividade

Atualizado: {now_iso()}

{repos_html}{meetings_html}

## Notas

<!-- Add manual notes here -->

---
*Perfil gerado automaticamente pelo Team Intel*
"""

    base_path = Path(vault) / get("obsidian.team_base", "Rui/equipa")
    write_md(str(base_path / f"{name_slug}.md"), content)


def update_team_overview(github_data: dict, calendar_data: dict, email_data: dict, vault: str):
    total_prs = sum(d.get("prs", 0) for d in github_data.get("repos_work", {}).values())

    contributors_html = ""
    for user, data in github_data.get("contributors", {}).items():
        repos = ", ".join(data.get("repos", [])[:3])
        contributors_html += f"\n| @{user} | {data['prs']} PRs | {repos} |"

    upcoming_html = ""
    for meeting in calendar_data.get("upcoming_1on1s", [])[:5]:
        upcoming_html += f"\n- **{meeting['title']}** ({meeting['start']})"

    team_meetings_html = ""
    for meeting in calendar_data.get("team_meetings", [])[:5]:
        team_meetings_html += f"\n- **{meeting['title']}** ({meeting['start']})"

    content = f"""# Team Overview — Team Intelligence

> Atualizado: {now_iso()}

## Métricas da Semana

| Métrica | Valor |
|---------|-------|
| Total PRs merged | {total_prs} |
| Repositórios ativos | {len(github_data.get('repos_work', {}))} |
| Emails não lidos | {email_data.get('unread_count', 0)} |
| Decisões pendentes | {len(email_data.get('decisions', []))} |

## Repositórios Ativos

"""

    for repo, data in github_data.get("repos_work", {}).items():
        people = ", ".join([f"@{p}" for p in data.get("people", [])])
        content += f"### [[{repo}|{repo.split('/')[-1]}]]\n"
        content += f"- PRs: **{data['prs']}**\n"
        content += f"- Pessoas: {people}\n"

    content += f"""

## Equipa — Atividade por Pessoa

| Pessoa | PRs | Repositórios |
|--------|-----|--------------|
{contributors_html}

## Agenda da Semana

### 1:1s
{upcoming_html if upcoming_html else "- Nenhum 1:1 agendado"}

### Reuniões de equipa
{team_meetings_html if team_meetings_html else "- Nenhuma reunião de equipa"}

## Decisões Recentes

"""

    for decision in email_data.get("decisions", [])[:5]:
        content += f"\n- **{decision.get('subject', 'Sem título')}** — {decision.get('from', '')} ({decision.get('date', '')})"

    if not email_data.get("decisions"):
        content += "\n- Nenhuma decisão recente nos emails"

    content += """

---
*Gerado automaticamente — Team Intel*
"""

    base_path = Path(vault) / get("obsidian.insights_base", "Rui/insights")
    write_md(str(base_path / "team-overview.md"), content)


def update_metrics(github_data: dict, vault: str):
    date = datetime.now().strftime("%Y-%m-%d")
    total_prs = sum(d.get("prs", 0) for d in github_data.get("repos_work", {}).values())
    total_contributors = len(github_data.get("contributors", {}))
    total_repos = len(github_data.get("repos_work", {}))

    new_entry = f"| {date} | {total_prs} | {total_contributors} | {total_repos} |"

    metrics_path = Path(vault) / get("obsidian.metrics_path", "Rui/metrics/weekly-metrics.md")

    if metrics_path.exists():
        with open(metrics_path) as f:
            content = f.read()
        lines = content.split("\n")
        last_idx = -1
        for i, line in enumerate(lines):
            if line.startswith("| --"):
                last_idx = i - 1
                break
        if last_idx > 0:
            lines.insert(last_idx + 1, new_entry)
            content = "\n".join(lines)
    else:
        content = f"""# Métricas Semanais da Equipa

| Data | PRs Merged | Contributors | Repos Ativos |
|------|------------|--------------|--------------|
{new_entry}
"""

    write_md(str(metrics_path), content)


# === Main Sync ===

def run_sync():
    """Run full GitHub→Obsidian sync using config settings."""
    print(f"🔄 Team Intel — Sync starting at {now_iso()}")

    vault = vault_path()
    team = get("team", [])

    print("📡 Fetching GitHub activity...")
    github_data = fetch_github_activity()
    print(f"   → {len(github_data.get('contributors', {}))} contribuidores, {len(github_data.get('repos_work', {}))} repos")

    print("📅 Fetching Calendar insights...")
    calendar_data = fetch_calendar_insights()
    print(f"   → {len(calendar_data.get('this_week', []))} eventos esta semana")

    print("📧 Fetching Email intel...")
    email_data = fetch_email_intel()
    print(f"   → {email_data.get('unread_count', 0)} emails não lidos")

    # Write to Obsidian
    print("💾 Updating Obsidian vault...")

    for person in team:
        update_person_profile(person, github_data, calendar_data, vault)

    update_team_overview(github_data, calendar_data, email_data, vault)
    update_metrics(github_data, vault)

    # Save raw data for queries
    sync_data = {
        "timestamp": now_iso(),
        "github": github_data,
        "calendar": calendar_data,
        "email": email_data
    }
    write_json(LAST_SYNC, sync_data)

    print("✅ Sync complete!")
    return True


if __name__ == "__main__":
    run_sync()