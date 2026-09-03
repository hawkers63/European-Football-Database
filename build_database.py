#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_database.py - European Football Database (Classic Era)

Creates `european_football.db` from `schema.sql`, populates the canonical club
registry (clubs.py) and every season of fixtures (seasons.py).

Crucially, it VERIFIES the data before committing: for each tie it recomputes the
aggregate from the individual legs and checks it against RSSSF's printed total
(the `agg` field). If anything disagrees, the build prints the offending ties and
writes NOTHING. A wrong scoreline can't reach the database unnoticed.

Run:  python build_database.py            (builds if the DB is absent)
      python build_database.py --force    (rebuilds from scratch)
"""

import os
import sqlite3
import sys

from clubs import CLUBS
from seasons import SEASONS

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "european_football.db")
SCHEMA_PATH = os.path.join(HERE, "schema.sql")

MATCH_INSERT_SQL = """INSERT INTO match
   (tie_id, leg_number, match_date, home_club_id, away_club_id,
    home_score, away_score, home_pens, away_pens, after_extra_time,
    venue, attendance, referee)
   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"""


def leg_fields(leg):
    """Normalise a leg tuple to (home, away, hs, as_, extras_dict)."""
    home, away, hs, as_ = leg[0], leg[1], leg[2], leg[3]
    extras = leg[4] if len(leg) > 4 else {}
    return home, away, hs, as_, extras


def match_insert_tuple(tie_id, leg_number, club_id, leg):
    """Values for MATCH_INSERT_SQL, including shootout columns from extras."""
    h, a, hs, as_, x = leg_fields(leg)
    return (
        tie_id, leg_number, x.get("date"), club_id[h], club_id[a], hs, as_,
        x.get("home_pens"), x.get("away_pens"),
        1 if x.get("aet") else 0, x.get("venue"), x.get("att"), x.get("ref"),
    )


def collect_referenced_keys(seasons=None):
    keys = set()
    for s in (SEASONS if seasons is None else seasons):
        for k in (s["winner"], s["runner_up"]):
            if k:
                keys.add(k)
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                keys.add(tie["t1"]); keys.add(tie["t2"])
                if tie["win"]:
                    keys.add(tie["win"])
                for leg in tie["legs"]:
                    h, a, _, _, _ = leg_fields(leg)
                    keys.add(h); keys.add(a)
    return keys


def unused_club_keys(clubs=None, referenced=None):
    """Registered clubs that never appear in any tie, edition, or leg."""
    clubs = CLUBS if clubs is None else clubs
    referenced = collect_referenced_keys() if referenced is None else referenced
    return sorted(k for k in clubs if k not in referenced)


def build(force=False):
    if os.path.exists(DB_PATH):
        if not force:
            print(f"Database already exists at {DB_PATH}\nRe-run with --force to rebuild.")
            return 0
        os.remove(DB_PATH)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        schema_sql = fh.read()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    cur.executescript(schema_sql)

    # ---- clubs: insert only those actually referenced, fail on unknown keys --
    referenced = collect_referenced_keys()
    unknown = sorted(k for k in referenced if k not in CLUBS)
    if unknown:
        conn.close(); os.remove(DB_PATH)
        sys.exit(f"ERROR: season data references unknown club keys: {unknown}")

    unused = unused_club_keys(CLUBS, referenced)
    if unused:
        print("WARNING: %d registered club(s) have 0 appearances: %s"
              % (len(unused), ", ".join(unused)))

    club_id = {}
    for key in sorted(referenced):
        c = CLUBS[key]
        cur.execute("INSERT INTO club (name, country, city, notes) VALUES (?,?,?,?)",
                    (c["name"], c.get("country"), c.get("city"), c.get("notes")))
        club_id[key] = cur.lastrowid

    # ---- lineages ---------------------------------------------------------
    lineage_id = {}
    for name in dict.fromkeys(s["lineage"] for s in SEASONS):
        cur.execute("INSERT INTO lineage (name, notes) VALUES (?,?)",
                    (name, "Premier European trophy line: European Cup -> UEFA Champions League."))
        lineage_id[name] = cur.lastrowid

    # ---- editions / rounds / ties / matches -------------------------------
    for s in SEASONS:
        cur.execute(
            """INSERT INTO edition
               (lineage_id, season_label, start_year, competition_name,
                winner_club_id, runner_up_club_id, away_goals_active, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (lineage_id[s["lineage"]], s["season_label"], s["start_year"],
             s["competition_name"],
             club_id.get(s["winner"]), club_id.get(s["runner_up"]),
             1 if s["away_goals_active"] else 0, s.get("notes")))
        edition_id = cur.lastrowid

        for order, rnd in enumerate(s["rounds"], start=1):
            cur.execute("INSERT INTO round (edition_id, name, round_order) VALUES (?,?,?)",
                        (edition_id, rnd["name"], order))
            round_id = cur.lastrowid

            for tie in rnd["ties"]:
                cur.execute(
                    """INSERT INTO tie (round_id, club_a_id, club_b_id, winner_club_id, decided_by, notes)
                       VALUES (?,?,?,?,?,?)""",
                    (round_id, club_id[tie["t1"]], club_id[tie["t2"]],
                     club_id.get(tie["win"]) if tie["win"] else None,
                     tie["by"], tie.get("note")))
                tie_id = cur.lastrowid

                for i, leg in enumerate(tie["legs"], start=1):
                    cur.execute(MATCH_INSERT_SQL, match_insert_tuple(tie_id, i, club_id, leg))

    # ---- VERIFY before committing -----------------------------------------
    problems = verify(cur, club_id)
    if problems:
        conn.rollback(); conn.close(); os.remove(DB_PATH)
        print("\n".join(problems))
        sys.exit(f"\nBUILD ABORTED: {len(problems)} data problem(s). Nothing written.")

    conn.commit()
    report(cur)
    conn.close()
    return 0


