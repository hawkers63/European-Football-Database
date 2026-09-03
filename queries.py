# -*- coding: utf-8 -*-
"""
queries.py - shared read helpers over european_football.db.

Kept independent of the CustomTkinter viewer so the CLI and tests can reuse them.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional, Union

CursorLike = Union[sqlite3.Cursor, sqlite3.Connection]


def _cursor(db: CursorLike) -> sqlite3.Cursor:
    if isinstance(db, sqlite3.Connection):
        return db.cursor()
    return db


def get_club_display_name(db: CursorLike, club_id: int, edition_id: Optional[int] = None) -> str:
    """Return the period-accurate club name for an edition, else the canonical name.

    Looks up ``club_name_history`` for an exact ``edition_id`` match first, then
    falls back to a ``season_label`` match for that edition, then to ``club.name``.
    """
    cur = _cursor(db)
    if edition_id is not None:
        row = cur.execute(
            """SELECT name_used FROM club_name_history
               WHERE club_id = ? AND edition_id = ?
               LIMIT 1""",
            (club_id, edition_id),
        ).fetchone()
        if row:
            return row[0] if not isinstance(row, sqlite3.Row) else row["name_used"]

        row = cur.execute(
            """SELECT h.name_used
               FROM club_name_history h
               JOIN edition e ON e.season_label = h.season_label
               WHERE h.club_id = ? AND e.edition_id = ?
                 AND (h.edition_id IS NULL OR h.edition_id = e.edition_id)
               LIMIT 1""",
            (club_id, edition_id),
        ).fetchone()
        if row:
            return row[0] if not isinstance(row, sqlite3.Row) else row["name_used"]

    row = cur.execute("SELECT name FROM club WHERE club_id = ?", (club_id,)).fetchone()
    if not row:
        raise KeyError("unknown club_id %s" % club_id)
    return row[0] if not isinstance(row, sqlite3.Row) else row["name"]


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def standings_for_group(db: CursorLike, group_id: int, points_for_win: int,
                        tiebreak: Optional[str] = None) -> list:
    """Derive a ranked table from standing_match rows (never a stored ranking)."""
    from tools.standings import rank_table
    cur = _cursor(db)
    members = [r[0] if not isinstance(r, sqlite3.Row) else r["club_id"]
               for r in cur.execute(
                   "SELECT club_id FROM standing_member WHERE group_id = ?",
                   (group_id,))]
    key_of = {cid: str(cid) for cid in members}
    matches = []
    for r in cur.execute(
        """SELECT home_club_id, away_club_id, home_score, away_score,
                  awarded, walkover_winner_id
           FROM standing_match WHERE group_id = ?""",
        (group_id,),
    ):
        if isinstance(r, sqlite3.Row):
            home, away, hs, aws, awarded, wwin = (
                r["home_club_id"], r["away_club_id"], r["home_score"],
                r["away_score"], r["awarded"], r["walkover_winner_id"])
        else:
            home, away, hs, aws, awarded, wwin = r
        matches.append({
            "home": str(home), "away": str(away),
            "hs": hs, "as": aws,
            "awarded": bool(awarded),
            "walkover_winner": str(wwin) if wwin else None,
        })
    ranked = rank_table([str(c) for c in members], matches, points_for_win, tiebreak)
    # Restore integer club_ids.
    for row in ranked:
        row["club_id"] = int(row["club"])
    return ranked


def list_competition_transfers(db: CursorLike, edition_id: Optional[int] = None) -> list:
    """Return mid-season movement rows as data (no special-case logic)."""
    cur = _cursor(db)
    sql = """SELECT transfer_id, club_id, from_edition_id, from_rank,
                    to_edition_id, reason, notes
             FROM competition_transfer"""
    args: tuple = ()
    if edition_id is not None:
        sql += " WHERE from_edition_id = ? OR to_edition_id = ?"
        args = (edition_id, edition_id)
    sql += " ORDER BY transfer_id"
    rows = cur.execute(sql, args).fetchall()
    out = []
    for r in rows:
        if isinstance(r, sqlite3.Row):
            out.append(dict(r))
        else:
            out.append({
                "transfer_id": r[0], "club_id": r[1], "from_edition_id": r[2],
                "from_rank": r[3], "to_edition_id": r[4], "reason": r[5],
                "notes": r[6],
            })
    return out

