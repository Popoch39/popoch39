"""The portfolio's palette and fonts (louis-pocheron.com, charte « Encre seule »), shared by the cards.

Light is the site's day paper, dark its night. The signal never carries text on the paper: it marks
(rules, squares, the marker); text on the signal is in ink.

Text is drawn as outlines: GitHub serves the repo's SVGs under `default-src 'none'`, which blocks any
font, embedded or not. The site's own font files are shaped with HarfBuzz (kerning and variable axes
included) and outlined with fontTools. Requires: pip install fonttools brotli uharfbuzz
"""
import io
from functools import cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONT_FILES = {"archivo": "archivo-variable.woff2", "mono": "fragment-mono-400.woff2"}

THEMES = {
    "light": {
        "paper": "#efeee9", "ink": "#141412", "muted": "#5e5d58", "faint": "#a3a29b",
        "rule": "#d5d4cd", "accent": "#ff5b14",
    },
    "dark": {
        "paper": "#141412", "ink": "#efeee9", "muted": "#b3b1a9", "faint": "#5e5d58",
        "rule": "#2c2b28", "accent": "#ff5b14",
    },
}


@cache
def _font(name):
    """HarfBuzz reads no woff2: the file is decompressed once, in memory."""
    tt = TTFont(FONTS / FONT_FILES[name])
    tt.flavor = None
    raw = io.BytesIO()
    tt.save(raw)
    return hb.Font(hb.Face(hb.Blob(raw.getvalue()))), tt["head"].unitsPerEm


def _shape(text, font, size, axes, tracking):
    hb_font, upem = _font(font)
    hb_font.set_variations(axes or {})
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf, {"kern": True, "liga": True})
    k = size / upem
    glyphs, pen_x = [], 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        glyphs.append((info.codepoint, pen_x + pos.x_offset * k, -pos.y_offset * k))
        pen_x += pos.x_advance * k + tracking
    return hb_font, k, glyphs, pen_x - tracking if glyphs else 0.0


def width(text, size, font="mono", axes=None, tracking=0):
    return _shape(text, font, size, axes, tracking)[3]


def text(text, x, y, size, fill, font="mono", axes=None, tracking=0, anchor="start", attrs=""):
    """One <path> holding the outlines of `text`, its baseline at y; `anchor` as in SVG."""
    hb_font, k, glyphs, w = _shape(text, font, size, axes, tracking)
    x0 = x - {"start": 0, "middle": w / 2, "end": w}[anchor]
    d = []
    for gid, gx, gy in glyphs:
        pen = SVGPathPen(None, ntos=lambda v: f"{v:.1f}".removesuffix(".0"))
        hb_font.draw_glyph_with_pen(gid, TransformPen(pen, (k, 0, 0, -k, x0 + gx, y + gy)))
        d.append(pen.getCommands())
    return f'<path{attrs} d="{"".join(d)}" fill="{fill}"/>'
