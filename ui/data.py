# -*- coding: utf-8 -*-
"""Prefetch helpers, display-name cache, club profile, and bracket model.

All functions are display-free (no CustomTkinter) so tests can exercise them.
Period-accurate names mirror queries.get_club_display_name but are batched
(two history lookups for the whole registry, never N+1 per club).
"""

from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Mapping, Optional, Union

from ui.formatters import (
    _field,
    aggregate_from_matches,
    format_score_header,
)

CursorLike = Union[sqlite3.Cursor, sqlite3.Connection]


def _cursor(db: CursorLike) -> sqlite3.Cursor:
    if isinstance(db, sqlite3.Connection):
        return db.cursor()
    return db


def row_as_dict(row: Any) -> Optional[dict]:
    """Normalise sqlite3.Row / mapping / sequence-unfriendly objects to a dict."""
    if row is None:
        return None
    if isinstance(row, dict):
        return dict(row)
    keys = getattr(row, "keys", None)
    if callable(keys):
        return {k: row[k] for k in keys()}
    return None


def load_club_cache(db: CursorLike, edition_id: Optional[int] = None,
                    season_label: Optional[str] = None) -> dict:
    """Load {club_id: {name, country, city, notes, display_name}} for an edition.

    Display names follow queries.get_club_display_name: exact edition_id on
    club_name_history first, then a season_label match, then club.name.
    """
    cur = _cursor(db)
    clubs: dict[int, dict] = {}
    for row in cur.execute(
            "SELECT club_id, name, country, city, notes FROM club"):
        d = row_as_dict(row) or {}
        cid = int(d["club_id"])
        d["club_id"] = cid
        d["display_name"] = d.get("name") or "?"
        clubs[cid] = d

    if edition_id is None and not season_label:
        return clubs

    labelled = season_label
    if edition_id is not None and labelled is None:
        ed = cur.execute(
            "SELECT season_label FROM edition WHERE edition_id=?",
            (edition_id,),
        ).fetchone()
        if ed is not None:
            labelled = ed[0] if not isinstance(ed, sqlite3.Row) else ed["season_label"]

    claimed: set[int] = set()
    if edition_id is not None:
        for row in cur.execute(
                "SELECT club_id, name_used FROM club_name_history "
                "WHERE edition_id=?",
                (edition_id,)):
            d = row_as_dict(row) or {}
            cid = int(d["club_id"])
            if cid in clubs:
                clubs[cid]["display_name"] = d["name_used"]
                claimed.add(cid)

    if labelled:
        for row in cur.execute(
                "SELECT club_id, name_used, edition_id FROM club_name_history "
                "WHERE season_label=?",
                (labelled,)):
            d = row_as_dict(row) or {}
            cid = int(d["club_id"])
            if cid not in clubs or cid in claimed:
                continue
            hist_eid = d.get("edition_id")
            if hist_eid is not None and edition_id is not None and int(hist_eid) != int(edition_id):
                continue
            clubs[cid]["display_name"] = d["name_used"]
    return clubs


def fetch_edition_payload(db: CursorLike, edition_id: int) -> dict:
    """Prefetch one edition: rounds, ties, matches, clubs, season totals.

    Rendering then aggregates in Python and never issues per-tie SELECTs.
    """
    cur = _cursor(db)
    ed = row_as_dict(cur.execute(
        "SELECT * FROM edition WHERE edition_id=?", (edition_id,)
    ).fetchone())
    if ed is None:
        raise KeyError("unknown edition_id %s" % edition_id)

    rounds = [row_as_dict(r) for r in cur.execute(
        "SELECT * FROM round WHERE edition_id=? ORDER BY round_order",
        (edition_id,),
    )]
    round_ids = [r["round_id"] for r in rounds]

    ties: list[dict] = []
    if round_ids:
        placeholders = ",".join("?" * len(round_ids))
        ties = [row_as_dict(t) for t in cur.execute(
            "SELECT * FROM tie WHERE round_id IN (%s) ORDER BY tie_id" % placeholders,
            round_ids,
        )]

    tie_ids = [t["tie_id"] for t in ties]
    matches: list[dict] = []
    if tie_ids:
        placeholders = ",".join("?" * len(tie_ids))
        matches = [row_as_dict(m) for m in cur.execute(
            "SELECT * FROM match WHERE tie_id IN (%s) "
            "ORDER BY tie_id, leg_number" % placeholders,
            tie_ids,
        )]

    matches_by_tie: dict[int, list] = {}
    for m in matches:
        matches_by_tie.setdefault(m["tie_id"], []).append(m)

    ties_by_round: dict[int, list] = {}
    for t in ties:
        legs = matches_by_tie.get(t["tie_id"], [])
        t["matches"] = legs
        t["aggregate"] = aggregate_from_matches(t, legs)
        ties_by_round.setdefault(t["round_id"], []).append(t)

    for rnd in rounds:
        rnd["ties"] = ties_by_round.get(rnd["round_id"], [])

    clubs = load_club_cache(
        cur, edition_id=edition_id, season_label=ed.get("season_label"))

    match_count = len(matches)
    goal_count = 0
    for m in matches:
        hs = m.get("home_score")
        aws = m.get("away_score")
        if hs is not None:
            goal_count += int(hs)
        if aws is not None:
            goal_count += int(aws)

    return {
        "edition": ed,
        "rounds": rounds,
        "ties": ties,
        "matches": matches,
        "clubs": clubs,
        "match_count": match_count,
        "goal_count": goal_count,
    }


