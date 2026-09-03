#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_group_stage.py - RSSSF group-stage blocks to seasons.py fragments.

Does not write european_football.db. Feed the printed fragment into seasons.py
(and register any new club keys in clubs.py), then rebuild with
``python build_database.py --force``.

Points-for-a-win is an explicit flag (--points-for-win 2|3). The parser never
infers 2 vs 3 from a calendar year: 1991-92 used 2, UEFA switched the
Champions League to 3 in 1995-96, and later editions can differ again.

Usage::

    python tools/parse_group_stage.py tools/fixtures/cl_1991_92_groups.rsssf \\
        --season 1991-92 --points-for-win 2 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.phase_parse import parse_blocks
from tools.standings import (
    DEFAULT_GROUP_TIEBREAK,
    rank_table,
    tables_match,
)


def clubs_in_group(group: dict):
    keys = []
    seen = set()
    for row in group.get("printed_table") or []:
        k = row.get("club")
        if k and k not in seen:
            seen.add(k)
            keys.append(k)
    for m in group.get("matches") or []:
        for k in (m.get("home"), m.get("away")):
            if k and k not in seen:
                seen.add(k)
                keys.append(k)
    return keys


def enrich_group(group: dict, points_for_win: int, tiebreak: str):
    clubs = clubs_in_group(group)
    played = [m for m in group["matches"] if m.get("type") == "match" and m.get("hs") is not None]
    computed = rank_table(clubs, played, points_for_win, tiebreak) if clubs else []
    printed = []
    for row in group.get("printed_table") or []:
        printed.append({
            "club": row.get("club"),
            "played": row["played"],
            "w": row["w"],
            "d": row["d"],
            "l": row["l"],
            "gf": row["gf"],
            "ga": row["ga"],
            "pts": row["pts"],
            "name": row.get("name"),
        })
    problems = []
    if printed and computed:
        problems = tables_match(computed, printed)
    unmatched = []
    for m in group["matches"]:
        if m.get("type") == "match":
            if not m.get("home"):
                unmatched.append(m.get("home_name"))
            if not m.get("away"):
                unmatched.append(m.get("away_name"))
    for row in group.get("printed_table") or []:
        if not row.get("club"):
            unmatched.append(row.get("name"))
    return {
        "name": group["name"],
        "phase_type": group.get("phase_type") or "group",
        "clubs": clubs,
        "matches": played,
        "walkover_notes": group.get("walkover_notes") or [],
        "printed_table": printed,
        "computed_table": computed,
        "problems": problems,
        "unmatched": unmatched,
    }


def emit_season_fragment(season_label, lineage, competition_name, points_for_win,
                         tiebreak, groups, transfers, winner="TODO", runner_up="TODO"):
    round_name = "Group Stage"
    lines = [
        "{",
        '  "lineage": "%s", "season_label": "%s", "start_year": %s,' % (
            lineage, season_label, season_label.split("-")[0]),
        '  "competition_name": "%s",' % competition_name,
        '  "winner": "%s", "runner_up": "%s", "away_goals_active": False,' % (winner, runner_up),
        '  "points_for_win": %d,' % points_for_win,
        '  "standings_tiebreak": "%s",' % tiebreak,
        '  "notes": "Imported group-stage draft from RSSSF. Review club keys.",',
        '  "rounds": [',
        '    {"name": "%s", "phase_type": "group", "ties": [], "groups": [' % round_name,
    ]
    g_blocks = []
    for g in groups:
        matches = []
        for m in g["matches"]:
            extra = []
            if m.get("matchday") is not None:
                extra.append('"matchday": %s' % m["matchday"])
            if m.get("venue"):
                extra.append('"venue": %s' % json.dumps(m["venue"], ensure_ascii=False))
            if m.get("note"):
                extra.append('"note": %s' % json.dumps(m["note"], ensure_ascii=False))
            if m.get("awarded"):
                extra.append('"awarded": True')
            extra_s = (", " + ", ".join(extra)) if extra else ""
            matches.append(
                '        {"home": "%s", "away": "%s", "hs": %s, "as": %s%s}'
                % (m.get("home") or "UNKNOWN", m.get("away") or "UNKNOWN", m["hs"], m["as"], extra_s)
            )
        table = []
        for row in g["computed_table"]:
            table.append(
                '        {"club": "%s", "played": %d, "w": %d, "d": %d, "l": %d, '
                '"gf": %d, "ga": %d, "pts": %d}'
                % (row["club"], row["played"], row["w"], row["d"], row["l"],
                   row["gf"], row["ga"], row["pts"])
            )
        g_blocks.append(
            '      {"name": "%s", "clubs": %s,\n'
            '       "matches": [\n%s\n       ],\n'
            '       "table": [\n%s\n       ]}'
            % (g["name"], json.dumps(g["clubs"]), ",\n".join(matches), ",\n".join(table))
        )
    lines.append(",\n".join(g_blocks))
    lines.append("    ]},")
    lines.append("  ],")
    if transfers:
        t_lines = []
        for t in transfers:
            t_lines.append(
                '    {"club": "%s", "from_rank": %d, "to_competition": %s, "reason": %s}'
                % (t.get("club") or "UNKNOWN", t["from_rank"],
                   json.dumps(t["to_competition"], ensure_ascii=False),
                   json.dumps(t["reason"], ensure_ascii=False))
            )
        lines.append('  "transfers": [')
        lines.append(",\n".join(t_lines))
        lines.append("  ],")
    lines.append("}")
    return "\n".join(lines) + "\n"


