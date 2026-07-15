#!/usr/bin/env python3
"""Generate assets/langs-dark.svg and langs-light.svg from GitHub language stats.

Replaces github-readme-stats (public instance is flaky) with static, on-brand cards.
Run by .github/workflows/langs.yml weekly, or locally: GITHUB_TOKEN=$(gh auth token) python3 scripts/gen_langs.py
"""
import json
import os
import urllib.request
from pathlib import Path

USER = "Popoch39"
TOP_N = 6
EXCLUDE = {"HTML", "CSS", "SCSS", "Makefile", "Dockerfile"}  # markup/build noise, often vendored

# CVD-validated categorical palettes (dark on #0d1117, light on #ffffff).
# Colors follow the language (entity), not its rank, so refreshes don't repaint.
SLOTS = [  # (dark, light)
    ("#0d9488", "#0d9488"),  # teal
    ("#c98500", "#b45309"),  # amber
    ("#3987e5", "#2a78d6"),  # blue
    ("#e66767", "#e34948"),  # red
    ("#9085e9", "#4a3aa7"),  # violet
    ("#d55181", "#e87ba4"),  # magenta
]
KNOWN = {"Go": 0, "Rust": 1, "TypeScript": 2, "C": 3, "Lua": 4, "Shell": 5}

THEMES = {
    "dark":  {"bg": "#0d1117", "frame": "#30363d", "ink": "#e6edf3", "muted": "#8b949e", "accent": "#2dd4bf"},
    "light": {"bg": "#ffffff", "frame": "#d0d7de", "ink": "#1f2328", "muted": "#57606a", "accent": "#0f766e"},
}


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


def slot_for(lang, used):
    if lang in KNOWN:
        return KNOWN[lang]
    return next(i for i in range(len(SLOTS)) if i not in used)


def render(langs, mode):
    t = THEMES[mode]
    total = sum(v for _, v in langs)
    top = langs[:TOP_N]
    used = {KNOWN[l] for l, _ in top if l in KNOWN}
    rows = []
    for l, v in top:
        s = slot_for(l, used)
        used.add(s)
        rows.append((l, 100 * v / total, SLOTS[s][0 if mode == "dark" else 1]))

    w, row_h, top_pad = 640, 26, 58
    h = top_pad + row_h * len(rows) + 22
    bar_x, bar_max, pct_x = 150, 380, 620
    max_pct = max(p for _, p, _ in rows)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Top languages">',
        "<style>",
        ".mono { font-family: ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace; }",
        ".bar { transform-origin: %dpx 0; animation: grow 1.2s cubic-bezier(0.4, 0, 0.2, 1) forwards; transform: scaleX(0); }" % bar_x,
        "@keyframes grow { to { transform: scaleX(1); } }",
        "@media (prefers-reduced-motion: reduce) { .bar { animation: none; transform: none; } }",
        "</style>",
        f'<rect width="{w}" height="{h}" fill="{t["bg"]}"/>',
        f'<rect x="10.5" y="10.5" width="{w-21}" height="{h-21}" fill="none" stroke="{t["frame"]}" stroke-width="1"/>',
        f'<text class="mono" x="28" y="40" font-size="12" fill="{t["accent"]}" letter-spacing="4">TOP LANGUAGES</text>',
        f'<text class="mono" x="{w-28}" y="40" font-size="10" fill="{t["muted"]}" letter-spacing="1" text-anchor="end">BY BYTES OF CODE</text>',
        f'<path d="M28 50h{w-56}" stroke="{t["frame"]}" stroke-width="1"/>',
    ]
    for i, (name, pct, color) in enumerate(rows):
        y = top_pad + row_h * i + 16
        bw = max(8, bar_max * pct / max_pct)
        delay = 0.12 * i
        svg += [
            f'<text class="mono" x="28" y="{y+4}" font-size="12" fill="{t["ink"]}">{name}</text>',
            f'<rect class="bar" style="animation-delay:{delay:.2f}s" x="{bar_x}" y="{y-4}" width="{bw:.1f}" height="8" rx="4" fill="{color}"/>',
            f'<text class="mono" x="{pct_x}" y="{y+4}" font-size="11" fill="{t["muted"]}" text-anchor="end">{pct:.1f}%</text>',
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
