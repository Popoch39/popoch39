#!/usr/bin/env python3
"""Generate assets/header-dark.svg and header-light.svg — the profile hero card.

A synthetic topographic sheet of an imaginary Besançon-like terrain: a height
field (sum of anisotropic gaussians) contoured with marching squares, SE-flank
hachures from the gradient, a Doubs-style river meander, map furniture
(neatline, graticule, north arrow, scale bar) and the title block.
Run: python3 scripts/gen_header.py
"""
import math
from pathlib import Path

W, H = 1000, 260
# terrain occupies the right part of the sheet, clipped to the neatline
TX0, TX1, TY0, TY1 = 455, 984.5, 15.5, 244.5

THEMES = {
    "dark": {
        "bg": "#0d1117", "grid": "#21262d", "frame": "#30363d", "tick": "#484f58",
        "ink": "#e6edf3", "muted": "#8b949e", "contour": "#2dd4bf",
        "accent": "#d29922", "river": "#58a6ff",
    },
    "light": {
        "bg": "#ffffff", "grid": "#eff2f5", "frame": "#d0d7de", "tick": "#8c959f",
        "ink": "#1f2328", "muted": "#57606a", "contour": "#0f766e",
        "accent": "#b45309", "river": "#0969da",
    },
}

# ---------------------------------------------------------------- height field
PEAKS = [  # (cx, cy, sx, sy, rot_deg, amplitude) — two summits and a ridge
    (795, 105, 105, 62, -18, 1.00),
    (585, 68, 78, 46, 22, 0.62),
    (925, 195, 60, 42, -30, 0.48),
    # valley along the river course (negative -> keeps contours off the water)
    (640, 228, 130, 34, -6, -0.55),
    (480, 200, 70, 40, 15, -0.35),
]


def height(x, y):
    h = 0.0
    for cx, cy, sx, sy, rot, a in PEAKS:
        t = math.radians(rot)
        dx, dy = x - cx, y - cy
        u = dx * math.cos(t) + dy * math.sin(t)
        v = -dx * math.sin(t) + dy * math.cos(t)
        h += a * math.exp(-(u * u / (2 * sx * sx) + v * v / (2 * sy * sy)))
    return h


def gradient(x, y, eps=1.5):
    gx = (height(x + eps, y) - height(x - eps, y)) / (2 * eps)
    gy = (height(x, y + eps) - height(x, y - eps)) / (2 * eps)
    return gx, gy


# ------------------------------------------------------------ marching squares
def contour_polylines(level, nx=176, ny=88):
    xs = [TX0 + (TX1 - TX0) * i / nx for i in range(nx + 1)]
    ys = [TY0 + (TY1 - TY0) * j / ny for j in range(ny + 1)]
    grid = [[height(x, y) for x in xs] for y in ys]

    def interp(pa, pb, va, vb):
        t = (level - va) / (vb - va)
        return (pa[0] + t * (pb[0] - pa[0]), pa[1] + t * (pb[1] - pa[1]))

    segs = []
    for j in range(ny):
        for i in range(nx):
            v = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
            p = [(xs[i], ys[j]), (xs[i + 1], ys[j]), (xs[i + 1], ys[j + 1]), (xs[i], ys[j + 1])]
            idx = sum(1 << k for k in range(4) if v[k] > level)
            if idx in (0, 15):
                continue
            e = {}
            for k in range(4):
                a, b = k, (k + 1) % 4
                if (v[a] > level) != (v[b] > level):
                    e[k] = interp(p[a], p[b], v[a], v[b])
            ks = sorted(e)
            if len(ks) == 2:
                segs.append((e[ks[0]], e[ks[1]]))
            elif len(ks) == 4:  # saddle: pair edges 0-1 / 2-3
                segs.append((e[0], e[1]))
                segs.append((e[2], e[3]))

    key = lambda pt: (round(pt[0] * 4), round(pt[1] * 4))
    adj = {}
    for a, b in segs:
        adj.setdefault(key(a), []).append((a, b))
        adj.setdefault(key(b), []).append((b, a))

    seen, lines = set(), []
    def walk(start_pt):
        line = [start_pt]
        cur = start_pt
        while True:
            nxt = None
            for a, b in adj.get(key(cur), []):
                sk = tuple(sorted((key(a), key(b))))
                if sk not in seen:
                    seen.add(sk)
                    nxt = b
                    break
            if nxt is None:
                return line
            line.append(nxt)
            cur = nxt

    ends = [k for k, lst in adj.items() if len(lst) == 1]
    for k in ends:
        for a, _ in adj[k]:
            line = walk(a)
            if len(line) > 4:
                lines.append(line)
    for k, lst in adj.items():  # remaining closed loops
        for a, b in lst:
            sk = tuple(sorted((key(a), key(b))))
            if sk not in seen:
                line = walk(a)
                if len(line) > 8:
                    lines.append(line)
    return lines


