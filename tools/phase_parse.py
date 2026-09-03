# -*- coding: utf-8 -*-
"""Shared RSSSF group / league-phase line parsers.

Used by parse_group_stage.py and parse_swiss_phase.py. Club matching reuses
tools.import_rsssf so knockout and standings importers stay in step.
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.import_rsssf import match_club

# "UC Sampdoria             (1) 2  Red Star (Belgrade)      (0) 0"
# "Red Star (Belgrade)      (1) 3  RSC Anderlecht           (1) 2  in Budapest"
MATCH_RE = re.compile(
    r"^(?P<home>.+?)\s+\((?P<hht>\d+)\)\s+(?P<hs>\d+)\s+"
    r"(?P<away>.+?)\s+\((?P<aht>\d+)\)\s+(?P<as>\d+)"
    r"(?P<tail>.*)$"
)

# Compact "Club  2-1  Club" / "Club  2-1  Club  aet" (Swiss listings, dry-runs).
COMPACT_RE = re.compile(
    r"^(?P<home>.+?)\s+(\d+)\s*[-:]\s*(\d+)\s+(?P<away>.+?)$"
)

# "UC SAMPDORIA               6  3  2  1 10  5  8"
TABLE_RE = re.compile(
    r"^(?P<name>.+?)\s+"
    r"(?P<p>\d+)\s+(?P<w>\d+)\s+(?P<d>\d+)\s+(?P<l>\d+)\s+"
    r"(?P<gf>\d+)\s+(?P<ga>\d+)\s+(?P<pts>\d+)\s*$"
)

TABLE_HEADER_RE = re.compile(r"^\s*P\s+W\s+D\s+L\s+F\s+A\s+Pts\s*$", re.I)
GROUP_HEADER_RE = re.compile(r"^Group\s+([A-Za-z0-9]+)\s*$", re.I)
MATCHDAY_RE = re.compile(r"^Matchday\s+(\d+)\s*$", re.I)
LEAGUE_HEADER_RE = re.compile(r"^(League phase|Swiss phase|League Phase)\s*$", re.I)
TRANSFER_HEADER_RE = re.compile(r"^Transfers?\s*$", re.I)
# Benfica  rank=3  ->  UEFA Europa League  knockout_playoff  reason=group_third
TRANSFER_RE = re.compile(
    r"^(?P<club>.+?)\s+rank=(?P<rank>\d+)\s*->\s*(?P<dest>.+?)"
    r"(?:\s+reason=(?P<reason>\S+))?\s*$",
    re.I,
)
WALKOVER_RE = re.compile(r"walkover|withdrew|awarded", re.I)


def resolve_club(name: str):
    key, conf = match_club(name)
    return key, conf, name.strip()


def parse_match_line(line: str, matchday=None):
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return None
    if WALKOVER_RE.search(raw) and not MATCH_RE.match(raw):
        return {
            "type": "walkover",
            "raw": raw,
            "matchday": matchday,
            "awarded": True,
            "hs": None,
            "as": None,
            "home": None,
            "away": None,
            "note": raw,
        }
    m = MATCH_RE.match(raw)
    if m:
        home_name = m.group("home").strip()
        away_name = m.group("away").strip()
        h_key, h_conf, _ = resolve_club(home_name)
        a_key, a_conf, _ = resolve_club(away_name)
        tail = m.group("tail").strip()
        note = tail or None
        awarded = bool(WALKOVER_RE.search(tail))
        extras = {}
        if "aet" in tail.lower():
            extras["aet"] = True
        venue = None
        if tail.lower().startswith("in "):
            venue = tail[3:].strip()
            note = tail
        return {
            "type": "match",
            "home_name": home_name,
            "away_name": away_name,
            "home": h_key,
            "away": a_key,
            "home_conf": h_conf,
            "away_conf": a_conf,
            "hs": int(m.group("hs")),
            "as": int(m.group("as")),
            "hht": int(m.group("hht")),
            "aht": int(m.group("aht")),
            "matchday": matchday,
            "note": note,
            "venue": venue,
            "awarded": awarded,
            "walkover_winner": (h_key if awarded and int(m.group("hs")) > int(m.group("as"))
                                else (a_key if awarded else None)),
            "raw": raw,
            **extras,
        }
    c = COMPACT_RE.match(raw)
    if c:
        home_name, away_name = c.group("home").strip(), c.group("away").strip()
        # Compact away may include trailing notes; split flags.
        away_name, _, flags = away_name.partition("  ")
        away_name = away_name.strip()
        hs, aws = int(c.group(2)), int(c.group(3))
        h_key, h_conf, _ = resolve_club(home_name)
        a_key, a_conf, _ = resolve_club(away_name)
        tail = (flags or "").strip()
        awarded = bool(WALKOVER_RE.search(raw))
        return {
            "type": "match",
            "home_name": home_name,
            "away_name": away_name,
            "home": h_key,
            "away": a_key,
            "home_conf": h_conf,
            "away_conf": a_conf,
            "hs": hs,
            "as": aws,
            "matchday": matchday,
            "note": tail or None,
            "venue": None,
            "awarded": awarded,
            "walkover_winner": (h_key if awarded and hs > aws else (a_key if awarded else None)),
            "raw": raw,
        }
    return None


def parse_table_line(line: str):
    raw = line.strip()
    if not raw or TABLE_HEADER_RE.match(raw):
        return None
    m = TABLE_RE.match(raw)
    if not m:
        return None
    name = m.group("name").strip()
    key, conf, _ = resolve_club(name)
    return {
        "type": "table_row",
        "name": name,
        "club": key,
        "conf": conf,
        "played": int(m.group("p")),
        "w": int(m.group("w")),
        "d": int(m.group("d")),
        "l": int(m.group("l")),
        "gf": int(m.group("gf")),
        "ga": int(m.group("ga")),
        "pts": int(m.group("pts")),
        "raw": raw,
    }


def parse_transfer_line(line: str):
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return None
    m = TRANSFER_RE.match(raw)
    if not m:
        return None
    club_name = m.group("club").strip()
    key, conf, _ = resolve_club(club_name)
    dest = m.group("dest").strip()
    reason = (m.group("reason") or "group_third").strip()
    return {
        "type": "transfer",
        "club_name": club_name,
        "club": key,
        "conf": conf,
        "from_rank": int(m.group("rank")),
        "to_competition": dest,
        "reason": reason,
        "raw": raw,
    }


def parse_blocks(text: str):
    """Split RSSSF text into named groups / a league phase plus optional transfers."""
    groups = []
    transfers = []
    current = None
    in_table = False
    in_transfers = False
    matchday = None

    def start_group(name, phase):
        nonlocal current, in_table, in_transfers
        if current:
            groups.append(current)
        current = {
            "name": name,
            "phase_type": phase,
            "matches": [],
            "printed_table": [],
            "walkover_notes": [],
        }
        in_table = False
        in_transfers = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("Additional"):
            continue
        if stripped.startswith("#") and not stripped.startswith("#-"):
            continue

        gh = GROUP_HEADER_RE.match(stripped)
        if gh:
            start_group("Group %s" % gh.group(1).upper(), "group")
            matchday = None
            continue
        if LEAGUE_HEADER_RE.match(stripped):
            start_group("League phase", "league")
            matchday = None
            continue
        if TRANSFER_HEADER_RE.match(stripped):
            if current:
                groups.append(current)
                current = None
            in_transfers = True
            in_table = False
            continue
        md = MATCHDAY_RE.match(stripped)
        if md:
            matchday = int(md.group(1))
            continue
        if TABLE_HEADER_RE.match(stripped):
            in_table = True
            continue
        if in_transfers:
            tr = parse_transfer_line(stripped)
            if tr:
                transfers.append(tr)
            continue
        if current is None:
            continue
        if in_table:
            row = parse_table_line(stripped)
            if row:
                current["printed_table"].append(row)
                continue
            # Non-table prose ("Sampdoria qualify") ends the table.
            in_table = False
            continue
        parsed = parse_match_line(stripped, matchday=matchday)
        if parsed and parsed["type"] == "match":
            current["matches"].append(parsed)
        elif parsed and parsed["type"] == "walkover":
            current["walkover_notes"].append(parsed)
            current["matches"].append(parsed)

    if current:
        groups.append(current)
    return groups, transfers
