#!/usr/bin/env python3
"""Generate assets/header-light.svg and header-dark.svg — the profile's hero, after louis-pocheron.com.

The site's hero (03 · Méridien) on one sheet: the graticule round Besançon at a true minute pitch,
the name standing on the parallel that runs to the marker, the lede typing its versions as the site's
Vim buffer does, the scale, and the statusline. Palette and fonts from charte.py.
Run: python3 scripts/gen_header.py
"""
import math
from pathlib import Path

from charte import MONO, MONO_FACE, THEMES, font_face

W, H = 1000, 340
# The map's frame, and the statusline under it.
FX0, FY0, FX1, FY1 = 16.5, 56.5, 983.5, 300.5
BAR_Y = 316

LAT, LON = 47.2378, 6.0241
# The marker stands at 64 % of the map's width, as on the desktop site; the parallel at its height.
MX, MY = 640, 200
# One minute of latitude, px (two thirds of the site's 120); a minute of longitude narrows with the latitude.
LAT_MINUTE = 80
LON_MINUTE = LAT_MINUTE * math.cos(math.radians(LAT))

NAME_SIZE = 96
LEDE_SIZE = 20
LEDE_X, LEDE_Y = 56, 242
CHAR = 0.6 * LEDE_SIZE  # Fragment Mono advances 600/1000 em

# The site's lede (src/i18n/en.ts): "I build {what} for your {whose}." and who each version is for.
VERSIONS = [
    ("the maps", "power grid", "major energy companies"),
    ("the site", "guesthouse", "guesthouses and B&Bs"),
    ("the online store", "shop", "local shops"),
    ("the website", "restaurant", "restaurants, cafés and bakeries"),
    ("the appointment booking", "salon", "craftspeople, hairdressers and beauty salons"),
    ("the API", "back office", "product teams"),
    ("the map", "town", "town halls and local authorities"),
    ("the tool", "field team", "field workers"),
]
SLOT = 4.0  # s per version
TYPING = 1.4  # s to type a line
CYCLE = SLOT * len(VERSIONS)


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def angle(minutes):
    return f"{int(minutes // 60)}°{int(minutes % 60):02d}′"


def sexagesimal(value):
    s = round(abs(value) * 3600)
    return f"{s // 3600}°{s // 60 % 60:02d}′{s % 60:02d}″"


def graticule(t):
    """Whole minutes inside the frame, their lines and, every other one, their tick."""
    out = []
    lon0 = LON * 60
    lines = []
    m = math.ceil(lon0 - (MX - FX0) / LON_MINUTE)
    while (x := MX + (m - lon0) * LON_MINUTE) < FX1:
        lines.append(f"M{x:.1f} {FY0}V{FY1}")
        if m % 2 == 0 and 40 < x < FX1 - 70:
            out.append(f'<text x="{x:.1f}" y="{FY0 + 17}" text-anchor="middle">{angle(m)}</text>')
        m += 1
    lat0 = LAT * 60
    m = math.floor(lat0 + (MY - FY0) / LAT_MINUTE)
    while (y := MY - (m - lat0) * LAT_MINUTE) < FY1:
        if y > FY0 + 10:  # a line hugging the frame would read as a double border
            lines.append(f"M{FX0} {y:.1f}H{FX1}")
            if FY0 + 30 < y < FY1 - 10:
                out.append(f'<text x="{FX1 - 12}" y="{y - 6:.1f}" text-anchor="end">{angle(m)}</text>')
        m -= 1
    return (f'<path d="{" ".join(lines)}" stroke="{t["rule"]}" stroke-width="1"/>'
            f'<g class="mono" font-size="10" fill="{t["muted"]}" letter-spacing="0.5">{"".join(out)}</g>')


