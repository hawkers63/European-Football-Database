#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_rsssf.py - turn pasted RSSSF result lines into seasons.py-ready blocks.

Typical RSSSF preliminary / round line looks like::

    Heart Of Midlothian      Sco  SL Benfica               Por   1-2  0-3  1-5

Usage::

    python tools/import_rsssf.py --stdin
    python tools/import_rsssf.py path/to/lines.txt --season 1960-61 --lineage "European Cup"

The script fuzzy-matches club names against clubs.CLUBS (plus common aliases),
emits L() leg tuples, and validates that leg totals reproduce the printed aggregate.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from clubs import CLUBS

# Extra aliases that appear in RSSSF copy but differ from our canonical names.
ALIASES = {
    "heart of midlothian": "hearts",
    "sl benfica": "benfica",
    "red star belgrade": "red_star",
    "red star (belgrade)": "red_star",
    "crvena zvezda": "red_star",
    "ujpesti dozsa": "ujpest",
    "újpesti dózsa": "ujpest",
    "fredrikstad fk": "fredrikstad",
    "legia warsaw": "cwks_warsaw",
    "cwks warsaw": "cwks_warsaw",
    "cdna sofia": "cdna_sofia",
    "cdna (sofia)": "cdna_sofia",
    "hifk helsinki": "hifk",
    "hifk (helsinki)": "hifk",
    "ifk helsingfors": "hifk",
    "ifk malmo": "ifk_malmo",
    "ifk malmö": "ifk_malmo",
    "sk rapid vienna": "rapid_wien",
    "sk rapid wien": "rapid_wien",
    "bsc young boys": "young_boys",
    "stade de reims": "reims",
    "as la jeunesse d'esch": "jeunesse",
    "jeunesse esch": "jeunesse",
    "fc barcelona": "barcelona",
    "lierse sk": "lierse",
    "wismut karl-marx-stadt": "wismut",
    "hradec kralove": "hradec",
    "spartak hradec kralove": "hradec",
    "cca bucharest": "cca_buc",
    "cca bucuresti": "cca_buc",
    "cca bucurești": "cca_buc",
    "hamburger sv": "hamburg",
    "real madrid": "real_madrid",
    "ac fiorentina": "fiorentina",
    "fc lucerne": "lucerne",
    "fc luzern": "lucerne",
    "nk dinamo zagreb": "dinamo_zagreb",
    "nk dinamo (zagreb)": "dinamo_zagreb",
    "fk austria vienna": "austria_wien",
    "fk austria (vienna)": "austria_wien",
    "austria wien": "austria_wien",
    "borussia monchengladbach": "gladbach",
    "borussia mönchengladbach": "gladbach",
    "wolverhampton wanderers": "wolves",
    "ferencvarosi tc": "ferencvaros",
    "ferencvárosi tc": "ferencvaros",
    "red star brno": "red_star_brno",
    "ruda hvezda brno": "red_star_brno",
    "rudá hvězda brno": "red_star_brno",
    "ask vorwarts berlin": "vorwarts",
    "ask vorwärts berlin": "vorwarts",
    "vorwarts berlin": "vorwarts",
}


SCORE = re.compile(r"(\d+)-(\d+)")
# club blob then country code then club blob then country code then scores
LINE_RE = re.compile(
    r"^(?P<a>.+?)\s+(?P<ac>[A-Za-z]{3})\s+"
    r"(?P<b>.+?)\s+(?P<bc>[A-Za-z]{3})\s+"
    r"(?P<scores>(?:\d+-\d+\s*)+)"
    r"(?P<flags>.*)$"
)


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower().replace(".", ""))


def match_club(name: str, cutoff: float = 0.72):
    """Return (club_key, confidence) or (None, 0)."""
    n = _norm(name)
    if n in ALIASES:
        return ALIASES[n], 1.0
    # strip trailing parenthetical city
    n2 = re.sub(r"\s*\([^)]*\)\s*", " ", n).strip()
    if n2 in ALIASES:
        return ALIASES[n2], 1.0

    by_name = {_norm(c["name"]): k for k, c in CLUBS.items()}
    if n in by_name:
        return by_name[n], 1.0
    if n2 in by_name:
        return by_name[n2], 1.0

    candidates = list(by_name.keys()) + list(ALIASES.keys())
    hit = difflib.get_close_matches(n, candidates, n=1, cutoff=cutoff)
    if not hit:
        hit = difflib.get_close_matches(n2, candidates, n=1, cutoff=cutoff)
    if not hit:
        return None, 0.0
    key = by_name.get(hit[0]) or ALIASES.get(hit[0])
    ratio = difflib.SequenceMatcher(None, n, hit[0]).ratio()
    return key, ratio


