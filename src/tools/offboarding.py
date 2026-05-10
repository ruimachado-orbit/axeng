#!/usr/bin/env python3
"""
Axemaster Offboarding Tool
Remove a collaborator's access from all GitHub orgs AND Linear workspace.
Usage:
  python3 offboarding.py <github_login> [--dry-run] [--skip-linear]
  python3 offboarding.py vitordesouza --dry-run
  python3 offboarding.py brunoselistre-orbit
"""
import json, subprocess, sys, os, argparse
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
EXCLUDED_ORGS = {"mynort", "remynd", "my-north-ai", "remynd-me"}  # orgs to skip
GH_TOKEN       = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
LINEAR_KEY     = os.getenv("LINEAR_API_KEY")
GH_HEADERS     = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"} if GH_TOKEN else {}
LIN_ENDPOINT   = "https://api.linear.app/graphql"

# ── Helpers ──────────────────────────────────────────────────────────────────
def run(cmd, die=True):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode and die:
        print(f"❌ FAIL: {cmd}\n{r.stderr}")
        sys.exit(1)
    return r.stdout.strip()

def lin(query, vars=None):
    payload = {"query": query}
    if vars:
        payload["variables"] = vars
    body = json.dumps(payload).replace('"', '\\"')
    # Build curl args carefully to avoid shell quoting issues
    cmd = (
        f'curl -s -X POST {LIN_ENDPOINT} '
        f'-H "Authorization: {LINEAR_KEY}" '
        f'-H "Content-Type: application/json" '
        f'-d "{body}"'
    )
    out = run(cmd)
    try:
        return json.loads(out)
    except Exception as e:
        print(f"⚠️  Linear parse error: {e}\nRaw: {out}")
        return {}

# ── GitHub: list orgs ────────────────────────────────────────────────────────
def gh_list_orgs():
    out = run("gh api user/orgs --jq '[.[] .login]'")
    orgs = json.loads(out)
    return [o for o in orgs if o.lower() not in {x.lower() for x in EXCLUDED_ORGS}]

# ── GitHub: list repos in an org ─────────────────────────────────────────────
def gh_list_repos(org):
    out = run(f"gh api orgs/{org}/repos --paginate --jq '[.[] .name]'")
    return json.loads(out)

# ── GitHub: list collaborators on a repo ─────────────────────────────────────
def gh_list_collabs(org, repo):
    out = run(f"gh api repos/{org}/{repo}/collaborators --jq '[.[] .login]'", die=False)
    if not out:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []

# ── GitHub: remove a collaborator ────────────────────────────────────────────
def gh_remove(org, repo, login):
    run(f"gh api -X DELETE repos/{org}/{repo}/collaborators/{login}", die=False)
    return True

# ── GitHub: cancel pending invitations ────────────────────────────────────────
def gh_cancel_invitations(org, repo, login):
    invitations = run(f"gh api repos/{org}/{repo}/invitations --jq '[.[] | select(.invitee.login == \"{login}\")]'", die=False)
    if not invitations:
        return []
    try:
        inv_list = json.loads(invitations)
    except Exception:
        return []
    removed = []
    for inv in inv_list:
        run(f"gh api -X DELETE repos/{org}/{repo}/invitations/{inv['id']}", die=False)
        removed.append(inv["id"])
    return removed

# ── Linear: find user ──────────────────────────────────────────────────────────
def lin_find_user(email_or_name):
    q = f'{{ users(first: 50) {{ nodes {{ id name email active }} }} }}'
    data = lin(q)
    users = data.get("data", {}).get("users", {}).get("nodes", [])
    # match by email or name (case-insensitive)
    needle = email_or_name.lower()
    for u in users:
        if (u.get("email") or "").lower() == needle or u.get("name", "").lower() == needle:
            return u
    # partial match on name
    for u in users:
        if needle in u.get("name", "").lower():
            return u
    return None