def lede(t):
    """Each version types itself in its slot, behind a block cursor, then gives way to the next."""
    css, groups = [], []
    for i, (what, whose, audience) in enumerate(VERSIONS):
        before, between = "I build ", " for your "
        line = f"{before}{what}{between}{whose}."
        width = len(line) * CHAR
        x_what = LEDE_X + len(before) * CHAR
        x_whose = x_what + len(what + between) * CHAR
        typed = 100 * TYPING / CYCLE
        css.append(
            f"@keyframes type{i} {{ 0% {{ transform: translateX(0); animation-timing-function: steps({len(line)}, end); }}"
            f" {typed:.2f}%, 100% {{ transform: translateX({width:.0f}px); }} }}"
            f" .v{i} {{ animation-delay: {i * SLOT:.0f}s; }} .v{i} .typed {{ animation: type{i} {CYCLE:.0f}s {i * SLOT:.0f}s infinite; }}")
        underline = lambda x, word: (f'<rect x="{x:.1f}" y="{LEDE_Y + 6}" width="{len(word) * CHAR:.1f}" height="3" '
                                     f'fill="{t["accent"]}"/>')
        groups.append(
            f'<g class="v v{i}"{"" if i == 0 else " opacity=\"0\""}>'
            f'<clipPath id="typed{i}"><rect class="typed" x="{LEDE_X - width:.1f}" y="{LEDE_Y - 22}" '
            f'width="{width:.1f}" height="34" style="transform: translateX({width:.0f}px)"/></clipPath>'
            f'<g clip-path="url(#typed{i})">'
            f'<text class="mono" x="{LEDE_X}" y="{LEDE_Y}" font-size="{LEDE_SIZE}" fill="{t["ink"]}" xml:space="preserve">{esc(line)}</text>'
            f'{underline(x_what, what)}{underline(x_whose, whose)}</g>'
            f'<rect class="typed" x="{LEDE_X}" y="{LEDE_Y - 18}" width="{CHAR:.0f}" height="24" fill="{t["accent"]}" '
            f'style="transform: translateX({width:.0f}px)"/>'
            f'<g class="mono" font-size="11" fill="{t["muted"]}">'
            f'<text x="{LEDE_X}" y="{LEDE_Y + 30}">version {i + 1}/{len(VERSIONS)}</text>'
            f'<text x="{LEDE_X}" y="{LEDE_Y + 46}">for: {esc(audience)}</text></g></g>')
    return "\n".join(css), "\n".join(groups)


def statusline(t):
    y, h = BAR_Y, H - BAR_Y
    mid = y + h / 2 + 4
    return (f'<rect y="{y}" width="{W}" height="{h}" fill="{t["bar"]}"/>'
            f'<rect y="{y}" width="72" height="{h}" fill="{t["accent"]}"/>'
            f'<rect x="{W - 44}" y="{y}" width="44" height="{h}" fill="{t["accent"]}"/>'
            f'<g class="mono" font-size="11">'
            f'<text x="36" y="{mid}" text-anchor="middle" fill="{t["on_accent"]}" font-weight="bold">NORMAL</text>'
            f'<text x="88" y="{mid}" fill="{t["on_bar"]}">main</text>'
            f'<text x="140" y="{mid}" fill="{t["on_bar"]}">~/louis/README.md</text>'
            f'<text x="{W - 100}" y="{mid}" text-anchor="end" fill="{t["on_bar_muted"]}">utf-8 · markdown</text>'
            f'<text x="{W - 60}" y="{mid}" text-anchor="end" fill="{t["on_bar"]}">Top</text>'
            f'<text x="{W - 22}" y="{mid}" text-anchor="middle" fill="{t["on_accent"]}">:wq</text></g>')