def path_d(line):
    d = f"M{line[0][0]:.1f} {line[0][1]:.1f}"
    for x, y in line[1:]:
        d += f"L{x:.1f} {y:.1f}"
    return d


# ------------------------------------------------------------------- hachures
def hachures():
    out = []
    step = 11
    y = TY0 + 6
    while y < TY1 - 6:
        x = TX0 + 6
        while x < TX1 - 6:
            h = height(x, y)
            gx, gy = gradient(x, y)
            mag = math.hypot(gx, gy)
            if 0.22 < h < 0.82 and mag > 0.0035:
                dx, dy = -gx / mag, -gy / mag  # downhill
                if (dx + dy) / math.sqrt(2) > 0.25:  # SE-facing flank
                    l = 6.5
                    out.append((x, y, x + dx * l, y + dy * l))
            x += step
        y += step
    return out


# ---------------------------------------------------------------------- river
RIVER = ("M462 236"
         "C505 231 540 234 566 226"
         "C592 218 596 200 615 188"
         "C634 176 660 174 674 186"
         "C688 198 684 216 666 222"
         "C648 228 632 224 626 232"
         "C622 238 640 242 668 240"
         "C710 236 742 238 790 234"
         "C850 229 920 236 984 228")

# ------------------------------------------------------------------ rendering
def render(mode):
    t = THEMES[mode]
    levels = [0.14, 0.24, 0.34, 0.44, 0.54, 0.64, 0.74, 0.84, 0.93]
    index_levels = {0.34, 0.64}

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Louis Pocheron — Geospatial Software Engineer">',
         "<style>",
         ".serif { font-family: Georgia, 'Times New Roman', serif; }",
         ".mono  { font-family: ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace; }",
         ".draw { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 2s cubic-bezier(0.4,0,0.2,1) forwards; }",
         ".fade { opacity: 0; animation: fadein .9s ease-out forwards; }",
         ".f1 { animation-delay: .2s; } .f2 { animation-delay: .5s; }",
         ".f3 { animation-delay: .8s; } .f4 { animation-delay: 1.1s; }",
         ".hach { opacity: 0; animation: fadein 1.4s ease-out 2.1s forwards; }",
         f".pulse {{ transform-origin: var(--peak); animation: pulse 3s ease-out 2s infinite; opacity: 0; }}",
         "@keyframes draw { to { stroke-dashoffset: 0; } }",
         "@keyframes fadein { to { opacity: 1; } }",
         "@keyframes pulse { 0% { opacity:.7; transform: scale(.3); } 70%,100% { opacity:0; transform: scale(1.4); } }",
         "@media (prefers-reduced-motion: reduce) {",
         "  .draw { animation: none; stroke-dashoffset: 0; }",
         "  .fade, .hach { animation: none; opacity: 1; }",
         "  .pulse { animation: none; opacity: 0; } }",
         "</style>",
         f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>']

    # faint tile grid
    vlines = " ".join(f"M{x} 0V{H}" for x in range(76, W, 76))
    hlines = " ".join(f"M0 {y}H{W}" for y in range(65, H, 65))
    s.append(f'<g stroke="{t["grid"]}" stroke-width="1"><path d="{vlines}"/><path d="{hlines}"/></g>')

    # neatline + graticule
    s.append(f'<rect x="14.5" y="14.5" width="971" height="231" fill="none" stroke="{t["frame"]}" stroke-width="1"/>')
    s.append(f'<g stroke="{t["tick"]}" stroke-width="1"><path d="M255 14.5v7 M500 14.5v7 M745 14.5v7 '
             f'M255 245.5v-7 M500 245.5v-7 M745 245.5v-7 M14.5 130h7 M985.5 130h-7"/></g>')
    s.append(f'<g class="mono fade f1" font-size="10" fill="{t["muted"]}" letter-spacing="1">'
             f'<text x="24" y="34">47.2378° N</text>'
             f'<text x="976" y="34" text-anchor="end">6.0241° E</text></g>')

    # ---- terrain (clipped) ----
    s.append(f'<clipPath id="terrain"><rect x="{TX0}" y="{TY0}" width="{TX1-TX0}" height="{TY1-TY0}"/></clipPath>')
    s.append('<g clip-path="url(#terrain)">')

    # hachures (under the contours)
    hd = " ".join(f"M{a:.1f} {b:.1f}L{c:.1f} {d:.1f}" for a, b, c, d in hachures())
    s.append(f'<path class="hach" d="{hd}" stroke="{t["contour"]}" stroke-width="1" stroke-opacity="0.22" fill="none"/>')

    # contours
    label_spots = {}
    for li, lv in enumerate(levels):
        idx = lv in index_levels
        width_ = 1.5 if idx else 1
        op = 0.85 if idx else max(0.3, 0.28 + 0.5 * lv)
        delay = 0.10 * li
        for line in contour_polylines(lv):
            s.append(f'<path class="draw" style="animation-delay:{delay:.2f}s" d="{path_d(line)}" '
                     f'pathLength="1" fill="none" stroke="{t["contour"]}" stroke-opacity="{op:.2f}" '
                     f'stroke-width="{width_}" stroke-linejoin="round" stroke-linecap="round"/>')
            if idx and lv not in label_spots and len(line) > 120:
                label_spots[lv] = line[len(line) // 3]

    # elevation labels on index contours (one cote per level)
    cotes = {0.34: "270", 0.64: "330"}
    for lv, (lx, ly) in label_spots.items():
        s.append(f'<g class="fade f3"><rect x="{lx-14:.0f}" y="{ly-7:.0f}" width="28" height="13" fill="{t["bg"]}"/>'
                 f'<text class="mono" x="{lx:.0f}" y="{ly+3:.0f}" font-size="9.5" fill="{t["contour"]}" '
                 f'text-anchor="middle" letter-spacing="1">{cotes[lv]}</text></g>')

    # the river
    s.append(f'<path class="draw" style="animation-delay:1.1s;animation-duration:1.8s" d="{RIVER}" pathLength="1" '
             f'fill="none" stroke="{t["river"]}" stroke-width="1.6" stroke-opacity="0.85" stroke-linecap="round"/>')
    s.append('</g>')  # /terrain clip
    # river label, outside the clip so it isn't cut by the neatline
    s.append(f'<g class="fade f4"><rect x="748" y="222" width="66" height="14" fill="{t["bg"]}" fill-opacity="0.85"/>'
             f'<text class="serif" x="752" y="233" font-size="12" font-style="italic" '
             f'fill="{t["river"]}" fill-opacity="0.9" letter-spacing="1">le Doubs</text></g>')

    # summit marker (at the main peak)
    px, py = 795, 105
    s.append(f'<style>:root {{ --peak: {px}px {py}px; }}</style>')
    s.append(f'<circle class="pulse" cx="{px}" cy="{py}" r="22" fill="none" stroke="{t["accent"]}" stroke-width="1.5"/>')
    s.append(f'<g class="fade f4"><circle cx="{px}" cy="{py}" r="7" fill="none" stroke="{t["accent"]}" stroke-width="1.5"/>'
             f'<circle cx="{px}" cy="{py}" r="2.5" fill="{t["accent"]}"/></g>')

    # north arrow, on a small halo so it stays readable over the contours
    s.append(f'<g class="fade f2"><rect x="938" y="52" width="28" height="66" fill="{t["bg"]}" fill-opacity="0.85"/>'
             f'<g stroke="{t["muted"]}" fill="none" stroke-width="1.2"><path d="M952 96V66 M952 66l-5 9 M952 66l5 9"/></g>'
             f'<text class="serif" x="952" y="112" font-size="11" fill="{t["muted"]}" text-anchor="middle">N</text></g>')

    # ---- title block ----
    s.append(f'<text class="mono fade f1" x="60" y="78" font-size="12" fill="{t["accent"]}" letter-spacing="3">◉ BESANÇON, FRANCE</text>')
    s.append(f'<text class="serif fade f2" x="58" y="128" font-size="50" font-weight="bold" '
             f'style="font-variant: small-caps" fill="{t["ink"]}" letter-spacing="2">Louis Pocheron</text>')
    s.append(f'<g class="fade f2" stroke="{t["frame"]}" stroke-width="1"><path d="M60 144h368"/></g>')
    s.append(f'<text class="mono fade f3" x="60" y="170" font-size="14" fill="{t["contour"]}" letter-spacing="4">GEOSPATIAL SOFTWARE ENGINEER</text>')
    s.append(f'<text class="mono fade f4" x="60" y="196" font-size="12" fill="{t["muted"]}" letter-spacing="1">maps · tiles · pointclouds — @ DaVikingCode</text>')

    # scale bar
    s.append(f'<g class="fade f4"><g stroke="{t["muted"]}" stroke-width="1"><path d="M60 222h120 M60 218v8 M120 218v8 M180 218v8"/></g>'
             f'<rect x="60" y="220" width="30" height="4" fill="{t["muted"]}"/>'
             f'<rect x="120" y="220" width="30" height="4" fill="{t["muted"]}"/>'
             f'<text class="mono" x="188" y="226" font-size="9" fill="{t["muted"]}">1:25 000</text></g>')

    s.append("</svg>")
    return "\n".join(s)


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    for mode in THEMES:
        svg = render(mode)
        (out / f"header-{mode}.svg").write_text(svg)
        print(f"wrote assets/header-{mode}.svg ({len(svg)//1024} KB)")


if __name__ == "__main__":
    main()