def parse_group_stage(text: str, points_for_win: int, tiebreak: str = DEFAULT_GROUP_TIEBREAK):
    raw_groups, transfers = parse_blocks(text)
    groups = [enrich_group(g, points_for_win, tiebreak) for g in raw_groups
              if g.get("phase_type") != "league" or g.get("matches") or g.get("printed_table")]
    # Keep groups even if labelled league; caller decides.
    return {"groups": groups, "transfers": transfers}


def main(argv=None):
    p = argparse.ArgumentParser(description="Parse RSSSF group-stage blocks (does not write the database).")
    p.add_argument("path", nargs="?", help="Text file of RSSSF group blocks (default: stdin)")
    p.add_argument("--stdin", action="store_true")
    p.add_argument("--season", default="YYYY-YY")
    p.add_argument("--lineage", default="European Cup")
    p.add_argument("--competition", default=None)
    p.add_argument("--points-for-win", type=int, required=True, choices=(2, 3),
                   help="Edition flag. Never inferred from the season label.")
    p.add_argument("--tiebreak", default=DEFAULT_GROUP_TIEBREAK)
    p.add_argument("--dry-run", action="store_true", help="Print JSON summary as well as the fragment")
    p.add_argument("--json", action="store_true", help="JSON only")
    args = p.parse_args(argv)

    if args.stdin or not args.path:
        text = sys.stdin.read()
    else:
        with open(args.path, encoding="utf-8") as fh:
            text = fh.read()

    parsed = parse_group_stage(text, args.points_for_win, args.tiebreak)
    problems = []
    unmatched = []
    for g in parsed["groups"]:
        problems.extend("%s: %s" % (g["name"], x) for x in g["problems"])
        unmatched.extend(g["unmatched"])

    if problems:
        print("VALIDATION FAILED:", file=sys.stderr)
        for prob in problems:
            print("  !!", prob, file=sys.stderr)
        sys.exit(1)

    if args.json or args.dry_run:
        payload = {
            "season": args.season,
            "points_for_win": args.points_for_win,
            "tiebreak": args.tiebreak,
            "groups": [
                {
                    "name": g["name"],
                    "clubs": g["clubs"],
                    "n_matches": len(g["matches"]),
                    "computed_table": [
                        {k: row[k] for k in ("rank", "club", "played", "w", "d", "l", "gf", "ga", "pts")}
                        for row in g["computed_table"]
                    ],
                    "unmatched": g["unmatched"],
                }
                for g in parsed["groups"]
            ],
            "transfers": parsed["transfers"],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        if args.json:
            return 0

    comp = args.competition or args.lineage
    print(emit_season_fragment(
        args.season, args.lineage, comp, args.points_for_win, args.tiebreak,
        parsed["groups"], parsed["transfers"],
    ))
    if unmatched:
        print("# WARNING: unmatched club names: %s" % ", ".join(unmatched), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
