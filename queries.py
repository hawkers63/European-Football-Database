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
