# -*- coding: utf-8 -*-
"""Yearbook colour palette for the Classic Era viewer.

CustomTkinter widget kwargs stay American (`fg_color`); names and comments
here use British spelling (`colour`).
"""

from __future__ import annotations

# Victory green (winner accent) and brass/gold (champions).
WIN = "#2ea043"
GOLD = "#d4af37"
NOTE = GOLD

DARK = {
    "card": "#2b2d31",
    "head": "#1e1f22",
    "dim": "#8a8f98",
    "win": WIN,
    "gold": GOLD,
    "note": NOTE,
    "pill": "#3a3d44",
    "callout_bg": "#3a3420",
    "border": "#3e4147",
    "score_pill": "#1e1f22",
    "canvas": "#1e1f22",
    "node": "#2b2d31",
    "text": "#f2f3f5",
}

LIGHT = {
    "card": "#f6f3ec",
    "head": "#e8e2d4",
    "dim": "#5c6169",
    "win": "#1a7f37",
    "gold": "#b8960c",
    "note": "#8a7010",
    "pill": "#e4dfd2",
    "callout_bg": "#f4ecd0",
    "border": "#d4cbb8",
    "score_pill": "#efe9d8",
    "canvas": "#efe9d8",
    "node": "#f6f3ec",
    "text": "#1e1f22",
}


def palette(mode: str = "dark") -> dict:
    """Return the colour table for ``dark`` or ``light`` appearance."""
    if str(mode).lower().startswith("light"):
        return dict(LIGHT)
    return dict(DARK)
