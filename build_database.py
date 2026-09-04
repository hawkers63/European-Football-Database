#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_database.py - European Football Database (Classic Era)

Creates `european_football.db` from `schema.sql`, populates the canonical club
registry (clubs.py) and every season of fixtures (seasons.py).

Crucially, it VERIFIES the data before committing: for each tie it recomputes the
aggregate from the individual legs and checks it against RSSSF's printed total
(the `agg` field). If anything disagrees, the build prints the offending ties and
writes NOTHING - the rebuild happens in a temporary file, so a failed `--force`
leaves the last known-good database exactly as it was. A wrong scoreline can't
reach the database unnoticed, and a failed rebuild can't destroy a good one.

Run:  python build_database.py            (builds if the DB is absent)
      python build_database.py --force    (rebuilds from scratch)
"""

import os
import sqlite3
import sys

from clubs import CLUBS, CLUB_NAME_HISTORY
from lineages import LINEAGES
from seasons import SEASONS

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "european_football.db")
SCHEMA_PATH = os.path.join(HERE, "schema.sql")

MATCH_INSERT_SQL = """INSERT INTO match
   (tie_id, leg_number, match_date, home_club_id, away_club_id,
    home_score, away_score, home_pens, away_pens, after_extra_time,
    venue, attendance, referee, notes)
   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""


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
        x.get("notes"),
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


def _editions_contested_by(club_key, edition_ids, seasons=None):
    """(lineage, season_label, edition_id) for editions where club_key actually played.

    Two lineages can share a season_label (e.g. "1960-61" for both the
    European Cup and the Cup Winners' Cup); matching by label alone would
    attribute a club's period name to a lineage it never entered that season.
    """
    result = []
    for s in (SEASONS if seasons is None else seasons):
        played = club_key in (s["winner"], s["runner_up"]) or any(
            club_key in (tie["t1"], tie["t2"])
            for rnd in s["rounds"] for tie in rnd["ties"]
        )
        if played:
            eid = edition_ids.get((s["lineage"], s["season_label"]))
            if eid is not None:
                result.append((s["lineage"], s["season_label"], eid))
    return result


