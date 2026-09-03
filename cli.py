#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli.py - query and export helpers for the European Football Database.

Examples:
  python cli.py club real_madrid
  python cli.py h2h benfica barcelona
  python cli.py season 1960-61
  python cli.py export 1960-61 --format json
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

from clubs import CLUBS
from queries import connect, get_club_display_name

HERE = os.path.dirname(os.path.abspath(__file__))

# Windows consoles are often cp1252; keep UTF-8 club names printable.
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

DB_PATH = os.path.join(HERE, "european_football.db")


def _require_db():
    if not os.path.exists(DB_PATH):
        sys.exit("Database missing. Run: python build_database.py --force")
    return connect(DB_PATH)


def _resolve_club_key(key: str) -> str:
    if key in CLUBS:
        return key
    lowered = key.lower().replace(" ", "_").replace("-", "_")
    if lowered in CLUBS:
        return lowered
    # fuzzy: match against canonical name
    needle = key.lower()
    hits = [k for k, c in CLUBS.items() if needle in c["name"].lower() or needle == k]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit("Unknown club key/name: %s" % key)
    sys.exit("Ambiguous club %r; matches: %s" % (key, ", ".join(hits)))


def _club_id(cur, key: str) -> int:
    name = CLUBS[key]["name"]
    row = cur.execute("SELECT club_id FROM club WHERE name = ?", (name,)).fetchone()
    if not row:
        sys.exit("Club %s (%s) is not in the built database." % (key, name))
    return row["club_id"]


def cmd_club(args):
    key = _resolve_club_key(args.club_key)
    conn = _require_db()
    cur = conn.cursor()
    cid = _club_id(cur, key)
    meta = CLUBS[key]
    print("%s (%s, %s) [%s]" % (meta["name"], meta.get("country") or "?", meta.get("city") or "?", key))

    matches = cur.execute(
        """SELECT m.home_club_id, m.away_club_id, m.home_score, m.away_score,
                  e.winner_club_id AS edition_winner, e.runner_up_club_id,
                  e.season_label, e.competition_name
           FROM match m
           JOIN tie t ON t.tie_id = m.tie_id
           JOIN round r ON r.round_id = t.round_id
           JOIN edition e ON e.edition_id = r.edition_id
           WHERE m.home_club_id = ? OR m.away_club_id = ?""",
        (cid, cid),
    ).fetchall()

    played = wins = draws = losses = gf = ga = 0
    finals_won = finals_lost = 0
    for m in matches:
        if m["home_score"] is None or m["away_score"] is None:
            continue
        played += 1
        if m["home_club_id"] == cid:
            gf += m["home_score"]; ga += m["away_score"]
            ours, theirs = m["home_score"], m["away_score"]
        else:
            gf += m["away_score"]; ga += m["home_score"]
            ours, theirs = m["away_score"], m["home_score"]
        if ours > theirs:
            wins += 1
        elif ours < theirs:
            losses += 1
        else:
            draws += 1

    editions = cur.execute(
        """SELECT season_label, competition_name, winner_club_id, runner_up_club_id
           FROM edition
           WHERE winner_club_id = ? OR runner_up_club_id = ?
           ORDER BY start_year""",
        (cid, cid),
    ).fetchall()
    for e in editions:
        if e["winner_club_id"] == cid:
            finals_won += 1
        elif e["runner_up_club_id"] == cid:
            finals_lost += 1

    print("  Matches: %d  W-D-L: %d-%d-%d  Goals: %d-%d" % (played, wins, draws, losses, gf, ga))
    print("  Finals won: %d  Finals lost (runner-up): %d" % (finals_won, finals_lost))
    if editions:
        print("  Trophy finishes:")
        for e in editions:
            role = "Champion" if e["winner_club_id"] == cid else "Runner-up"
            print("    - %s %s (%s)" % (e["competition_name"], e["season_label"], role))

    # Period names
    hist = cur.execute(
        """SELECT season_label, name_used FROM club_name_history
           WHERE club_id = ? ORDER BY season_label""",
        (cid,),
    ).fetchall()
    if hist:
        print("  Period names:")
        for h in hist:
            print("    - %s: %s" % (h["season_label"], h["name_used"]))
    conn.close()


