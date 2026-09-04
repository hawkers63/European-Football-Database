# -*- coding: utf-8 -*-
"""
queries.py - shared read helpers over european_football.db.

Kept independent of the CustomTkinter viewer so the CLI and tests can reuse them.

Statistical helpers (head-to-head, goals, leaderboards) are derived from
verified ``match`` / ``tie`` / ``edition`` rows. Totals are never stored as
denormalised career tables. Period club names are display-only; joins use
``club_id``.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional, Union

CursorLike = Union[sqlite3.Cursor, sqlite3.Connection]

LEADERBOARD_KINDS = ("titles", "matches", "wins", "gd", "finals")

# Documented leaderboard sort orders (British English labels live in the CLI).
LEADERBOARD_SORT = {
    "titles": "titles descending, then canonical club name ascending",
    "matches": (
        "matches played descending, then wins descending, then goal difference "
        "descending, then canonical club name ascending"
    ),
    "wins": (
        "wins descending, then matches played descending, then goal difference "
        "descending, then canonical club name ascending"
    ),
    "gd": (
        "goal difference descending, then matches played descending, then wins "
        "descending, then canonical club name ascending"
    ),
    "finals": (
        "finals reached descending, then titles descending, then canonical club "
        "name ascending"
    ),
}

_MATCH_SELECT = """
SELECT m.match_id, m.tie_id, m.leg_number, m.match_date,
       m.home_club_id, m.away_club_id, m.home_score, m.away_score,
       m.after_extra_time, m.venue, m.notes AS match_notes,
       t.decided_by, t.notes AS tie_notes,
       t.club_a_id, t.club_b_id, t.winner_club_id,
       r.round_id, r.name AS round_name, r.round_order,
       e.edition_id, e.season_label, e.start_year, e.competition_name,
       l.name AS lineage_name, l.lineage_id
  FROM match m
  JOIN tie t ON t.tie_id = m.tie_id
  JOIN round r ON r.round_id = t.round_id
  JOIN edition e ON e.edition_id = r.edition_id
  JOIN lineage l ON l.lineage_id = e.lineage_id
