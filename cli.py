#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli.py - query and export helpers for the European Football Database.

Examples:
  python cli.py club real_madrid
  python cli.py h2h benfica barcelona
  python cli.py goals real_madrid
  python cli.py goals --season 1959-60
  python cli.py leaderboard titles
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
from queries import (
    LEADERBOARD_KINDS,
    LEADERBOARD_SORT,
    club_record,
    connect,
    get_club_display_name,
    head_to_head,
    leaderboard,
    season_goal_stats,
)

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


def _wdl(wins, draws, losses):
    return "%d-%d-%d" % (wins, draws, losses)


def cmd_club(args):
    key = _resolve_club_key(args.club_key)
    conn = _require_db()
    cur = conn.cursor()
    cid = _club_id(cur, key)
    meta = CLUBS[key]
    rec = club_record(cur, cid)
    print("%s (%s, %s) [%s]" % (meta["name"], meta.get("country") or "?", meta.get("city") or "?", key))
    print("  Matches: %d  W-D-L: %s  Goals: %d-%d  GD: %+d" % (
        rec["matches_played"], _wdl(rec["wins"], rec["draws"], rec["losses"]),
        rec["goals_for"], rec["goals_against"], rec["goal_difference"]))
    print("  Average goals scored per match: %s" % rec["average_goals_per_match"])
    print("  Finals won: %d  Runner-up finishes: %d  Finals reached: %d" % (
        rec["titles"], rec["runner_up_finishes"], rec["finals_reached"]))
    print("  Finals goals: %d-%d (%d match(es))" % (
        rec["finals_goals_for"], rec["finals_goals_against"], rec["finals_matches"]))
    if rec["highest_scoring_ties"]:
        print("  Highest-scoring ties:")
        for tie in rec["highest_scoring_ties"]:
            print("    - %s %s %s: %s vs %s  %d goals (%d leg(s))" % (
                tie["competition_name"], tie["season_label"], tie["round_name"],
                tie["club_a_name"], tie["club_b_name"], tie["goals"], tie["legs"]))

    editions = cur.execute(
        """SELECT season_label, competition_name, winner_club_id, runner_up_club_id
           FROM edition
           WHERE winner_club_id = ? OR runner_up_club_id = ?
           ORDER BY start_year""",
        (cid, cid),
    ).fetchall()
    if editions:
        print("  Trophy finishes:")
        for e in editions:
            role = "Champion" if e["winner_club_id"] == cid else "Runner-up"
            print("    - %s %s (%s)" % (e["competition_name"], e["season_label"], role))

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
    if k1 == k2:
        sys.exit("Head-to-head requires two distinct clubs.")
    conn = _require_db()
    cur = conn.cursor()
    c1 = _club_id(cur, k1)
    c2 = _club_id(cur, k2)
    rec = head_to_head(cur, c1, c2)
    print("Head-to-head: %s vs %s" % (rec["club_a_name"], rec["club_b_name"]))
    print("=" * 64)
    print("  Matches played:  %d" % rec["matches_played"])
    print("  Ties contested:  %d" % rec["ties_contested"])
    print("  Record:          %s %d  Draw %d  %s %d" % (
        rec["club_a_name"], rec["wins_a"], rec["draws"], rec["club_b_name"], rec["wins_b"]))
    print("  Goals:           %d-%d" % (rec["goals_a"], rec["goals_b"]))

    if rec["by_competition"]:
        print("\n  By competition (lineage):")
        for b in rec["by_competition"]:
            print("    - %s: %d match(es)  W-D-L %s  Goals %d-%d" % (
                b["lineage_name"], b["matches_played"],
                _wdl(b["wins_a"], b["draws"], b["wins_b"]),
                b["goals_a"], b["goals_b"]))

    if rec["walkovers"]:
        print("\n  Walkovers / byes (not scored 3-0 unless a match row records it):")
        for w in rec["walkovers"]:
            who = w["winner_name"] or "?"
            note = (" - " + w["notes"]) if w["notes"] else ""
            print("    - %s %s %s: awarded to %s (%s)%s" % (
                w["competition_name"], w["season_label"], w["round_name"],
                who, w["decided_by"], note))

    if rec["matches"]:
        print("\n  Matches:")
        for m in rec["matches"]:
            if m["home_score"] is None or m["away_score"] is None:
                score = "?-?"
            else:
                score = "%s-%s" % (m["home_score"], m["away_score"])
            if m["after_extra_time"]:
                score += " aet"
            when = m["date"] or m["season_label"]
            loc = (" @ " + m["venue"]) if m["venue"] else ""
            print("    %s | %s %s | %s %s %s%s" % (
                when, m["competition_name"], m["round_name"],
                m["home_name"], score, m["away_name"], loc))
    elif not rec["walkovers"]:
        print("\n  No matches recorded between these clubs in the loaded database.")
    conn.close()