# ── Linear: archive user ───────────────────────────────────────────────────────
def lin_archive_user(user_id):
    q = 'mutation($id: String!) { userArchive(id: $id) { success } }'
    data = lin(q, {"id": user_id})
    return data.get("data", {}).get("userArchive", {}).get("success", False)

# ── Linear: remove user from all teams ───────────────────────────────────────
def lin_remove_from_teams(user_id):
    # Get all team memberships for this user
    q = 'query($userId: String!) { teamMemberships(filter: { userId: { eq: $userId } }) { nodes { id teamId userId } } }'
    data = lin(q, {"userId": user_id})
    memberships = data.get("data", {}).get("teamMemberships", {}).get("nodes", [])
    for m in memberships:
        mid = m["id"]
        run(
            f'curl -s -X POST {LIN_ENDPOINT} '
            f'-H "Authorization: {LINEAR_KEY}" '
            f'-H "Content-Type: application/json" '
            f'-d "{{\\"query\\":\\"mutation {{ teamMembershipDelete(id: \\\"{mid}\\\") {{ success }} }} \\"}}"',
            die=False
        )
    return len(memberships)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Axemaster Offboarding Tool")
    ap.add_argument("login", help="GitHub login of the collaborator to offboard")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    ap.add_argument("--skip-linear", action="store_true", help="Skip Linear offboarding")
    ap.add_argument("--email", default=None, help="Linear user email or name (auto-detected if omitted)")
    args = ap.parse_args()

    login = args.login
    print(f"\n{'='*60}")
    print(f"🔴 OFFBOARDING: {login}")
    print(f"   Dry-run: {args.dry_run} | Skip Linear: {args.skip_linear}")
    print(f"{'='*60}\n")

    # ── Step 1: GitHub ─────────────────────────────────────────────────────
    print("📦 [GitHub] Discovering organizations…")
    orgs = gh_list_orgs()
    print(f"   → {len(orgs)} orgs (excluded: {EXCLUDED_ORGS})")

    total_removed = 0
    total_invites  = 0

    for org in sorted(orgs):
        repos = gh_list_repos(org)
        for repo in sorted(repos):
            collabs = gh_list_collabs(org, repo)
            if login in collabs:
                if args.dry_run:
                    print(f"   🔍 [DRY] Would remove {login} from {org}/{repo}")
                else:
                    gh_remove(org, repo, login)
                    print(f"   ✅ Removed {login} ← {org}/{repo}")
                    total_removed += 1
            # cancel pending invitations
            if not args.dry_run:
                cancelled = gh_cancel_invitations(org, repo, login)
                total_invites += len(cancelled)

    # ── Step 2: Linear ─────────────────────────────────────────────────────
    if args.skip_linear:
        print("\n⏭️  [Linear] Skipped by flag.")
    else:
        email = args.email or login
        print(f"\n📋 [Linear] Looking for user: {email}")
        user = lin_find_user(email)
        if not user:
            print("   ⚠️  User not found in Linear workspace.")
        else:
            uid   = user["id"]
            name  = user.get("name", "?")
            email_addr = user.get("email", "?")
            print(f"   → Found: {name} ({email_addr}) — ID: {uid}")
            if args.dry_run:
                print(f"   🔍 [DRY] Would archive user {uid} and remove from teams.")
            else:
                n_teams = lin_remove_from_teams(uid)
                archived = lin_archive_user(uid)
                if archived:
                    print(f"   ✅ Archived in Linear | Removed from {n_teams} teams.")
                else:
                    print("   ⚠️  Archive may have failed — check Linear manually.")

    # ── Summary ────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY for {login}")
    print(f"   GitHub repos cleaned:  {total_removed}")
    print(f"   Pending invites cancelled: {total_invites}")
    print(f"   Linear: {'skipped' if args.skip_linear else 'archived'}")
    print(f"{'='*60}")
    if args.dry_run:
        print("\n🔍 This was a DRY RUN — no actual changes were made.\n")

if __name__ == "__main__":
    main()