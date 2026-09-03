# -*- coding: utf-8 -*-
"""Pure formatting helpers for the Classic Era viewer."""
# Kept free of CustomTkinter so unit tests can import them without a display.
# Re-exported from app so existing tests that import app keep working.

from __future__ import annotations

import os
import sqlite3

from ui.theme import GOLD, NOTE, WIN

DIM = "#8a8f98"
CARD = "#2b2d31"
HEAD = "#1e1f22"

DECISION_TAG = {
    "replay": "play-off",
    "coin_toss": "coin toss",
    "walkover": "walkover",
    "bye": "bye",
}

MATCH_SEP = "     \u00b7     "

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(HERE, "european_football.db")


def connect(path=None):
    """Open a long-lived SQLite connection with Row factory and FK pragma."""
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _field(row, key, default=None):
    """Read a key from a mapping or sqlite3.Row, returning default if absent/NULL."""
    try:
        keys = row.keys() if hasattr(row, "keys") else None
        if keys is not None and key not in keys:
            return default
        val = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if val is None else val


def load_club_name_cache(cur, edition_id=None):
    """Pre-load club_id -> name so tie rendering does not N+1 query the registry.

    When edition_id is omitted the cache is the canonical club.name (the shape
    pinned by tests/test_ui_helpers.py). Pass an edition for period-accurate
    display names; that path uses the richer loader in ui.data.
    """
    if edition_id is None:
        return {row["club_id"]: row["name"] for row in cur.execute(
            "SELECT club_id, name FROM club")}
    from ui.data import load_club_cache
    clubs = load_club_cache(cur, edition_id=edition_id)
    return {cid: info.get("display_name") or info.get("name")
            for cid, info in clubs.items()}


def aggregate_from_matches(tie, matches):
    """Aggregate over the two legs only (a play-off is a separate decider).

    Prefetched matches replace the per-tie SELECT that tie_aggregate used to
    run while rendering a season.
    """
    a, b = tie["club_a_id"], tie["club_b_id"]
    ga = gb = 0
    for m in matches:
        ln = _field(m, "leg_number")
        if ln is not None:
            try:
                if int(ln) not in (1, 2):
                    continue
            except (TypeError, ValueError):
                pass
        if _field(m, "home_score") is None:
            continue
        if m["home_club_id"] == a:
            ga += m["home_score"]
        if m["away_club_id"] == a:
            ga += m["away_score"]
        if m["home_club_id"] == b:
            gb += m["home_score"]
        if m["away_club_id"] == b:
            gb += m["away_score"]
    return ga, gb


def tie_aggregate(cur, tie):
    """Aggregate over the two legs only (a play-off is a separate decider)."""
    matches = cur.execute(
        "SELECT home_club_id, away_club_id, home_score, away_score, leg_number "
        "FROM match WHERE tie_id=? AND leg_number IN (1,2)", (tie["tie_id"],)
    ).fetchall()
    return aggregate_from_matches(tie, matches)


def format_attendance(attendance):
    """Return e.g. '135,000 spectators', or None when attendance is missing."""
    if attendance in (None, ""):
        return None
    try:
        n = int(attendance)
    except (TypeError, ValueError):
        return None
    return f"{n:,} spectators"


def match_extra_fragments(m):
    """Venue, date, referee and attendance fragments; empty values are omitted."""
    referee = _field(m, "referee")
    return [x for x in (
        _field(m, "venue"),
        _field(m, "match_date"),
        f"ref {referee}" if referee else None,
        format_attendance(_field(m, "attendance")),
    ) if x]


def format_match_line(home_name, away_name, m):
    """One-line summary of a leg, including aet and penalty shoot-out tags."""
    seg = f"{home_name} {_field(m, 'home_score')}-{_field(m, 'away_score')} {away_name}"
    if _field(m, "after_extra_time"):
        seg += " (aet)"
    hp = _field(m, "home_pens")
    ap = _field(m, "away_pens")
    if hp is not None and ap is not None:
        seg += f" (pens {hp}-{ap})"
    extras = match_extra_fragments(m)
    if extras:
        seg += "  (" + "; ".join(extras) + ")"
    return seg


def compose_tie_detail(parts, notes, separator=None):
    """Split match scores and historical notes.

    Notes are never discarded merely because match lines exist; the caller
    renders notes_callout in a distinct sub-label when it is non-empty.
    """
    if separator is None:
        separator = MATCH_SEP
    match_detail = separator.join(parts) if parts else ""
    notes_callout = notes or ""
    return match_detail, notes_callout


def _decider_leg(legs):
    """Third (or later) leg is the play-off / replay."""
    for m in legs:
        ln = _field(m, "leg_number")
        if ln is not None and int(ln) >= 3:
            return m
    if len(legs) >= 3:
        return legs[2]
    return None


def format_score_header(ga, gb, decided_by, legs):
    """Card header scoreline.

    Two-legged ties settled by replay or coin toss keep the aggregate visible
    but name the decider, so 5-5 is not mistaken for a scoring error.
    """
    if not legs:
        return "w/o"
    if decided_by == "single_match":
        return f"{ga} - {gb}"
    score = f"{ga}-{gb}"
    if decided_by == "replay":
        replay = _decider_leg(legs)
        if replay is not None and _field(replay, "home_score") is not None:
            hs = _field(replay, "home_score")
            aws = _field(replay, "away_score")
            score += f" (Replay: {hs}-{aws})"
    elif decided_by == "coin_toss":
        score += " (Coin Toss)"
    return score


def wraplength_for_width(width, padding=28, minimum=200):
    try:
        w = int(width)
    except (TypeError, ValueError):
        return minimum
    return max(minimum, w - padding)


def format_champion_banner(winner, runner_up):
    bits = []
    if winner:
        bits.append("\u2605 Champions\n%s" % winner)
    if runner_up:
        bits.append("Runner-up\n%s" % runner_up)
    return "\n\n".join(bits)


def missing_database_message(path=None):
    """In-window copy shown when european_football.db is absent (no sys.exit)."""
    shown = os.path.basename(path or DB_PATH)
    return (
        "%s was not found in this folder.\n\n"
        "Build it from the project directory with:\n"
        "    python build_database.py\n\n"
        "Then launch the viewer again."
    ) % shown