def parse_rsssf_line(line: str):
    """Parse one RSSSF result line into a structured dict (or None)."""
    raw = line.strip()
    if not raw or raw.startswith("#") or raw.lower().startswith("additional"):
        return None
    # walkover / bye prose lines are left for the human
    if "walkover" in raw.lower() or "withdrew" in raw.lower():
        return {"type": "note", "text": raw}

    m = LINE_RE.match(raw)
    if not m:
        return None

    scores = SCORE.findall(m.group("scores"))
    if len(scores) < 2:
        return None
    s1 = tuple(map(int, scores[0]))
    s2 = tuple(map(int, scores[1]))
    agg = tuple(map(int, scores[2])) if len(scores) >= 3 else (s1[0] + s2[1], s1[1] + s2[0])

    a_name, b_name = m.group("a").strip(), m.group("b").strip()
    a_key, a_conf = match_club(a_name)
    b_key, b_conf = match_club(b_name)
    flags = m.group("flags").strip()
    playoff = None
    if len(scores) >= 4:
        playoff = tuple(map(int, scores[3]))

    return {
        "type": "tie",
        "a_name": a_name,
        "b_name": b_name,
        "a_key": a_key,
        "b_key": b_key,
        "a_conf": a_conf,
        "b_conf": b_conf,
        "leg1": s1,
        "leg2": s2,
        "agg": agg,
        "playoff": playoff,
        "flags": flags,
        "raw": raw,
    }


def validate_aggregate(parsed) -> list:
    """Return problem strings if legs do not reproduce RSSSF aggregate."""
    if parsed["type"] != "tie":
        return []
    a1, b1 = parsed["leg1"]
    a2, b2 = parsed["leg2"]
    # RSSSF prints leg1 as t1-home, leg2 as t2-home, agg as t1-t2
    ga = a1 + b2
    gb = b1 + a2
    problems = []
    if (ga, gb) != tuple(parsed["agg"]):
        problems.append(
            "AGG mismatch for %s v %s: legs give %d-%d, RSSSF says %d-%d"
            % (parsed["a_name"], parsed["b_name"], ga, gb, parsed["agg"][0], parsed["agg"][1])
        )
    return problems


def emit_tie_block(parsed) -> str:
    """Format a seasons.py tie dict using L() helpers."""
    if parsed["type"] == "note":
        return "            # %s" % parsed["text"]

    a, b = parsed["a_key"] or "UNKNOWN_A", parsed["b_key"] or "UNKNOWN_B"
    a1, b1 = parsed["leg1"]
    a2, b2 = parsed["leg2"]
    ga, gb = parsed["agg"]
    if parsed["playoff"] is not None:
        by = "replay"
        win = a if parsed["playoff"][0] > parsed["playoff"][1] else b
    else:
        by = "aggregate"
        win = a if ga > gb else (b if gb > ga else "None")
    legs = [
        'L("%s", "%s", %d, %d)' % (a, b, a1, b1),
        'L("%s", "%s", %d, %d)' % (b, a, a2, b2),
    ]
    if parsed["playoff"] is not None:
        p1, p2 = parsed["playoff"]
        legs.append('L("%s", "%s", %d, %d, venue="(play-off)")' % (a, b, p1, p2))
    warn = []
    if parsed["a_key"] is None:
        warn.append("unmatched home %r" % parsed["a_name"])
    if parsed["b_key"] is None:
        warn.append("unmatched away %r" % parsed["b_name"])
    note = ('\n             "note": "%s",' % "; ".join(warn)) if warn else ""
    return (
        '            {"t1": "%s", "t2": "%s", "win": "%s", "by": "%s", "agg": (%d, %d),\n'
        '             "legs": [%s, %s%s]},%s'
        % (
            a, b, win, by, ga, gb,
            legs[0], legs[1],
            (",\n                      " + legs[2]) if len(legs) > 2 else "",
            note,
        )
    )


def emit_season_skeleton(season_label, lineage, competition_name, ties_blocks, round_name="Round"):
    body = "\n".join(ties_blocks)
    return '''{
  "lineage": "%s", "season_label": "%s", "start_year": %s,
  "competition_name": "%s",
  "winner": "TODO", "runner_up": "TODO", "away_goals_active": False,
  "notes": "Imported from RSSSF draft - review winner/runner-up and round names.",
  "rounds": [
    {"name": "%s", "ties": [
%s
    ]},
  ],
}
''' % (lineage, season_label, season_label.split("-")[0], competition_name, round_name, body)


def main(argv=None):
    p = argparse.ArgumentParser(description="Parse RSSSF lines into seasons.py blocks")
    p.add_argument("path", nargs="?", help="Text file of RSSSF lines (default: stdin)")
    p.add_argument("--stdin", action="store_true", help="Read lines from stdin")
    p.add_argument("--season", default="YYYY-YY")
    p.add_argument("--lineage", default="European Cup")
    p.add_argument("--competition", default=None)
    p.add_argument("--round-name", default="Round")
    args = p.parse_args(argv)

    if args.stdin or not args.path:
        text = sys.stdin.read()
    else:
        with open(args.path, encoding="utf-8") as fh:
            text = fh.read()

    parsed_rows = []
    problems = []
    for line in text.splitlines():
        parsed = parse_rsssf_line(line)
        if not parsed:
            continue
        parsed_rows.append(parsed)
        problems.extend(validate_aggregate(parsed))

    if problems:
        print("VALIDATION FAILED:", file=sys.stderr)
        for prob in problems:
            print("  !!", prob, file=sys.stderr)
        sys.exit(1)

    blocks = [emit_tie_block(r) for r in parsed_rows]
    comp = args.competition or args.lineage
    print(emit_season_skeleton(args.season, args.lineage, comp, blocks, args.round_name))
    unmatched = [r for r in parsed_rows if r.get("type") == "tie" and (not r["a_key"] or not r["b_key"])]
    if unmatched:
        print("# WARNING: %d tie(s) had unmatched club names - search UNKNOWN_ in output." % len(unmatched),
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
