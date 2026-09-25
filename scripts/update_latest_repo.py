from __future__ import annotations

import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

OWNER = os.environ.get("GITHUB_REPO_OWNER", "MohammedZidanC")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
README = Path(__file__).resolve().parents[1] / "README.md"
START = "<!-- LATEST_REPO:START -->"
END = "<!-- LATEST_REPO:END -->"


def github_get(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "MohammedZidanC-profile-updater",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def format_date(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc).strftime("%d %b %Y")


def code_tag(value: str) -> str:
    return f'<code>{html.escape(value)}</code>'


def build_card(repo: dict) -> str:
    name = html.escape(repo.get("name", "Latest repository"))
    description = repo.get("description")
    description_text = (
        html.escape(description.strip())
        if description
        else "No repository description has been added yet."
    )
    language = repo.get("language") or "Repository"
    created = format_date(repo["created_at"])
    url = html.escape(repo["html_url"], quote=True)

    topics = [str(topic) for topic in repo.get("topics", [])[:4]]
    tags = " ".join(code_tag(topic) for topic in topics)
    meta = f"{code_tag(language)} &nbsp; {code_tag('Created ' + created)}"
    if tags:
        meta += f"<br><br>{tags}"

    return f'''<table width="100%" border="0" cellpadding="0" cellspacing="0">
  <tr>
    <td>
      <sub>LATEST REPOSITORY</sub><br>
      <h3><a href="{url}">{name}</a></h3>
      <p>{description_text}</p>
      {meta}
      <br><br>
      <a href="{url}"><strong>VIEW REPOSITORY ↗</strong></a>
    </td>
  </tr>
</table>'''


def main() -> int:
    if not README.exists():
        print(f"README not found: {README}", file=sys.stderr)
        return 1

    repos = github_get(
        f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=created&direction=desc&type=owner"
    )
    if not isinstance(repos, list):
        print("GitHub API returned an unexpected payload.", file=sys.stderr)
        return 1

    eligible = [
        repo
        for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and repo.get("visibility", "public") == "public"
        and repo.get("name", "").lower() != OWNER.lower()
    ]

    if eligible:
        content = build_card(eligible[0])
    else:
        content = '''<table width="100%" border="0" cellpadding="0" cellspacing="0">
  <tr>
    <td>
      <sub>LATEST REPOSITORY</sub><br>
      <h3>No public repository yet</h3>
      <p>This panel will populate automatically when a new public repository is created.</p>
    </td>
  </tr>
</table>'''

    current = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    replacement = f"{START}\n{content}\n{END}"
    updated, count = pattern.subn(replacement, current, count=1)

    if count != 1:
        print("README markers were not found exactly once.", file=sys.stderr)
        return 1

    if updated != current:
        README.write_text(updated, encoding="utf-8")
        print("Latest repository section refreshed.")
    else:
        print("Latest repository section already up to date.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
