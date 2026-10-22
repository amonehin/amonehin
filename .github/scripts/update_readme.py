
import json
import os
from pathlib import Path
import requests
import yaml

ROOT = Path(__file__).resolve().parents[2]
README_PATH = ROOT / "README.md"
YAML_PATH = ROOT / ".github" / "data" / "profile.yml"
TEMPLATE_PATH = ROOT / "README.md"

def fetch_recent_prs(username, max_items=5):
    q = f"author:{username} is:pr"
    url = "https://api.github.com/search/issues"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN', '')}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    params = {"q": q, "sort": "updated", "order": "desc", "per_page": max_items}
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    items = r.json().get("items", [])
    lines = []
    for item in items:
        title = item.get("title", "Untitled PR")
        pr_url = item.get("html_url", "#")
        number = item.get("number")
        state = item.get("state", "open")
        lines.append(f"- [#{number}]({pr_url}) — {title} ({state})")
    return "\n".join(lines) if lines else "- No recent pull requests found."

def fetch_recent_commits(username, max_items=5):
    url = f"https://api.github.com/users/{username}/events/public"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN', '')}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    events = r.json()
    commits = []
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        payload = event.get("payload", {})
        for commit in payload.get("commits", []):
            sha = commit.get("sha", "")[:7]
            msg = commit.get("message", "Update").split("\\n")[0]
            commits.append(f"- `{sha}` — {msg}")
            if len(commits) >= max_items:
                break
        if len(commits) >= max_items:
            break
    return "\n".join(commits) if commits else "- No recent commits found."

def render_projects(projects):
    lines = []
    for project in projects:
        lines.append(f"- [{project['name']}]({project['url']}) — {project['description']}")
    return "\n".join(lines)

def main():
    with YAML_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    username = data.get("profile", {}).get("username", "amonehin")
    recent_prs = fetch_recent_prs(username, max_items=data.get("dashboard", {}).get("max_recent_prs", 5))
    recent_commits = fetch_recent_commits(username, max_items=data.get("dashboard", {}).get("max_recent_commits", 5))
    featured_projects = render_projects(data.get("projects", []))

    original = TEMPLATE_PATH.read_text(encoding="utf-8")
    original = original.replace("{{recent_prs}}", recent_prs)
    original = original.replace("{{recent_commits}}", recent_commits)
    original = original.replace("{{featured_projects}}", featured_projects)

    README_PATH.write_text(original, encoding="utf-8")

if __name__ == "__main__":
    main()