def final_score_text(payload: Mapping) -> str:
    """Scoreline of the Final (highest round_order), or empty string."""
    rounds = list(payload.get("rounds") or [])
    if not rounds:
        return ""
    last = max(rounds, key=lambda r: r.get("round_order") or 0)
    ties = last.get("ties") or []
    if not ties:
        return ""
    tie = ties[0]
    ga, gb = tie.get("aggregate") or (0, 0)
    return format_score_header(ga, gb, tie.get("decided_by"), tie.get("matches") or [])


def tie_matches_query(tie: Mapping, clubs: Mapping, query: str) -> bool:
    """True when the in-memory tie matches a club/notes search string."""
    if not query or not str(query).strip():
        return True
    needle = str(query).casefold()
    bits = [tie.get("notes") or ""]
    for cid in (tie.get("club_a_id"), tie.get("club_b_id")):
        info = clubs.get(cid) or {}
        bits.append(info.get("display_name") or "")
        bits.append(info.get("name") or "")
        bits.append(info.get("country") or "")
    return needle in " ".join(bits).casefold()


def map_feeders(prev_ties: Iterable[Mapping], curr_ties: Iterable[Mapping]):
    """Map each current tie to previous-round ties whose winners feed it.

    Returns (mapped, leftovers) where mapped is a list of
    {tie, feeder_a, feeder_b} and leftovers are previous ties whose winner
    did not appear in the next round (walkovers that go nowhere, data gaps).
    """
    by_winner: dict[int, list] = {}
    for t in prev_ties:
        w = t.get("winner_club_id")
        if w is not None:
            by_winner.setdefault(int(w), []).append(t)

    used: set = set()
    mapped = []
    for t in curr_ties:
        fa = _take_feeder(by_winner, t.get("club_a_id"), used)
        fb = _take_feeder(by_winner, t.get("club_b_id"), used)
        mapped.append({"tie": t, "feeder_a": fa, "feeder_b": fb})

    leftovers = [t for t in prev_ties if t.get("tie_id") not in used]
    return mapped, leftovers


def _take_feeder(by_winner: dict, club_id, used: set):
    if club_id is None:
        return None
    bucket = by_winner.get(int(club_id)) or []
    while bucket:
        cand = bucket.pop(0)
        tid = cand.get("tie_id")
        if tid in used:
            continue
        used.add(tid)
        return cand
    return None


def organise_bracket_columns(rounds: Iterable[Mapping]) -> list:
    """Build left-to-right columns keyed by round_order, never by round name.

    Names vary (Preliminary / Qualifying / First Round); round_order is stable.
    Each slot records feeder slot indices in the previous column, or None for
    a bye / missing feeder. 4-round and 5-round seasons both produce one
    column per round; leftover unadvanced ties stay visible in their column.
    """
    ordered = sorted(rounds, key=lambda r: r.get("round_order") or 0)
    columns = []
    prev_slots: list[dict] = []
    prev_ties: list = []
    for i, rnd in enumerate(ordered):
        ties = list(rnd.get("ties") or [])
        slots: list[dict] = []
        if i == 0:
            for t in ties:
                slots.append({"kind": "tie", "tie": t, "feeders": []})
        else:
            mapped, _leftovers = map_feeders(prev_ties, ties)
            index_of = {}
            for idx, slot in enumerate(prev_slots):
                tie = slot.get("tie")
                if tie is not None:
                    index_of[tie["tie_id"]] = idx
            for item in mapped:
                feeders = []
                for key in ("feeder_a", "feeder_b"):
                    ft = item[key]
                    if ft is not None:
                        feeders.append(index_of.get(ft["tie_id"]))
                    else:
                        feeders.append(None)
                slots.append({
                    "kind": "tie",
                    "tie": item["tie"],
                    "feeders": feeders,
                })
        columns.append({
            "round_order": rnd.get("round_order"),
            "name": rnd.get("name") or "",
            "slots": slots,
        })
        prev_slots = slots
        prev_ties = ties
    return columns


