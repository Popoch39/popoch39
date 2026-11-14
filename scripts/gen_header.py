#!/usr/bin/env python3
"""Generate assets/header-light.svg and header-dark.svg — the profile's hero, after louis-pocheron.com.

The site's hero (03 · Méridien) as a title sheet: the graticule round Besançon at a true minute
pitch, the name standing on the parallel that runs to the marker, the role and what it covers under
it, the scale. Palette and fonts from charte.py, every text outlined.
Run: python3 scripts/gen_header.py
"""
import math
from pathlib import Path

from charte import THEMES, text, width

W, H = 1000, 300
FX0, FY0, FX1, FY1 = 16.5, 16.5, 983.5, 283.5

LAT, LON = 47.2378, 6.0241
MX, MY = 700, 150  # the marker, and the parallel the name stands on
LAT_MINUTE = 80  # px; two thirds of the site's pitch
LON_MINUTE = LAT_MINUTE * math.cos(math.radians(LAT))

LEFT = 48
NAME = "Louis Pocheron"
NAME_AXES = {"wght": 800, "wdth": 75}  # the site's hero title
ROLE = "Geospatial Software Engineer"
ROLE_AXES = {"wght": 700, "wdth": 100}
TAGLINE = "Tile servers, caches & point clouds  ·  TypeScript on top, Rust underneath"


def angle(minutes):
    return f"{int(minutes // 60)}°{int(minutes % 60):02d}′"


def sexagesimal(value):
    s = round(abs(value) * 3600)
    return f"{s // 3600}°{s // 60 % 60:02d}′{s % 60:02d}″"


def graticule(t):
    """Whole minutes inside the frame: their lines and, every other one, their tick."""
    lines, ticks = [], []
    lon0, lat0 = LON * 60, LAT * 60
    m = math.ceil(lon0 - (MX - FX0) / LON_MINUTE)
    while (x := MX + (m - lon0) * LON_MINUTE) < FX1:
        lines.append(f"M{x:.1f} {FY0}V{FY1}")
        if m % 2 == 0 and 40 < x < FX1 - 70:
            ticks.append(text(angle(m), x, FY0 + 17, 10, t["muted"], tracking=0.5, anchor="middle"))
        m += 1
    m = math.floor(lat0 + (MY - FY0) / LAT_MINUTE)
    while (y := MY - (m - lat0) * LAT_MINUTE) < FY1:
        if y > FY0 + 10:  # a line hugging the frame would read as a double border
            lines.append(f"M{FX0} {y:.1f}H{FX1}")
            if FY0 + 30 < y < FY1 - 10:
                ticks.append(text(angle(m), FX1 - 12, y - 6, 10, t["muted"], tracking=0.5, anchor="end"))
        m -= 1
    return f'<path d="{" ".join(lines)}" stroke="{t["rule"]}" stroke-width="1"/>' + "".join(ticks)


def scale(t):
    km = LAT_MINUTE * 1000 / 1852
    x1, y = FX1 - 48, FY1 - 18
    x0 = x1 - km
    return (text("0", x0 - 6, y + 4, 9, t["muted"], anchor="end") + text("1 km", x1 + 6, y + 4, 9, t["muted"])
            + f'<rect x="{x0:.1f}" y="{y}" width="{km:.1f}" height="4" fill="none" stroke="{t["ink"]}" stroke-width="1"/>'
            f'<rect x="{x0:.1f}" y="{y}" width="{km / 2:.1f}" height="4" fill="{t["ink"]}"/>')


def render(mode):
    t = THEMES[mode]
    # The largest name that leaves the marker its room.
    size = min(104, (MX - 44 - LEFT) / width(NAME, 1, "archivo", NAME_AXES, -0.03))
    tracking = -0.03 * size
    site = "louis-pocheron.com ↗"
    site_w = width(site, 12)
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Louis Pocheron — Geospatial Software Engineer. Tile servers, caches and point clouds. Besançon, France.">',
        "<style>",
        ".rise { animation: rise .9s cubic-bezier(.2,.7,.2,1) both; }",
        f"@keyframes rise {{ from {{ transform: translateY({size:.0f}px); }} }}",
        ".fade { animation: fade .8s ease-out both; } .d1 { animation-delay: .35s; } .d2 { animation-delay: .55s; } .d3 { animation-delay: .75s; }",
        "@keyframes fade { from { opacity: 0; transform: translateY(6px); } }",
        ".ring { transform-origin: %dpx %dpx; animation: ring 3s ease-out 1.2s infinite; }" % (MX, MY),
        "@keyframes ring { 0% { opacity: .8; transform: scale(.5); } 70%, 100% { opacity: 0; transform: scale(1.8); } }",
        "@media (prefers-reduced-motion: reduce) { .rise, .fade, .ring { animation: none; } }",
        "</style>",
        f'<rect width="{W}" height="{H}" fill="{t["paper"]}"/>',
        graticule(t),
        f'<rect x="{FX0}" y="{FY0}" width="{FX1 - FX0}" height="{FY1 - FY0}" fill="none" stroke="{t["ink"]}" stroke-width="1"/>',
        # the name rises out of the parallel it stands on
        f'<clipPath id="above"><rect x="{FX0}" y="{FY0}" width="{MX - FX0}" height="{MY - FY0 + 1}"/></clipPath>',
        f'<g clip-path="url(#above)">'
        + text(NAME, LEFT, MY, size, t["ink"], "archivo", NAME_AXES, tracking, attrs=' class="rise"') + "</g>",
        f'<path d="M{FX0} {MY + 0.5}H{MX - 18}" stroke="{t["ink"]}" stroke-width="1"/>',
        # what he does
        f'<g class="fade d1">{text(ROLE, LEFT + 2, MY + 46, 30, t["ink"], "archivo", ROLE_AXES, -0.3)}</g>',
        f'<g class="fade d2">{text(TAGLINE, LEFT + 3, MY + 76, 13, t["muted"])}</g>',
        f'<g class="fade d3"><rect x="{LEFT + 3}" y="{FY1 - 31}" width="8" height="8" fill="{t["accent"]}"/>'
        + text(site, LEFT + 19, FY1 - 23, 12, t["ink"])
        + text("·  Da Viking Code, Besançon", LEFT + 19 + site_w + 12, FY1 - 23, 12, t["muted"]) + "</g>",
        # Besançon
        f'<circle class="ring" cx="{MX}" cy="{MY}" r="14" fill="none" stroke="{t["accent"]}" stroke-width="1.5" opacity="0"/>',
        f'<circle cx="{MX}" cy="{MY}" r="14" fill="none" stroke="{t["accent"]}" stroke-width="1"/>',
        f'<rect x="{MX - 5}" y="{MY - 5}" width="10" height="10" fill="{t["accent"]}"/>',
        text("Besançon", MX + 26, MY + 24, 12, t["ink"]),
        text(f"{sexagesimal(LAT)} N · {sexagesimal(LON)} E", MX + 26, MY + 41, 11, t["muted"]),
        scale(t),
        "</svg>",
    ]
    return "\n".join(s)


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    for mode in THEMES:
        svg = render(mode)
        (out / f"header-{mode}.svg").write_text(svg)
        print(f"wrote assets/header-{mode}.svg ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
