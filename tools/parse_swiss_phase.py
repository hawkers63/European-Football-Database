#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_swiss_phase.py - RSSSF / UEFA league-phase listings to season fragments.

Models the 36-club Swiss league phase: eight opponents each, one table,
UEFA-style tie-breakers stored as data on the edition. Standings are derived
from fixtures. Mid-season movement (a club dropping into another trophy line)
is emitted as competition_transfer rows, never as special-case code.

Does not write european_football.db.

Usage::

    python tools/parse_swiss_phase.py tools/fixtures/swiss_miniature.rsssf \\
        --season 2024-25 --points-for-win 3 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.parse_group_stage import enrich_group, emit_season_fragment
from tools.phase_parse import parse_blocks
from tools.standings import DEFAULT_SWISS_TIEBREAK, rank_table


def opponents_map(matches):
    opp = defaultdict(set)
    for m in matches:
        if not m.get("home") or not m.get("away"):
            continue
        opp[m["home"]].add(m["away"])
        opp[m["away"]].add(m["home"])
    return opp


def parse_swiss_phase(text: str, points_for_win: int, tiebreak: str = DEFAULT_SWISS_TIEBREAK):
    raw_groups, transfers = parse_blocks(text)
    phases = []
    for g in raw_groups:
        enriched = enrich_group(g, points_for_win, tiebreak)
        enriched["phase_type"] = "league"
        if not enriched["name"] or enriched["name"].startswith("Group"):
            if g.get("phase_type") == "league" or g.get("name") == "League phase":
                enriched["name"] = "League phase"
        opp = opponents_map(enriched["matches"])
        enriched["opponents"] = {k: sorted(v) for k, v in opp.items()}
        enriched["n_clubs"] = len(enriched["clubs"])
        phases.append(enriched)
    return {"phases": phases, "transfers": transfers}


def swiss_invariants(phase: dict, expect_clubs=36, expect_opponents=8):
    """Return problem strings for the 36 x 8 Swiss model (skipped if smaller)."""
    problems = []
    n = len(phase["clubs"])
    if n == expect_clubs:
        for club, opps in phase["opponents"].items():
            if len(opps) != expect_opponents:
                problems.append("%s has %d opponents, expected %d" % (club, len(opps), expect_opponents))
        missing = [c for c in phase["clubs"] if c not in phase["opponents"]]
        for club in missing:
            problems.append("%s has no opponents listed" % club)
    return problems


def main(argv=None):
    p = argparse.ArgumentParser(description="Parse Swiss / league-phase listings (does not write the database).")
    p.add_argument("path", nargs="?", help="Text file (default: stdin)")
    p.add_argument("--stdin", action="store_true")
    p.add_argument("--season", default="YYYY-YY")
    p.add_argument("--lineage", default="European Cup")
    p.add_argument("--competition", default="UEFA Champions League")
    p.add_argument("--points-for-win", type=int, required=True, choices=(2, 3),
                   help="Edition flag. Never inferred from the season label.")
    p.add_argument("--tiebreak", default=DEFAULT_SWISS_TIEBREAK)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--expect-clubs", type=int, default=0,
                   help="If 36, enforce eight-opponent invariant. 0 = no size check.")
    args = p.parse_args(argv)

    if args.stdin or not args.path:
        text = sys.stdin.read()
    else:
        with open(args.path, encoding="utf-8") as fh:
            text = fh.read()

    parsed = parse_swiss_phase(text, args.points_for_win, args.tiebreak)
    problems = []
    for phase in parsed["phases"]:
        problems.extend("%s: %s" % (phase["name"], x) for x in phase["problems"])
        if args.expect_clubs:
            problems.extend(swiss_invariants(phase, expect_clubs=args.expect_clubs))

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
            "phases": [
                {
                    "name": g["name"],
                    "n_clubs": g["n_clubs"],
                    "n_matches": len(g["matches"]),
                    "computed_table": [
                        {k: row[k] for k in ("rank", "club", "played", "w", "d", "l", "gf", "ga", "pts")}
                        for row in g["computed_table"]
                    ],
                    "opponents": g["opponents"],
                    "unmatched": g["unmatched"],
                }
                for g in parsed["phases"]
            ],
            "transfers": parsed["transfers"],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        if args.json:
            return 0

    # Reuse group-stage emitter; caller relabels the round as league.
    groups = []
    for g in parsed["phases"]:
        item = dict(g)
        item["phase_type"] = "league"
        groups.append(item)
    print(emit_season_fragment(
        args.season, args.lineage, args.competition, args.points_for_win, args.tiebreak,
        groups, parsed["transfers"],
    ).replace('"phase_type": "group"', '"phase_type": "league"', 1)
     .replace('"name": "Group Stage"', '"name": "League phase"', 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