def _print_goal_edition(stats):
    print("%s %s" % (stats["competition_name"], stats["season_label"]))
    print("  Total goals: %d" % stats["total_goals"])
    print("  By round:")
    for rnd in stats["rounds"]:
        print("    - %s: %d goal(s) in %d match(es)" % (
            rnd["name"], rnd["goals"], rnd["matches"]))
    if stats["hat_trick_notes"]:
        print("  Hat-trick notes (as stored; scorers are not invented):")
        for n in stats["hat_trick_notes"]:
            print("    - [%s] %s %s: %s" % (
                n["source"], n["season_label"], n["round_name"], n["notes"]))
    else:
        print("  Hat-trick notes: none stored in match / tie notes.")


def cmd_goals(args):
    if not args.club_key and not args.season_label:
        sys.exit("Provide a club key/name and/or --season (e.g. 1959-60).")
    conn = _require_db()
    cur = conn.cursor()
    if args.club_key:
        key = _resolve_club_key(args.club_key)
        cid = _club_id(cur, key)
        rec = club_record(cur, cid, season_label=args.season_label)
        scope = args.season_label or "all-time (loaded database)"
        print("Goal statistics: %s  [%s]" % (rec["name"], scope))
        print("=" * 64)
        print("  Matches: %d  Goals scored: %d  Conceded: %d  GD: %+d" % (
            rec["matches_played"], rec["goals_for"], rec["goals_against"],
            rec["goal_difference"]))
        print("  Average goals scored per match: %s" % rec["average_goals_per_match"])
        print("  Finals goals: %d-%d (%d match(es))" % (
            rec["finals_goals_for"], rec["finals_goals_against"], rec["finals_matches"]))
        if rec["highest_scoring_ties"]:
            print("  Highest-scoring ties:")
            for tie in rec["highest_scoring_ties"]:
                print("    - %s %s %s: %s vs %s  %d goals (%d leg(s))" % (
                    tie["competition_name"], tie["season_label"], tie["round_name"],
                    tie["club_a_name"], tie["club_b_name"], tie["goals"], tie["legs"]))
    if args.season_label:
        if args.club_key:
            print()
        try:
            editions = season_goal_stats(cur, args.season_label)
        except KeyError:
            conn.close()
            sys.exit("No edition found for season %s" % args.season_label)
        for stats in editions:
            _print_goal_edition(stats)
            print()
    conn.close()