"""


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


def get_club(db: CursorLike, club_id: int) -> sqlite3.Row:
    """Return the canonical club row, or raise KeyError."""
    cur = _cursor(db)
    row = cur.execute(
        "SELECT club_id, name, country, city, notes FROM club WHERE club_id = ?",
        (club_id,),
    ).fetchone()
    if not row:
        raise KeyError("unknown club_id %s" % club_id)
    return row


def club_id_by_name(db: CursorLike, name: str) -> int:
    """Resolve a canonical ``club.name`` to ``club_id``."""
    cur = _cursor(db)
    row = cur.execute("SELECT club_id FROM club WHERE name = ?", (name,)).fetchone()
    if not row:
        raise KeyError("unknown club name %s" % name)
    return row["club_id"] if isinstance(row, sqlite3.Row) else row[0]


find_club_id = club_id_by_name


def _apply_limit(rows: list, limit: Optional[int]) -> list:
    if limit is None or limit == 0:
        return rows
    return rows[:limit]


def _with_rank(rows: list) -> list:
    for i, rec in enumerate(rows, start=1):
        rec["rank"] = i
    return rows


def is_final_round(name: str) -> bool:
    """True for the trophy Final, not quarter-finals or semi-finals."""
    n = (name or "").strip().lower()
    if "quarter" in n or "semi" in n:
        return False
    return n == "final" or n.endswith(" final")


def _match_contribution(match_row: Any, club_id: int):
    """Return (goals_for, goals_against, result) for club_id, or None.

    Extra-time scores already stored on the match row are used as-is. Unscored
    rows (NULL home or away) are skipped so walkovers without a scoreline are
    never silently treated as 3-0.
    """
    hs = match_row["home_score"]
    as_ = match_row["away_score"]
    if hs is None or as_ is None:
        return None
    home = match_row["home_club_id"]
    away = match_row["away_club_id"]
    if club_id == home:
        gf, ga = hs, as_
    elif club_id == away:
        gf, ga = as_, hs
    else:
        return None
    if gf > ga:
        result = "W"
    elif gf < ga:
        result = "L"
    else:
        result = "D"
    return gf, ga, result


def _empty_record(club_id: int) -> dict:
    return {
        "club_id": club_id,
        "matches_played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_difference": 0,
        "average_goals_per_match": 0.0,
        "finals_matches": 0,
        "finals_goals_for": 0,
        "finals_goals_against": 0,
    }


def _finalise_record(rec: dict) -> dict:
    rec["goal_difference"] = rec["goals_for"] - rec["goals_against"]
    played = rec["matches_played"]
    rec["average_goals_per_match"] = round((rec["goals_for"] / played), 2) if played else 0.0
    return rec


def club_match_record(
    db: CursorLike,
    club_id: int,
    season_label: Optional[str] = None,
) -> dict:
    """Played / W-D-L / goals from verified match rows only.

    Each match row is counted once: two-legged ties contribute two matches,
    play-offs and replays contribute their extra legs, and a single-leg final
    contributes one. Replay legs are not double-counted against the aggregate.
    Walkovers have no match rows and do not alter this record.
    """
    get_club(db, club_id)
    cur = _cursor(db)
    sql = _MATCH_SELECT + " WHERE (m.home_club_id = ? OR m.away_club_id = ?)"
    params: list[Any] = [club_id, club_id]
    if season_label:
        sql += " AND e.season_label = ?"
        params.append(season_label)
    rows = cur.execute(sql, params).fetchall()
    rec = _empty_record(club_id)
    for m in rows:
        contrib = _match_contribution(m, club_id)
        if contrib is None:
            continue
        gfor, gagt, result = contrib
        rec["matches_played"] += 1
        rec["goals_for"] += gfor
        rec["goals_against"] += gagt
        if result == "W":
            rec["wins"] += 1
        elif result == "L":
            rec["losses"] += 1
        else:
            rec["draws"] += 1
        if is_final_round(m["round_name"]):
            rec["finals_matches"] += 1
            rec["finals_goals_for"] += gfor
            rec["finals_goals_against"] += gagt
    return _finalise_record(rec)


def _hat_trick_clause():
    return """(
        (t.notes IS NOT NULL AND (
            lower(t.notes) LIKE '%hat-trick%'
            OR lower(t.notes) LIKE '%hat trick%'
            OR lower(t.notes) LIKE '%hattrick%'))
        OR (m.notes IS NOT NULL AND (
            lower(m.notes) LIKE '%hat-trick%'
            OR lower(m.notes) LIKE '%hat trick%'
            OR lower(m.notes) LIKE '%hattrick%'))
    )"""


def hat_trick_notes(
    db: CursorLike,
    club_id: Optional[int] = None,
    edition_id: Optional[int] = None,
) -> list:
    """Hat-trick notes only when stored on ``match.notes`` or ``tie.notes``.

    Scorers are never invented. An empty list means the loaded database has
    no such note, not that no hat-trick occurred in history.
    """
    cur = _cursor(db)
    sql = """
        SELECT e.season_label, e.competition_name, e.edition_id,
               r.name AS round_name, t.tie_id, m.match_id,
               t.notes AS tie_notes, m.notes AS match_notes
          FROM tie t
          JOIN round r ON r.round_id = t.round_id
          JOIN edition e ON e.edition_id = r.edition_id
          LEFT JOIN match m ON m.tie_id = t.tie_id
         WHERE """ + _hat_trick_clause()
    params: list[Any] = []
    if edition_id is not None:
        sql += " AND e.edition_id = ?"
        params.append(edition_id)
    if club_id is not None:
        sql += """ AND (t.club_a_id = ? OR t.club_b_id = ?
                    OR m.home_club_id = ? OR m.away_club_id = ?)"""
        params.extend([club_id, club_id, club_id, club_id])
    sql += " ORDER BY e.start_year, r.round_order, t.tie_id, m.leg_number"
    out = []
    seen = set()
    for row in cur.execute(sql, params):
        for source, text in (("tie.notes", row["tie_notes"]), ("match.notes", row["match_notes"])):
            if not text:
                continue
            lowered = text.lower()
            if not any(tok in lowered for tok in ("hat-trick", "hat trick", "hattrick")):
                continue
            key = (row["tie_id"], row["match_id"], source, text)
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "season_label": row["season_label"],
                "competition_name": row["competition_name"],
                "round_name": row["round_name"],
                "tie_id": row["tie_id"],
                "match_id": row["match_id"],
                "source": source,
                "notes": text,
            })
    return out


def highest_scoring_ties(
    db: CursorLike,
    club_id: Optional[int] = None,
    season_label: Optional[str] = None,
    limit: Optional[int] = 5,
) -> list:
    """Ties ranked by total goals on their match rows (legs plus replays)."""
    cur = _cursor(db)
    sql = """
        SELECT t.tie_id, t.club_a_id, t.club_b_id, t.decided_by, t.notes,
               r.name AS round_name, e.edition_id, e.season_label,
               e.competition_name, e.start_year, l.name AS lineage_name,
               SUM(m.home_score + m.away_score) AS total_goals,
               COUNT(m.match_id) AS match_count
          FROM tie t
          JOIN match m ON m.tie_id = t.tie_id
          JOIN round r ON r.round_id = t.round_id
          JOIN edition e ON e.edition_id = r.edition_id
          JOIN lineage l ON l.lineage_id = e.lineage_id
         WHERE m.home_score IS NOT NULL AND m.away_score IS NOT NULL
    """
    params: list[Any] = []
    if club_id is not None:
        sql += " AND (t.club_a_id = ? OR t.club_b_id = ?)"
        params.extend([club_id, club_id])
    if season_label:
        sql += " AND e.season_label = ?"
        params.append(season_label)
    sql += """
         GROUP BY t.tie_id
         ORDER BY total_goals DESC, e.start_year ASC, r.round_order ASC, t.tie_id ASC
    """
    rows = cur.execute(sql, params).fetchall()
    out = []
    for row in rows:
        total = int(row["total_goals"] or 0)
        legs = row["match_count"]
        out.append({
            "tie_id": row["tie_id"],
            "club_a_id": row["club_a_id"],
            "club_b_id": row["club_b_id"],
            "club_a_name": get_club_display_name(cur, row["club_a_id"], row["edition_id"]),
            "club_b_name": get_club_display_name(cur, row["club_b_id"], row["edition_id"]),
            "total_goals": total,
            "goals": total,
            "match_count": legs,
            "legs": legs,
            "decided_by": row["decided_by"],
            "season_label": row["season_label"],
            "competition_name": row["competition_name"],
            "lineage_name": row["lineage_name"],
            "round_name": row["round_name"],
            "notes": row["notes"],
        })
    return _apply_limit(out, limit)


def club_record(
    db: CursorLike,
    club_id: int,
    season_label: Optional[str] = None,
    highest_n: int = 5,
) -> dict:
    """Per-club match record, titles, finals goals and highest-scoring ties."""
    rec = club_match_record(db, club_id, season_label=season_label)
    club = get_club(db, club_id)
    rec["name"] = club["name"]
    rec["country"] = club["country"]
    rec["highest_scoring_ties"] = highest_scoring_ties(
        db, club_id, season_label=season_label, limit=highest_n,
    )
    if season_label:
        # hat_trick_notes(edition_id=) only scopes to one edition, so union
        # over every edition of this season_label (it may span lineages).
        rec["hat_trick_notes"] = []
        for e in editions_for_season(db, season_label):
            rec["hat_trick_notes"].extend(
                hat_trick_notes(db, club_id=club_id, edition_id=e["edition_id"])
            )
    else:
        rec["hat_trick_notes"] = hat_trick_notes(db, club_id=club_id)
    cur = _cursor(db)
    sql = """SELECT edition_id, season_label, competition_name, start_year,
                    winner_club_id, runner_up_club_id
               FROM edition
              WHERE winner_club_id = ? OR runner_up_club_id = ?"""
    params: list[Any] = [club_id, club_id]
    if season_label:
        sql += " AND season_label = ?"
        params.append(season_label)
    sql += " ORDER BY start_year, competition_name"
    editions = cur.execute(sql, params).fetchall()
    titles = sum(1 for e in editions if e["winner_club_id"] == club_id)
    runner_up = sum(1 for e in editions if e["runner_up_club_id"] == club_id)
    rec["titles"] = titles
    rec["runner_up_finishes"] = runner_up
    rec["runner_up"] = runner_up
    rec["finals_reached"] = titles + runner_up
    rec["trophy_finishes"] = []
    for e in editions:
        rec["trophy_finishes"].append({
            "edition_id": e["edition_id"],
            "season_label": e["season_label"],
            "competition_name": e["competition_name"],
            "role": "Champion" if e["winner_club_id"] == club_id else "Runner-up",
            "display_name": get_club_display_name(cur, club_id, e["edition_id"]),
        })
    rec["period_names"] = [
        {"season_label": h["season_label"], "name_used": h["name_used"]}
        for h in cur.execute(
            """SELECT season_label, name_used FROM club_name_history
               WHERE club_id = ? ORDER BY season_label""",
            (club_id,),
        )
    ]
    return rec


club_goal_stats = club_record
club_all_time_record = club_record


def editions_for_season(db: CursorLike, season_label: str) -> list:
    cur = _cursor(db)
    return list(cur.execute(
        """SELECT edition_id, season_label, competition_name, start_year,
                  winner_club_id, runner_up_club_id, notes, lineage_id
             FROM edition
            WHERE season_label = ?
            ORDER BY competition_name""",
        (season_label,),
    ))


def edition_goal_stats(db: CursorLike, edition_id: int) -> dict:
    """Total goals for an edition, plus per-round totals and stored hat-trick notes."""
    cur = _cursor(db)
    e = cur.execute(
        """SELECT e.*, l.name AS lineage_name
             FROM edition e
             JOIN lineage l ON l.lineage_id = e.lineage_id
            WHERE e.edition_id = ?""",
        (edition_id,),
    ).fetchone()
    if not e:
        raise KeyError("unknown edition_id %s" % edition_id)
    total = cur.execute(
        """SELECT COALESCE(SUM(m.home_score + m.away_score), 0) AS goals,
                  COUNT(m.match_id) AS matches
             FROM match m
             JOIN tie t ON t.tie_id = m.tie_id
             JOIN round r ON r.round_id = t.round_id
            WHERE r.edition_id = ?
              AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL""",
        (edition_id,),
    ).fetchone()
    rounds = []
    round_rows = list(cur.execute(
        """SELECT round_id, name, round_order FROM round
           WHERE edition_id = ? ORDER BY round_order""",
        (edition_id,),
    ))
    for rnd in round_rows:
        g = cur.execute(
            """SELECT COALESCE(SUM(m.home_score + m.away_score), 0) AS goals,
                      COUNT(m.match_id) AS matches
                 FROM match m
                 JOIN tie t ON t.tie_id = m.tie_id
                WHERE t.round_id = ?
                  AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL""",
            (rnd["round_id"],),
        ).fetchone()
        rounds.append({
            "round_id": rnd["round_id"],
            "name": rnd["name"],
            "round_order": rnd["round_order"],
            "goals": int(g["goals"] or 0),
            "matches": g["matches"],
        })
    return {
        "edition_id": edition_id,
        "season_label": e["season_label"],
        "competition_name": e["competition_name"],
        "lineage_name": e["lineage_name"],
        "total_goals": int(total["goals"] or 0),
        "matches": total["matches"],
        "rounds": rounds,
        "hat_trick_notes": hat_trick_notes(db, edition_id=edition_id),
    }


def season_goal_stats(db: CursorLike, season_label: str) -> list:
    """Goal totals for every edition in ``season_label`` (may be several lineages)."""
    editions = editions_for_season(db, season_label)
    if not editions:
        raise KeyError("unknown season %s" % season_label)
    return [edition_goal_stats(db, e["edition_id"]) for e in editions]


def club_campaign(db: CursorLike, club_id: int, season_label: str) -> list:
    """A club's ties in ``season_label``, ordered by competition then round.

    Includes walkovers (no legs). Scorelines are read only from stored match
    rows - a club that didn't play that season_label gets an empty list, not
    an error.
    """
    get_club(db, club_id)
    cur = _cursor(db)
    ties = cur.execute(
        """SELECT t.tie_id, t.club_a_id, t.club_b_id, t.winner_club_id,
                  t.decided_by, t.notes,
                  r.name AS round_name, r.round_order,
                  e.edition_id, e.season_label, e.competition_name,
                  l.name AS lineage_name
             FROM tie t
             JOIN round r ON r.round_id = t.round_id
             JOIN edition e ON e.edition_id = r.edition_id
             JOIN lineage l ON l.lineage_id = e.lineage_id
            WHERE e.season_label = ?
              AND (t.club_a_id = ? OR t.club_b_id = ?)
            ORDER BY e.competition_name, r.round_order, t.tie_id""",
        (season_label, club_id, club_id),
    ).fetchall()

    out = []
    for t in ties:
        opp_id = t["club_b_id"] if t["club_a_id"] == club_id else t["club_a_id"]
        legs = cur.execute(
            """SELECT leg_number, match_date, home_club_id, away_club_id,
                      home_score, away_score, after_extra_time, venue
                 FROM match WHERE tie_id = ? ORDER BY leg_number""",
            (t["tie_id"],),
        ).fetchall()
        out.append({
            "edition_id": t["edition_id"],
            "competition_name": t["competition_name"],
            "lineage_name": t["lineage_name"],
            "season_label": t["season_label"],
            "round_name": t["round_name"],
            "round_order": t["round_order"],
            "opponent_id": opp_id,
            "opponent": get_club_display_name(cur, opp_id, t["edition_id"]),
            "won": t["winner_club_id"] == club_id,
            "decided_by": t["decided_by"],
            "notes": t["notes"],
            "legs": [
                {
                    "leg_number": m["leg_number"],
                    "date": m["match_date"],
                    "home": get_club_display_name(cur, m["home_club_id"], t["edition_id"]),
                    "away": get_club_display_name(cur, m["away_club_id"], t["edition_id"]),
                    "home_score": m["home_score"],
                    "away_score": m["away_score"],
                    "after_extra_time": bool(m["after_extra_time"]),
                    "venue": m["venue"],
                }
                for m in legs
            ],
        })
    return out


def edition_chronology(db: CursorLike, season_label: str) -> list:
    """Matches in ``season_label`` with a stored date, oldest first.

    Undated matches are omitted rather than guessed; pair with
    ``editions_for_season`` if you also want a dated/total coverage count.
    """
    cur = _cursor(db)
    if not editions_for_season(db, season_label):
        raise KeyError("unknown season %s" % season_label)
    rows = cur.execute(
        _MATCH_SELECT + """
         WHERE e.season_label = ?
           AND m.match_date IS NOT NULL
         ORDER BY m.match_date, r.round_order, m.leg_number, m.match_id""",
        (season_label,),
    ).fetchall()
    return [{
        "match_id": m["match_id"],
        "date": m["match_date"],
        "competition_name": m["competition_name"],
        "lineage_name": m["lineage_name"],
        "round_name": m["round_name"],
        "leg_number": m["leg_number"],
        "home": get_club_display_name(cur, m["home_club_id"], m["edition_id"]),
        "away": get_club_display_name(cur, m["away_club_id"], m["edition_id"]),
        "home_score": m["home_score"],
        "away_score": m["away_score"],
        "after_extra_time": bool(m["after_extra_time"]),
        "venue": m["venue"],
    } for m in rows]


def winner_path_club_ids(db: CursorLike, edition_id: int) -> set:
    """Club IDs on the champion's route through ``edition_id``, champion included.

    Empty set when the edition has no recorded winner (e.g. not yet decided).
    """
    cur = _cursor(db)
    ed = cur.execute(
        "SELECT winner_club_id FROM edition WHERE edition_id = ?",
        (edition_id,),
    ).fetchone()
    if not ed or not ed["winner_club_id"]:
        return set()
    champ = ed["winner_club_id"]
    rows = cur.execute(
        """SELECT t.club_a_id, t.club_b_id
             FROM tie t
             JOIN round r ON r.round_id = t.round_id
            WHERE r.edition_id = ? AND t.winner_club_id = ?""",
        (edition_id, champ),
    ).fetchall()
    ids = {champ}
    for t in rows:
        ids.add(t["club_a_id"])
        ids.add(t["club_b_id"])
    return ids


def head_to_head(db: CursorLike, club_a_id: int, club_b_id: int) -> dict:
    """Head-to-head record for two clubs, derived from match and tie rows.

    Two-legged ties count as two matches; play-offs, replays and single-leg
    finals count as matches. Walkovers are labelled and are not scored 3-0
    unless a match row actually records that scoreline.
    """
    if club_a_id == club_b_id:
        raise ValueError("head-to-head requires two different clubs")
    cur = _cursor(db)
    a = get_club(db, club_a_id)
    b = get_club(db, club_b_id)
    matches = cur.execute(
        _MATCH_SELECT + """
         WHERE (m.home_club_id = ? AND m.away_club_id = ?)
            OR (m.home_club_id = ? AND m.away_club_id = ?)
         ORDER BY e.start_year, r.round_order, m.leg_number, m.match_id""",
        (club_a_id, club_b_id, club_b_id, club_a_id),
    ).fetchall()
    ties = cur.execute(
        """SELECT t.tie_id, t.club_a_id, t.club_b_id, t.winner_club_id,
                  t.decided_by, t.notes,
                  r.name AS round_name, e.edition_id, e.season_label,
                  e.competition_name, l.name AS lineage_name
             FROM tie t
             JOIN round r ON r.round_id = t.round_id
             JOIN edition e ON e.edition_id = r.edition_id
             JOIN lineage l ON l.lineage_id = e.lineage_id
            WHERE (t.club_a_id = ? AND t.club_b_id = ?)
               OR (t.club_a_id = ? AND t.club_b_id = ?)
            ORDER BY e.start_year, r.round_order, t.tie_id""",
        (club_a_id, club_b_id, club_b_id, club_a_id),
    ).fetchall()

    played = a_wins = b_wins = draws = a_gf = a_ga = 0
    by_lineage: dict[str, dict] = {}
    match_list = []
    for m in matches:
        contrib = _match_contribution(m, club_a_id)
        if contrib is None:
            continue
        gfor, gagt, result = contrib
        played += 1
        a_gf += gfor
        a_ga += gagt
        if result == "W":
            a_wins += 1
        elif result == "L":
            b_wins += 1
        else:
            draws += 1
        lin = m["lineage_name"]
        bucket = by_lineage.setdefault(lin, {
            "lineage_name": lin,
            "matches_played": 0,
            "matches": 0,
            "wins_a": 0,
            "wins_b": 0,
            "club_a_wins": 0,
            "club_b_wins": 0,
            "draws": 0,
            "goals_a": 0,
            "goals_b": 0,
            "club_a_goals": 0,
            "club_b_goals": 0,
        })
        bucket["matches_played"] += 1
        bucket["matches"] += 1
        bucket["goals_a"] += gfor
        bucket["goals_b"] += gagt
        bucket["club_a_goals"] += gfor
        bucket["club_b_goals"] += gagt
        if result == "W":
            bucket["wins_a"] += 1
            bucket["club_a_wins"] += 1
        elif result == "L":
            bucket["wins_b"] += 1
            bucket["club_b_wins"] += 1
        else:
            bucket["draws"] += 1
        match_list.append({
            "match_id": m["match_id"],
            "match_date": m["match_date"],
            "date": m["match_date"],
            "season_label": m["season_label"],
            "competition_name": m["competition_name"],
            "lineage_name": lin,
            "round_name": m["round_name"],
            "leg_number": m["leg_number"],
            "home_club_id": m["home_club_id"],
            "away_club_id": m["away_club_id"],
            "home_name": get_club_display_name(cur, m["home_club_id"], m["edition_id"]),
            "away_name": get_club_display_name(cur, m["away_club_id"], m["edition_id"]),
            "home_score": m["home_score"],
            "away_score": m["away_score"],
            "after_extra_time": bool(m["after_extra_time"]),
            "venue": m["venue"],
            "decided_by": m["decided_by"],
            "walkover": False,
        })

    walkovers = []
    for t in ties:
        if t["decided_by"] not in ("walkover", "bye"):
            continue
        winner_name = (
            get_club_display_name(cur, t["winner_club_id"], t["edition_id"])
            if t["winner_club_id"] else None
        )
        walkovers.append({
            "tie_id": t["tie_id"],
            "season_label": t["season_label"],
            "competition_name": t["competition_name"],
            "lineage_name": t["lineage_name"],
            "round_name": t["round_name"],
            "decided_by": t["decided_by"],
            "notes": t["notes"],
            "club_a_name": get_club_display_name(cur, t["club_a_id"], t["edition_id"]),
            "club_b_name": get_club_display_name(cur, t["club_b_id"], t["edition_id"]),
            "winner_club_id": t["winner_club_id"],
            "winner_name": winner_name,
        })

    competitions = sorted(by_lineage.values(), key=lambda d: d["lineage_name"])
    return {
        "club_a": {"club_id": club_a_id, "name": a["name"]},
        "club_b": {"club_id": club_b_id, "name": b["name"]},
        "club_a_id": club_a_id,
        "club_b_id": club_b_id,
        "club_a_name": a["name"],
        "club_b_name": b["name"],
        "matches_played": played,
        "ties_contested": len(ties),
        "wins_a": a_wins,
        "wins_b": b_wins,
        "club_a_wins": a_wins,
        "club_b_wins": b_wins,
        "draws": draws,
        "goals_a": a_gf,
        "goals_b": a_ga,
        "club_a_goals": a_gf,
        "club_b_goals": a_ga,
        "walkovers": walkovers,
        "by_competition": competitions,
        "competitions": competitions,
        "matches": match_list,
    }


def h2h_is_complement(left: dict, right: dict) -> bool:
    """True when ``right`` is the side-swapped complement of ``left``."""
    return (
        left["club_a_id"] == right["club_b_id"]
        and left["club_b_id"] == right["club_a_id"]
        and left["matches_played"] == right["matches_played"]
        and left["ties_contested"] == right["ties_contested"]
        and left["draws"] == right["draws"]
        and left["wins_a"] == right["wins_b"]
        and left["wins_b"] == right["wins_a"]
        and left["goals_a"] == right["goals_b"]
        and left["goals_b"] == right["goals_a"]
        and len(left["walkovers"]) == len(right["walkovers"])
        and len(left["matches"]) == len(right["matches"])
    )


def _match_records_by_club(db: CursorLike) -> dict:
    """Match records for every club that has at least one scored match."""
    cur = _cursor(db)
    rows = cur.execute(
        _MATCH_SELECT + " WHERE m.home_score IS NOT NULL AND m.away_score IS NOT NULL"
    ).fetchall()
    recs: dict[int, dict] = {}
    for m in rows:
        for cid in (m["home_club_id"], m["away_club_id"]):
            contrib = _match_contribution(m, cid)
            if contrib is None:
                continue
            gfor, gagt, result = contrib
            rec = recs.setdefault(cid, _empty_record(cid))
            rec["matches_played"] += 1
            rec["goals_for"] += gfor
            rec["goals_against"] += gagt
            if result == "W":
                rec["wins"] += 1
            elif result == "L":
                rec["losses"] += 1
            else:
                rec["draws"] += 1
    for rec in recs.values():
        _finalise_record(rec)
    return recs


def _attach_club_names(db: CursorLike, rows: list) -> list:
    cur = _cursor(db)
    for rec in rows:
        club = get_club(cur, rec["club_id"])
        rec["name"] = club["name"]
        rec["country"] = club["country"]
    return rows


def leaderboard_titles(db: CursorLike, limit: Optional[int] = None) -> list:
    """Titles won from ``edition.winner_club_id``. Sort: see LEADERBOARD_SORT['titles']."""
    cur = _cursor(db)
    rows = cur.execute(
        """SELECT winner_club_id AS club_id, COUNT(*) AS titles
             FROM edition
            WHERE winner_club_id IS NOT NULL
            GROUP BY winner_club_id"""
    ).fetchall()
    out = []
    for r in rows:
        club = get_club(cur, r["club_id"])
        out.append({
            "club_id": r["club_id"],
            "name": club["name"],
            "country": club["country"],
            "titles": r["titles"],
        })
    out.sort(key=lambda d: (-d["titles"], d["name"].lower()))
    return _with_rank(_apply_limit(out, limit))


def leaderboard_matches(db: CursorLike, limit: Optional[int] = None) -> list:
    """Match records. Sort: see LEADERBOARD_SORT['matches']."""
    out = _attach_club_names(db, list(_match_records_by_club(db).values()))
    out.sort(key=lambda d: (
        -d["matches_played"], -d["wins"], -d["goal_difference"], d["name"].lower()
    ))
    return _with_rank(_apply_limit(out, limit))


def leaderboard_wins(db: CursorLike, limit: Optional[int] = None) -> list:
    """Wins. Sort: see LEADERBOARD_SORT['wins']."""
    out = _attach_club_names(db, list(_match_records_by_club(db).values()))
    out.sort(key=lambda d: (
        -d["wins"], -d["matches_played"], -d["goal_difference"], d["name"].lower()
    ))
    return _with_rank(_apply_limit(out, limit))


def leaderboard_goal_difference(db: CursorLike, limit: Optional[int] = None) -> list:
    """Goal difference. Sort: see LEADERBOARD_SORT['gd']."""
    out = _attach_club_names(db, list(_match_records_by_club(db).values()))
    out.sort(key=lambda d: (
        -d["goal_difference"], -d["matches_played"], -d["wins"], d["name"].lower()
    ))
    return _with_rank(_apply_limit(out, limit))


def leaderboard_finals(db: CursorLike, limit: Optional[int] = None) -> list:
    """Finals reached = edition champion + runner-up. Sort: LEADERBOARD_SORT['finals']."""
    cur = _cursor(db)
    rows = cur.execute(
        """SELECT club_id,
                  SUM(CASE WHEN role = 'champion' THEN 1 ELSE 0 END) AS titles,
                  SUM(CASE WHEN role = 'runner_up' THEN 1 ELSE 0 END) AS runner_up,
                  COUNT(*) AS finals_reached
             FROM (
                 SELECT winner_club_id AS club_id, 'champion' AS role
                   FROM edition WHERE winner_club_id IS NOT NULL
                 UNION ALL
                 SELECT runner_up_club_id, 'runner_up'
                   FROM edition WHERE runner_up_club_id IS NOT NULL
             ) x
            GROUP BY club_id"""
    ).fetchall()
    out = []
    for r in rows:
        club = get_club(cur, r["club_id"])
        runner = r["runner_up"]
        out.append({
            "club_id": r["club_id"],
            "name": club["name"],
            "country": club["country"],
            "titles": r["titles"],
            "runner_up": runner,
            "runner_up_finishes": runner,
            "finals_reached": r["finals_reached"],
        })
    out.sort(key=lambda d: (-d["finals_reached"], -d["titles"], d["name"].lower()))
    return _with_rank(_apply_limit(out, limit))


_LEADERBOARD_FUNCS = {
    "titles": leaderboard_titles,
    "matches": leaderboard_matches,
    "wins": leaderboard_wins,
    "gd": leaderboard_goal_difference,
    "finals": leaderboard_finals,
}


def leaderboard(db: CursorLike, kind: str, limit: Optional[int] = None) -> list:
    """Dispatch an all-time leaderboard. ``kind`` is one of LEADERBOARD_KINDS."""
    func = _LEADERBOARD_FUNCS.get(kind)
    if func is None:
        raise ValueError("unknown leaderboard %r; choose from %s" % (
            kind, ", ".join(LEADERBOARD_KINDS)))
    return func(db, limit=limit)


def edition_results(
    db: CursorLike,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    lineage_name: Optional[str] = None,
) -> list:
    """Edition champions and runners-up (optional year / lineage filter)."""
    cur = _cursor(db)
    sql = """
        SELECT e.edition_id, e.season_label, e.start_year, e.competition_name,
               l.name AS lineage_name,
               e.winner_club_id, e.runner_up_club_id,
               w.name AS winner_name, r.name AS runner_up_name
          FROM edition e
          JOIN lineage l ON l.lineage_id = e.lineage_id
          LEFT JOIN club w ON w.club_id = e.winner_club_id
          LEFT JOIN club r ON r.club_id = e.runner_up_club_id
         WHERE 1 = 1
    """
    params: list[Any] = []
    if start_year is not None:
        sql += " AND e.start_year >= ?"
        params.append(start_year)
    if end_year is not None:
        sql += " AND e.start_year <= ?"
        params.append(end_year)
    if lineage_name is not None:
        sql += " AND l.name = ?"
        params.append(lineage_name)
    sql += " ORDER BY e.start_year, e.competition_name"
    out = []
    for row in cur.execute(sql, params):
        out.append({
            "edition_id": row["edition_id"],
            "season_label": row["season_label"],
            "start_year": row["start_year"],
            "competition_name": row["competition_name"],
            "lineage_name": row["lineage_name"],
            "winner_club_id": row["winner_club_id"],
            "runner_up_club_id": row["runner_up_club_id"],
            "winner_name": row["winner_name"],
            "runner_up_name": row["runner_up_name"],
        })
    return out


def classic_era_title_holders(db: CursorLike) -> list:
    """European Cup champions, 1955-56 through 1959-60 (Classic Era five-in-a-row)."""
    return edition_results(
        db, start_year=1955, end_year=1959, lineage_name="European Cup",
    )