def layout_bracket_positions(columns: list, slot_h: int = 72, top: int = 24) -> list:
    """Assign y coordinates so a node sits on the midpoint of its feeders."""
    ys_all = []
    for ci, col in enumerate(columns):
        col_ys = []
        for si, slot in enumerate(col.get("slots") or []):
            feeders = slot.get("feeders") or []
            feeder_ys = []
            if ci > 0 and feeders:
                prev = ys_all[ci - 1]
                for fi in feeders:
                    if fi is not None and 0 <= fi < len(prev):
                        feeder_ys.append(prev[fi])
            if feeder_ys:
                y = int(sum(feeder_ys) / len(feeder_ys))
            else:
                y = top + si * slot_h
            if col_ys and y < col_ys[-1] + slot_h:
                y = col_ys[-1] + slot_h
            col_ys.append(y)
        ys_all.append(col_ys)
    return ys_all


def fetch_club_profile(db: CursorLike, club_id: int) -> dict:
    """Batch-load a club profile: aliases, record, titles, match history.

    Four statements total (club row, history, tie record + titles, matches).
    No per-match follow-up queries.
    """
    cur = _cursor(db)
    club = row_as_dict(cur.execute(
        "SELECT * FROM club WHERE club_id=?", (club_id,)
    ).fetchone())
    if club is None:
        raise KeyError("unknown club_id %s" % club_id)

    aliases = [row_as_dict(r) for r in cur.execute(
        "SELECT name_used, season_label, edition_id, notes "
        "FROM club_name_history WHERE club_id=? "
        "ORDER BY season_label, edition_id",
        (club_id,),
    )]

    rec = row_as_dict(cur.execute(
        """
        SELECT
          (SELECT COUNT(*) FROM tie
             WHERE club_a_id = :id OR club_b_id = :id) AS ties_played,
          (SELECT COUNT(*) FROM tie
             WHERE winner_club_id = :id) AS wins,
          (SELECT COUNT(*) FROM tie
             WHERE (club_a_id = :id OR club_b_id = :id)
               AND winner_club_id IS NOT NULL
               AND winner_club_id != :id) AS losses,
          (SELECT COUNT(*) FROM edition WHERE winner_club_id = :id) AS titles,
          (SELECT COUNT(*) FROM edition
             WHERE runner_up_club_id = :id) AS runner_up_finishes
        """,
        {"id": club_id},
    ).fetchone()) or {}

    matches = [row_as_dict(m) for m in cur.execute(
        """
        SELECT m.*,
               t.decided_by,
               t.winner_club_id AS tie_winner_club_id,
               r.name AS round_name,
               r.round_order,
               e.edition_id,
               e.season_label,
               e.competition_name,
               e.start_year,
               hc.name AS home_canonical,
               ac.name AS away_canonical
        FROM match m
        JOIN tie t ON t.tie_id = m.tie_id
        JOIN round r ON r.round_id = t.round_id
        JOIN edition e ON e.edition_id = r.edition_id
        JOIN club hc ON hc.club_id = m.home_club_id
        JOIN club ac ON ac.club_id = m.away_club_id
        WHERE m.home_club_id = ? OR m.away_club_id = ?
        ORDER BY e.start_year, r.round_order, m.leg_number, m.match_id
        """,
        (club_id, club_id),
    )]

    history_rows = [row_as_dict(r) for r in cur.execute(
        "SELECT club_id, edition_id, season_label, name_used FROM club_name_history"
    )]
    display_by_edition: dict[tuple, str] = {}
    display_by_season: dict[tuple, str] = {}
    for h in history_rows:
        if h.get("edition_id") is not None:
            display_by_edition[(h["club_id"], h["edition_id"])] = h["name_used"]
        if h.get("season_label"):
            display_by_season[(h["club_id"], h["season_label"])] = h["name_used"]

    for m in matches:
        eid = m.get("edition_id")
        sl = m.get("season_label")
        for side, cid_key, canon_key, out_key in (
            ("home", "home_club_id", "home_canonical", "home_display"),
            ("away", "away_club_id", "away_canonical", "away_display"),
        ):
            cid = m.get(cid_key)
            name = m.get(canon_key) or "?"
            if eid is not None and (cid, eid) in display_by_edition:
                name = display_by_edition[(cid, eid)]
            elif sl and (cid, sl) in display_by_season:
                name = display_by_season[(cid, sl)]
            m[out_key] = name

    return {
        "club": club,
        "aliases": aliases,
        "ties_played": rec.get("ties_played") or 0,
        "wins": rec.get("wins") or 0,
        "losses": rec.get("losses") or 0,
        "titles": rec.get("titles") or 0,
        "runner_up_finishes": rec.get("runner_up_finishes") or 0,
        "matches": matches,
    }