def cmd_leaderboard(args):
    conn = _require_db()
    try:
        rows = leaderboard(conn, args.kind, limit=args.limit)
    except ValueError as exc:
        conn.close()
        sys.exit(str(exc))
    titles = {
        "titles": "All-time leaderboard: titles won",
        "matches": "All-time leaderboard: matches played / wins / goal difference",
        "finals": "All-time leaderboard: finals reached (champion + runner-up)",
    }
    print(titles[args.kind])
    print("Derived from the loaded database, not a hard-coded UEFA list.")
    print("Sort: %s" % LEADERBOARD_SORT[args.kind])
    print("=" * 72)
    if not rows:
        print("  (no rows)")
        conn.close()
        return
    if args.kind == "titles":
        print("%-4s %-28s %-8s %s" % ("#", "Club", "Country", "Titles"))
        for r in rows:
            print("%-4s %-28s %-8s %d" % (
                r["rank"], r["name"], r["country"] or "", r["titles"]))
    elif args.kind == "matches":
        print("%-4s %-28s %-8s %7s %5s %5s %5s %5s %5s" % (
            "#", "Club", "Country", "Played", "W", "D", "L", "GD", "GF"))
        for r in rows:
            print("%-4s %-28s %-8s %7d %5d %5d %5d %+5d %5d" % (
                r["rank"], r["name"], r["country"] or "",
                r["matches_played"], r["wins"], r["draws"], r["losses"],
                r["goal_difference"], r["goals_for"]))
    else:
        print("%-4s %-28s %-8s %7s %7s %10s" % (
            "#", "Club", "Country", "Finals", "Titles", "Runner-up"))
        for r in rows:
            print("%-4s %-28s %-8s %7d %7d %10d" % (
                r["rank"], r["name"], r["country"] or "",
                r["finals_reached"], r["titles"], r["runner_up_finishes"]))
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
                       if tie["winner_club_id"] else "-")
                print("    %s vs %s  [%s] -> %s" % (a, b, tie["decided_by"] or "?", win))
                # fetchall() first - get_club_display_name() below reuses this
                # same cursor, which would otherwise truncate the live
                # cur.execute() iteration after the first leg (see the
                # identical bug already fixed in _export_edition()).
                matches = cur.execute(
                    """SELECT * FROM match WHERE tie_id = ? ORDER BY leg_number""",
                    (tie["tie_id"],),
                ).fetchall()
                for m in matches:
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
    # fetchall() at every level before descending - get_club_display_name()
    # below re-executes on this same shared cursor, which would otherwise
    # silently truncate an in-progress cur.execute() iteration at this level.
    rounds = cur.execute(
        "SELECT * FROM round WHERE edition_id = ? ORDER BY round_order", (edition_id,)
    ).fetchall()
    for rnd in rounds:
        rnd_obj = {"name": rnd["name"], "ties": []}
        ties = cur.execute(
            "SELECT * FROM tie WHERE round_id = ? ORDER BY tie_id", (rnd["round_id"],)
        ).fetchall()
        for tie in ties:
            tie_obj = {
                "club_a": get_club_display_name(cur, tie["club_a_id"], edition_id),
                "club_b": get_club_display_name(cur, tie["club_b_id"], edition_id),
                "winner": (get_club_display_name(cur, tie["winner_club_id"], edition_id)
                           if tie["winner_club_id"] else None),
                "decided_by": tie["decided_by"],
                "notes": tie["notes"],
                "legs": [],
            }
            matches = cur.execute(
                "SELECT * FROM match WHERE tie_id = ? ORDER BY leg_number", (tie["tie_id"],)
            ).fetchall()
            for m in matches:
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
                    "notes": m["notes"],
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
    parser = argparse.ArgumentParser(
        description="European Football Database CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_club = sub.add_parser("club", help="All-time European record for a club")
    p_club.add_argument("club_key")
    p_club.set_defaults(func=cmd_club)

    p_h2h = sub.add_parser(
        "h2h",
        help="Head-to-head record (matches, wins, goals, competition breakdown)",
    )
    p_h2h.add_argument("club_1")
    p_h2h.add_argument("club_2")
    p_h2h.set_defaults(func=cmd_h2h)

    p_goals = sub.add_parser(
        "goals",
        help="Goal statistics for a club and/or a season programme",
    )
    p_goals.add_argument("club_key", nargs="?", help="Club key or name")
    p_goals.add_argument(
        "--season", dest="season_label",
        help="Season label (e.g. 1959-60) for edition / round totals",
    )
    p_goals.set_defaults(func=cmd_goals)

    p_lb = sub.add_parser(
        "leaderboard",
        help="All-time club leaderboards derived from the loaded database",
    )
    p_lb.add_argument(
        "kind", choices=list(LEADERBOARD_KINDS),
        help="titles: trophies won; matches: played/wins/goal difference; "
             "finals: finals reached (champion + runner-up)",
    )
    p_lb.add_argument(
        "--limit", type=int, default=None,
        help="Maximum rows to print (default: all)",
    )
    p_lb.set_defaults(func=cmd_leaderboard)

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
