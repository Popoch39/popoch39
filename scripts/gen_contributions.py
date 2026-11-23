#!/usr/bin/env python3
"""Rewrite the README's open source section from my merged pull requests on other people's repos.

Run by .github/workflows/contributions.yml daily, or locally: GITHUB_TOKEN=$(gh auth token) python3 scripts/gen_contributions.py
"""
import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

USER = "Popoch39"
# Tutorial repos where a PR is an exercise, not a contribution.
EXCLUDE = {"firstcontributions/first-contributions"}
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- CONTRIBUTIONS:START -->", "<!-- CONTRIBUTIONS:END -->"

QUERY = """
query($q: String!, $after: String) {
  search(query: $q, type: ISSUE, first: 100, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        number title url mergedAt
        repository { nameWithOwner url stargazerCount }
      }
    }
  }
}
"""


def fetch_prs(token):
    q = f"is:pr is:merged is:public author:{USER} -user:{USER}"
    prs, after = [], None
    while True:
        body = json.dumps({"query": QUERY, "variables": {"q": q, "after": after}}).encode()
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=body,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as r:
            data = json.load(r)
        if "errors" in data:
            raise SystemExit(f"GraphQL errors: {data['errors']}")
        search = data["data"]["search"]
        prs += [n for n in search["nodes"] if n and n["repository"]["nameWithOwner"] not in EXCLUDE]
        if not search["pageInfo"]["hasNextPage"]:
            return prs
        after = search["pageInfo"]["endCursor"]


def render(prs):
    by_repo = {}
    for pr in prs:
        by_repo.setdefault(pr["repository"]["nameWithOwner"], []).append(pr)
    # Most recent merge first, so the list reads as a log.
    repos = sorted(by_repo.values(), key=lambda ps: max(p["mergedAt"] for p in ps), reverse=True)
    lines = []
    for ps in repos:
        repo = ps[0]["repository"]
        lines.append(f"- **[{repo['nameWithOwner']}]({repo['url']})** <sub>★ {repo['stargazerCount']:,}</sub>")
        for pr in sorted(ps, key=lambda p: p["mergedAt"], reverse=True):
            month = datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00")).strftime("%b %Y")
            title = pr["title"].replace("[", "\\[").replace("]", "\\]")
            lines.append(f"  - [{title}]({pr['url']}) <sub>#{pr['number']} · {month}</sub>")
    return "\n".join(lines)


def main():
    token = os.environ["GITHUB_TOKEN"]
    readme = README.read_text()
    if START not in readme or END not in readme:
        raise SystemExit(f"README.md lacks the {START} / {END} markers")
    block = f"{START}\n{render(fetch_prs(token))}\n{END}"
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    README.write_text(pattern.sub(lambda _: block, readme))
    print("wrote README.md")


if __name__ == "__main__":
    main()