def cmd_h2h(args):
    k1 = _resolve_club_key(args.club_1)
    k2 = _resolve_club_key(args.club_2)
    conn = _require_db()
    cur = conn.cursor()
    c1 = _club_id(cur, k1)
    c2 = _club_id(cur, k2)
    rows = cur.execute(
        """SELECT m.match_date, m.home_club_id, m.away_club_id, m.home_score, m.away_score,
                  m.venue, e.season_label, e.competition_name, r.name AS round_name,
                  e.edition_id
           FROM match m
           JOIN tie t ON t.tie_id = m.tie_id
           JOIN round r ON r.round_id = t.round_id
           JOIN edition e ON e.edition_id = r.edition_id
           WHERE (m.home_club_id = ? AND m.away_club_id = ?)
              OR (m.home_club_id = ? AND m.away_club_id = ?)
           ORDER BY e.start_year, r.round_order, m.leg_number""",
        (c1, c2, c2, c1),
    ).fetchall()
    print("Head-to-head: %s vs %s (%d match(es))" % (CLUBS[k1]["name"], CLUBS[k2]["name"], len(rows)))
    for m in rows:
        home = get_club_display_name(cur, m["home_club_id"], m["edition_id"])
        away = get_club_display_name(cur, m["away_club_id"], m["edition_id"])
        score = "%s-%s" % (m["home_score"], m["away_score"]) if m["home_score"] is not None else "?-?"
        when = m["match_date"] or m["season_label"]
        loc = (" @ " + m["venue"]) if m["venue"] else ""
        print("  %s | %s %s | %s %s %s%s" % (
            when, m["competition_name"], m["round_name"], home, score, away, loc))
    conn.close()


def cmd_season(args):
    conn = _require_db()
    cur = conn.cursor()
    editions = cur.execute(
        """SELECT edition_id, season_label, competition_name, start_year,
                  winner_club_id, runner_up_club_id, notes
           FROM edition WHERE season_label = ? ORDER BY competition_name""",
        (args.season_label,),
    ).fetchall()
    if not editions:
        sys.exit("No edition found for season %s" % args.season_label)
    for e in editions:
        print("=" * 60)
        print("%s %s" % (e["competition_name"], e["season_label"]))
        if e["winner_club_id"]:
            w = get_club_display_name(cur, e["winner_club_id"], e["edition_id"])
            r = (get_club_display_name(cur, e["runner_up_club_id"], e["edition_id"])
                 if e["runner_up_club_id"] else None)
            print("  Champion: %s%s" % (w, ("    Runner-up: " + r) if r else ""))
        if e["notes"]:
            print("  Note: %s" % e["notes"])
        rounds = cur.execute(
            """SELECT round_id, name, round_order FROM round
               WHERE edition_id = ? ORDER BY round_order""",
            (e["edition_id"],),
        ).fetchall()
        for rnd in rounds:
            print("\n  %s" % rnd["name"])
            ties = cur.execute(
                """SELECT * FROM tie WHERE round_id = ? ORDER BY tie_id""",
                (rnd["round_id"],),
            ).fetchall()
            for tie in ties:
                a = get_club_display_name(cur, tie["club_a_id"], e["edition_id"])
                b = get_club_display_name(cur, tie["club_b_id"], e["edition_id"])
                win = (get_club_display_name(cur, tie["winner_club_id"], e["edition_id"])
                       if tie["winner_club_id"] else "—")
                print("    %s vs %s  [%s] -> %s" % (a, b, tie["decided_by"] or "?", win))
                for m in cur.execute(
                    """SELECT * FROM match WHERE tie_id = ? ORDER BY leg_number""",
                    (tie["tie_id"],),
                ):
                    hn = get_club_display_name(cur, m["home_club_id"], e["edition_id"])
                    an = get_club_display_name(cur, m["away_club_id"], e["edition_id"])
                    print("      L%d: %s %s-%s %s" % (
                        m["leg_number"], hn, m["home_score"], m["away_score"], an))
    conn.close()