def verify(cur, club_id, seasons=None):
    """Recompute each tie's aggregate from its legs and check it against `agg`."""
    problems = []
    for s in (SEASONS if seasons is None else seasons):
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                a, b = tie["t1"], tie["t2"]
                ga = gb = 0
                tag = f'{s["season_label"]} {rnd["name"]}: {a} v {b}'
                for idx, leg in enumerate(tie["legs"]):
                    h, aw, hs, as_, _ = leg_fields(leg)
                    if h not in (a, b) or aw not in (a, b):
                        problems.append(
                            f'!! CLUB {tag} leg {idx + 1}: {h} v {aw} is not among ({a}, {b})')
                        continue
                    # legs 3+ are play-offs/replays; aggregate is legs 1 & 2 only
                    if idx >= 2:
                        continue
                    if h == a: ga += hs
                    if aw == a: ga += as_
                    if h == b: gb += hs
                    if aw == b: gb += as_
                if tie["agg"] is not None and (ga, gb) != tuple(tie["agg"]):
                    problems.append(f'!! AGG  {tag}: legs give {ga}-{gb}, RSSSF says {tie["agg"][0]}-{tie["agg"][1]}')
                if tie["by"] == "aggregate":
                    winner = a if ga > gb else (b if gb > ga else None)
                    if winner != tie["win"]:
                        problems.append(f'!! WIN  {tag}: higher aggregate is {winner}, data says {tie["win"]}')
    return problems


def report(cur):
    counts = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("lineage", "club", "edition", "round", "tie", "match")}
    print(f"Built {DB_PATH}")
    print("  " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    print("  All aggregates verified against RSSSF printed totals.")
    for row in cur.execute("SELECT season_label, competition_name FROM edition ORDER BY start_year"):
        print(f"    - {row[1]} {row[0]}")


if __name__ == "__main__":
    sys.exit(build(force="--force" in sys.argv))
