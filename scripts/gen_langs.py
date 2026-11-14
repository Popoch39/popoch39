#!/usr/bin/env python3
"""Generate assets/langs-dark.svg and langs-light.svg from GitHub language stats.

Replaces github-readme-stats (public instance is flaky) with static cards in the portfolio's charte.
Run by .github/workflows/langs.yml weekly, or locally: GITHUB_TOKEN=$(gh auth token) python3 scripts/gen_langs.py
"""
import json
import os
import urllib.request
from pathlib import Path

from charte import THEMES, text

USER = "Popoch39"
TOP_N = 6
EXCLUDE = {"HTML", "CSS", "SCSS", "Makefile", "Dockerfile"}  # markup/build noise, often vendored


def api(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"} if token else {})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def fetch_langs(token):
    totals = {}
    page = 1
    while True:
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}", token)
        if not repos:
            break
        for repo in repos:
            if repo["fork"]:
                continue
            for lang, size in api(repo["languages_url"], token).items():
                if lang not in EXCLUDE:
                    totals[lang] = totals.get(lang, 0) + size
        page += 1
    return totals


def render(langs, mode):
    """One ink for every bar: the labels name them, the length is the reading."""
    t = THEMES[mode]
    total = sum(v for _, v in langs)
    rows = [(l, 100 * v / total) for l, v in langs[:TOP_N]]

    w, row_h, top_pad = 640, 26, 58
    h = top_pad + row_h * len(rows) + 22
    bar_x, bar_max, pct_x = 150, 380, 620
    max_pct = max(p for _, p in rows)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Top languages">',
        "<style>",
        ".bar { transform-origin: %dpx 0; animation: grow 1.2s cubic-bezier(0.4, 0, 0.2, 1) both; }" % bar_x,
        "@keyframes grow { from { transform: scaleX(0); } }",
        "@media (prefers-reduced-motion: reduce) { .bar { animation: none; } }",
        "</style>",
        f'<rect width="{w}" height="{h}" fill="{t["paper"]}"/>',
        f'<rect x="10.5" y="10.5" width="{w-21}" height="{h-21}" fill="none" stroke="{t["ink"]}" stroke-width="1"/>',
        f'<rect x="28" y="31" width="9" height="9" fill="{t["accent"]}"/>',
        text("Top languages", 46, 40, 12, t["ink"], tracking=2),
        text("by bytes of code", w - 28, 40, 10, t["muted"], anchor="end"),
        f'<path d="M28 50.5h{w-56}" stroke="{t["rule"]}" stroke-width="1"/>',
    ]
    for i, (name, pct) in enumerate(rows):
        y = top_pad + row_h * i + 16
        bw = max(8, bar_max * pct / max_pct)
        delay = 0.12 * i
        svg += [
            text(name, 28, y + 4, 12, t["ink"]),
            f'<rect class="bar" style="animation-delay:{delay:.2f}s" x="{bar_x}" y="{y-4}" width="{bw:.1f}" height="8" fill="{t["ink"]}"/>',
            text(f"{pct:.1f}%", pct_x, y + 4, 11, t["muted"], anchor="end"),
        ]
    svg.append("</svg>")
    return "\n".join(svg)


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    langs = sorted(fetch_langs(token).items(), key=lambda kv: -kv[1])
    out = Path(__file__).resolve().parent.parent / "assets"
    for mode in THEMES:
        (out / f"langs-{mode}.svg").write_text(render(langs, mode))
        print(f"wrote assets/langs-{mode}.svg")


if __name__ == "__main__":
    main()