def _export_edition(cur, edition_id):
    e = cur.execute("SELECT * FROM edition WHERE edition_id = ?", (edition_id,)).fetchone()
    payload = {
        "season_label": e["season_label"],
        "competition_name": e["competition_name"],
        "start_year": e["start_year"],
        "away_goals_active": bool(e["away_goals_active"]),
        "notes": e["notes"],
        "winner": get_club_display_name(cur, e["winner_club_id"], edition_id) if e["winner_club_id"] else None,
        "runner_up": get_club_display_name(cur, e["runner_up_club_id"], edition_id) if e["runner_up_club_id"] else None,
        "rounds": [],
    }
    for rnd in cur.execute(
        "SELECT * FROM round WHERE edition_id = ? ORDER BY round_order", (edition_id,)
    ):
        rnd_obj = {"name": rnd["name"], "ties": []}
        for tie in cur.execute(
            "SELECT * FROM tie WHERE round_id = ? ORDER BY tie_id", (rnd["round_id"],)
        ):
            tie_obj = {
                "club_a": get_club_display_name(cur, tie["club_a_id"], edition_id),
                "club_b": get_club_display_name(cur, tie["club_b_id"], edition_id),
                "winner": (get_club_display_name(cur, tie["winner_club_id"], edition_id)
                           if tie["winner_club_id"] else None),
                "decided_by": tie["decided_by"],
                "notes": tie["notes"],
                "legs": [],
            }
            for m in cur.execute(
                "SELECT * FROM match WHERE tie_id = ? ORDER BY leg_number", (tie["tie_id"],)
            ):
                tie_obj["legs"].append({
                    "leg_number": m["leg_number"],
                    "date": m["match_date"],
                    "home": get_club_display_name(cur, m["home_club_id"], edition_id),
                    "away": get_club_display_name(cur, m["away_club_id"], edition_id),
                    "home_score": m["home_score"],
                    "away_score": m["away_score"],
                    "home_pens": m["home_pens"],
                    "away_pens": m["away_pens"],
                    "after_extra_time": bool(m["after_extra_time"]),
                    "venue": m["venue"],
                    "attendance": m["attendance"],
                    "referee": m["referee"],
                })
            rnd_obj["ties"].append(tie_obj)
        payload["rounds"].append(rnd_obj)
    return payload


def cmd_export(args):
    if args.format != "json":
        sys.exit("Only --format json is supported currently.")
    conn = _require_db()
    cur = conn.cursor()
    editions = cur.execute(
        "SELECT edition_id FROM edition WHERE season_label = ? ORDER BY competition_name",
        (args.season_label,),
    ).fetchall()
    if not editions:
        sys.exit("No edition found for season %s" % args.season_label)
    out = [_export_edition(cur, e["edition_id"]) for e in editions]
    print(json.dumps(out if len(out) > 1 else out[0], ensure_ascii=False, indent=2))
    conn.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="European Football Database CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_club = sub.add_parser("club", help="All-time European record for a club")
    p_club.add_argument("club_key")
    p_club.set_defaults(func=cmd_club)

    p_h2h = sub.add_parser("h2h", help="Head-to-head match history")
    p_h2h.add_argument("club_1")
    p_h2h.add_argument("club_2")
    p_h2h.set_defaults(func=cmd_h2h)

    p_season = sub.add_parser("season", help="Season round-by-round breakdown")
    p_season.add_argument("season_label")
    p_season.set_defaults(func=cmd_season)

    p_export = sub.add_parser("export", help="Export a season as JSON")
    p_export.add_argument("season_label")
    p_export.add_argument("--format", default="json")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