def render(mode):
    t = THEMES[mode]
    lede_css, lede_svg = lede(t)
    rise = NAME_SIZE * 0.06
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Louis Pocheron — application designer &amp; developer, GIS &amp; mapping, Besançon">',
        "<style>",
        MONO_FACE(),
        font_face("Archivo Name", "archivo-name.woff2"),
        f".mono {{ {MONO} }}",
        ".name { font-family: 'Archivo Name', 'Archivo Narrow', 'Arial Narrow', sans-serif; font-weight: 800; }",
        # No backwards fill: while a version waits for its slot, its opacity="0" holds.
        f".v {{ animation: slot {CYCLE:.0f}s infinite; }}",
        f"@keyframes slot {{ 0%, {100 / len(VERSIONS) - 0.01:.2f}% {{ opacity: 1; }} {100 / len(VERSIONS):.2f}%, 100% {{ opacity: 0; }} }}",
        lede_css,
        ".rise { animation: rise .9s cubic-bezier(.2,.7,.2,1) both; }",
        f"@keyframes rise {{ from {{ transform: translateY({NAME_SIZE}px); }} }}",
        ".ring { transform-origin: %dpx %dpx; animation: ring 3s ease-out 1s infinite; }" % (MX, MY),
        "@keyframes ring { 0% { opacity: .8; transform: scale(.5); } 70%, 100% { opacity: 0; transform: scale(1.8); } }",
        "@media (prefers-reduced-motion: reduce) {",
        "  .v, .typed, .rise, .ring { animation: none !important; } .v { opacity: 0; } .v0 { opacity: 1; } .ring { opacity: 0; } }",
        "</style>",
        f'<rect width="{W}" height="{H}" fill="{t["paper"]}"/>',
        # the site's header: name of the job, specialty, address
        f'<g class="mono" font-size="11" fill="{t["muted"]}">'
        f'<text x="16" y="31" fill="{t["ink"]}">Louis Pocheron</text>'
        f'<text x="250" y="31">Application designer &amp; developer</text>'
        f'<text x="560" y="31">GIS &amp; mapping at industrial scale</text>'
        f'<text x="984" y="31" text-anchor="end" fill="{t["ink"]}">louis-pocheron.com ↗</text></g>',
        f'<path d="M16 44.5H984" stroke="{t["ink"]}" stroke-width="1"/>',
        graticule(t),
        f'<rect x="{FX0}" y="{FY0}" width="{FX1 - FX0}" height="{FY1 - FY0}" fill="none" stroke="{t["ink"]}" stroke-width="1"/>',
        # the name, each word rising out of the parallel it stands on
        f'<clipPath id="above"><rect x="{FX0}" y="{FY0}" width="{MX - FX0}" height="{MY - FY0 + rise:.1f}"/></clipPath>',
        f'<g clip-path="url(#above)" class="name" font-size="{NAME_SIZE}" letter-spacing="{-0.03 * NAME_SIZE:.1f}" fill="{t["ink"]}">'
        f'<text class="rise" x="52" y="{MY}" word-spacing="{0.12 * NAME_SIZE:.0f}">Louis Pocheron</text></g>',
        f'<path d="M{FX0} {MY + 0.5}H{MX - 16}" stroke="{t["ink"]}" stroke-width="1"/>',
        # Besançon
        f'<circle class="ring" cx="{MX}" cy="{MY}" r="14" fill="none" stroke="{t["accent"]}" stroke-width="1.5" opacity="0"/>',
        f'<circle cx="{MX}" cy="{MY}" r="14" fill="none" stroke="{t["accent"]}" stroke-width="1"/>',
        f'<rect x="{MX - 5}" y="{MY - 5}" width="10" height="10" fill="{t["accent"]}"/>',
        f'<g class="mono" font-size="11" fill="{t["ink"]}"><text x="{MX + 26}" y="{MY + 22}">Besançon</text>'
        f'<text x="{MX + 26}" y="{MY + 38}" fill="{t["muted"]}">{sexagesimal(LAT)} N · {sexagesimal(LON)} E</text></g>',
        lede_svg,
        # the scale: 1 km at this pitch
        scale(t),
        statusline(t),
        "</svg>",
    ]
    return "\n".join(s)


def scale(t):
    km = LAT_MINUTE * 1000 / 1852
    x1, y = FX1 - 48, FY1 - 16
    x0 = x1 - km
    return (f'<g class="mono" font-size="9" fill="{t["muted"]}"><text x="{x0 - 6:.1f}" y="{y + 4}" text-anchor="end">0</text>'
            f'<text x="{x1 + 6}" y="{y + 4}">1 km</text></g>'
            f'<rect x="{x0:.1f}" y="{y}" width="{km:.1f}" height="4" fill="none" stroke="{t["ink"]}" stroke-width="1"/>'
            f'<rect x="{x0:.1f}" y="{y}" width="{km / 2:.1f}" height="4" fill="{t["ink"]}"/>')


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    for mode in THEMES:
        svg = render(mode)
        (out / f"header-{mode}.svg").write_text(svg)
        print(f"wrote assets/header-{mode}.svg ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