def build(force=False, db_path=None):
    """Build the SQLite database. ``db_path`` defaults to ``european_football.db``.

    Tests pass a temporary path so they never assume a stale on-disk file.
    """
    db_path = db_path or DB_PATH
    if os.path.exists(db_path) and not force:
        print(f"Database already exists at {db_path}\nRe-run with --force to rebuild.")
        return 0

    # Build into a temporary sibling and only replace db_path once everything
    # (schema, inserts, verify()) has succeeded - a failed --force rebuild must
    # never leave the last known-good database deleted.
    tmp_path = db_path + ".tmp"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        schema_sql = fh.read()

    conn = sqlite3.connect(tmp_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    cur.executescript(schema_sql)

    # ---- clubs: insert only those actually referenced, fail on unknown keys --
    referenced = collect_referenced_keys()
    unknown = sorted(k for k in referenced if k not in CLUBS)
    if unknown:
        conn.close(); os.remove(tmp_path)
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
    # Insert every configured lineage, not just ones with a seeded edition -
    # otherwise a trophy line (e.g. Inter-Cities Fairs Cup) stays invisible
    # to the UI/CLI until its first season is added.
    seeded_names = dict.fromkeys(s["lineage"] for s in SEASONS)
    lineage_id = {}
    for name in list(LINEAGES) + [n for n in seeded_names if n not in LINEAGES]:
        note = LINEAGES.get(name, "")
        if name not in LINEAGES:
            print("WARNING: lineage %r has no LINEAGES entry; inserting with empty notes." % name)
        cur.execute("INSERT INTO lineage (name, notes) VALUES (?,?)", (name, note))
        lineage_id[name] = cur.lastrowid

    # ---- editions / rounds / ties / matches -------------------------------
    edition_ids = {}  # (lineage_name, season_label) -> edition_id
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
        edition_ids[(s["lineage"], s["season_label"])] = edition_id

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


    # ---- club_name_history (period-accurate display names) ----------------
    for entry in CLUB_NAME_HISTORY:
        key = entry["club"]
        if key not in club_id:
            # Club registered but unused in seeded seasons - skip quietly.
            continue
        season_label = entry.get("season_label")
        # Scope to editions the club actually contested that season, not just
        # any edition sharing the label - see _editions_contested_by.
        contested = _editions_contested_by(key, edition_ids)
        matched = [(lin, lab, eid) for (lin, lab, eid) in contested if lab == season_label]
        if matched:
            for _lin, lab, eid in matched:
                cur.execute(
                    """INSERT INTO club_name_history
                       (club_id, edition_id, season_label, name_used, notes)
                       VALUES (?,?,?,?,?)""",
                    (club_id[key], eid, lab, entry["name_used"], entry.get("notes")),
                )
        else:
            cur.execute(
                """INSERT INTO club_name_history
                   (club_id, edition_id, season_label, name_used, notes)
                   VALUES (?,?,?,?,?)""",
                (club_id[key], None, season_label, entry["name_used"], entry.get("notes")),
            )

    # ---- VERIFY before committing -----------------------------------------
    problems = verify(cur, club_id)
    if problems:
        conn.rollback(); conn.close(); os.remove(tmp_path)
        print("\n".join(problems))
        sys.exit(f"\nBUILD ABORTED: {len(problems)} data problem(s). "
                 f"{db_path} left untouched.")

    conn.commit()
    report(cur, db_path=db_path)
    conn.close()
    os.replace(tmp_path, db_path)  # atomic swap - only now does the old file go
    return 0


ALLOWED_SETTLEMENTS = {
    "aggregate", "away_goals", "replay", "penalties",
    "coin_toss", "single_match", "walkover", "bye",
}


def verify(cur, club_id, seasons=None):
    """Recompute each tie's aggregate from its legs and check settlement consistency.

    Beyond the aggregate/away-goals arithmetic, this also catches settlement
    shapes that don't match their decided_by: a one-leg "aggregate" (should be
    a walkover - see the Vorwarts-Linfield 1961-62 fix), a single_match with
    more than one leg, a replay/coin_toss missing its play-off leg, or a
    walkover/bye carrying legs or a missing winner.
    """
    problems = []
    for s in (SEASONS if seasons is None else seasons):
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                a, b = tie["t1"], tie["t2"]
                by, win, legs = tie["by"], tie["win"], tie["legs"]
                ga = gb = 0
                tag = f'{s["season_label"]} {rnd["name"]}: {a} v {b}'

                if by not in ALLOWED_SETTLEMENTS:
                    problems.append(f'!! BY   {tag}: unknown decided_by={by!r}')

                if win and win not in (a, b):
                    problems.append(f'!! WIN  {tag}: winner {win} is not {a} or {b}')

                for idx, leg in enumerate(legs):
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

                if by == "aggregate":
                    if len(legs) < 2:
                        problems.append(
                            f'!! LEGS {tag}: decided_by=aggregate but only {len(legs)} leg(s) '
                            f'(a withdrawal after one leg should be a walkover)')
                    winner = a if ga > gb else (b if gb > ga else None)
                    if winner != win:
                        problems.append(f'!! WIN  {tag}: higher aggregate is {winner}, data says {win}')

                elif by == "away_goals":
                    if ga != gb:
                        problems.append(
                            f'!! AG   {tag}: decided_by=away_goals but aggregate is {ga}-{gb}, not level')
                    else:
                        aa = ab = 0
                        for idx, leg in enumerate(legs):
                            if idx >= 2:
                                continue
                            h, aw, hs, as_, _ = leg_fields(leg)
                            if aw == a:
                                aa += as_
                            if aw == b:
                                ab += as_
                        winner = a if aa > ab else (b if ab > aa else None)
                        if winner != win:
                            problems.append(
                                f'!! AG   {tag}: away goals {aa}-{ab} imply {winner}, data says {win}')

                elif by == "single_match":
                    if len(legs) != 1:
                        problems.append(f'!! LEGS {tag}: single_match expects 1 leg, has {len(legs)}')
                    elif win:
                        h, aw, hs, as_, _ = leg_fields(legs[0])
                        scored_home = a if h == a else b
                        actual = (scored_home if hs > as_ else
                                  ((b if scored_home == a else a) if as_ > hs else None))
                        if actual and actual != win:
                            problems.append(
                                f'!! WIN  {tag}: single-match score implies {actual}, data says {win}')

                elif by in ("replay", "coin_toss"):
                    if len(legs) < 3:
                        problems.append(f'!! LEGS {tag}: {by} requires a play-off leg, has {len(legs)}')
                    elif by == "replay" and win:
                        h, aw, hs, as_, _ = leg_fields(legs[2])
                        if hs != as_:
                            po_home = a if h == a else b
                            actual = po_home if hs > as_ else (b if po_home == a else a)
                            if actual != win:
                                problems.append(
                                    f'!! WIN  {tag}: play-off score implies {actual}, data says {win}')

                elif by in ("walkover", "bye"):
                    if legs:
                        problems.append(f'!! LEGS {tag}: {by} should have 0 legs, has {len(legs)}')
                    if tie["agg"] is not None:
                        problems.append(f'!! AGG  {tag}: {by} should have agg=None')
                    if not win:
                        problems.append(f'!! WIN  {tag}: {by} has no declared winner')
    return problems


def report(cur, db_path=None):
    counts = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("lineage", "club", "club_name_history", "edition", "round", "tie", "match")}
    print(f"Built {db_path or DB_PATH}")
    print("  " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    print("  All aggregates verified against RSSSF printed totals.")
    for row in cur.execute("SELECT season_label, competition_name FROM edition ORDER BY start_year"):
        print(f"    - {row[1]} {row[0]}")


if __name__ == "__main__":
    sys.exit(build(force="--force" in sys.argv))
