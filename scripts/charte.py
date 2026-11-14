"""The portfolio's palette and fonts (louis-pocheron.com, charte « Encre seule »), shared by the cards.

Light is the site's day paper, dark its night. The signal never carries text on the paper: it marks
(underlines, cursor, marker, squares); text on the signal is in ink.
"""
import base64
from pathlib import Path

FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"

THEMES = {
    "light": {
        "paper": "#efeee9", "ink": "#141412", "muted": "#5e5d58", "faint": "#a3a29b",
        "rule": "#d5d4cd", "bar": "#2a2a27", "on_bar": "#efeee9", "on_bar_muted": "#b3b1a9",
        "accent": "#ff5b14", "on_accent": "#141412",
    },
    "dark": {
        "paper": "#141412", "ink": "#efeee9", "muted": "#b3b1a9", "faint": "#5e5d58",
        "rule": "#2c2b28", "bar": "#d5d4cd", "on_bar": "#141412", "on_bar_muted": "#5e5d58",
        "accent": "#ff5b14", "on_accent": "#141412",
    },
}


def font_face(family, file):
    """An @font-face carrying the woff2 inline: an SVG shown through <img> loads nothing else."""
    data = base64.b64encode((FONTS / file).read_bytes()).decode()
    return f"@font-face {{ font-family: '{family}'; src: url(data:font/woff2;base64,{data}) format('woff2'); }}"


MONO = "font-family: 'Fragment Mono', ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace;"
MONO_FACE = lambda: font_face("Fragment Mono", "fragment-mono.woff2")
