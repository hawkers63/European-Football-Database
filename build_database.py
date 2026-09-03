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

from clubs import CLUBS, CLUB_NAME_HISTORY
from lineages import LINEAGES
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
            for tie in rnd.get("ties") or []:
                keys.add(tie["t1"]); keys.add(tie["t2"])
                if tie["win"]:
                    keys.add(tie["win"])
                for leg in tie["legs"]:
                    h, a, _, _, _ = leg_fields(leg)
                    keys.add(h); keys.add(a)
            for group in rnd.get("groups") or []:
                for k in group.get("clubs") or []:
                    keys.add(k)
                for m in group.get("matches") or []:
                    if m.get("home"):
                        keys.add(m["home"])
                    if m.get("away"):
                        keys.add(m["away"])
                    if m.get("walkover_winner"):
                        keys.add(m["walkover_winner"])
        for tr in s.get("transfers") or []:
            if tr.get("club"):
                keys.add(tr["club"])
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
        note = LINEAGES.get(name, "")
        if name not in LINEAGES:
            print("WARNING: lineage %r has no LINEAGES entry; inserting with empty notes." % name)
        cur.execute("INSERT INTO lineage (name, notes) VALUES (?,?)", (name, note))
        lineage_id[name] = cur.lastrowid

    # ---- editions / rounds / ties / matches -------------------------------
    edition_ids = {}  # (lineage_name, season_label) -> edition_id
    round_ids = {}    # (lineage_name, season_label, round_name) -> round_id
    for s in SEASONS:
        cur.execute(
            """INSERT INTO edition
               (lineage_id, season_label, start_year, competition_name,
                winner_club_id, runner_up_club_id, away_goals_active, notes,
                points_for_win, standings_tiebreak)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (lineage_id[s["lineage"]], s["season_label"], s["start_year"],
             s["competition_name"],
             club_id.get(s["winner"]), club_id.get(s["runner_up"]),
             1 if s["away_goals_active"] else 0, s.get("notes"),
             s.get("points_for_win"), s.get("standings_tiebreak")))
        edition_id = cur.lastrowid
        edition_ids[(s["lineage"], s["season_label"])] = edition_id

        for order, rnd in enumerate(s["rounds"], start=1):
            phase_type = rnd.get("phase_type") or "knockout"
            cur.execute(
                "INSERT INTO round (edition_id, name, round_order, phase_type) VALUES (?,?,?,?)",
                (edition_id, rnd["name"], order, phase_type))
            round_id = cur.lastrowid
            round_ids[(s["lineage"], s["season_label"], rnd["name"])] = round_id

            insert_standing_groups(cur, club_id, round_id, rnd)

            for tie in rnd.get("ties") or []:
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
        # Prefer an edition of the same season_label (any lineage); if several,
        # insert one row per matching edition so display works in each.
        matched = [(lin, lab, eid) for (lin, lab), eid in edition_ids.items()
                   if lab == season_label]
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

    # ---- competition_transfer (mid-season movement between trophy lines)
    for s in SEASONS:
        from_eid = edition_ids[(s["lineage"], s["season_label"])]
        for tr in s.get("transfers") or []:
            to_lin = tr.get("to_lineage")
            to_lab = tr.get("to_season_label") or s["season_label"]
            to_eid = edition_ids.get((to_lin, to_lab)) if to_lin else None
            if to_eid is None:
                print("WARNING: skipping transfer %s; destination edition not seeded (%s %s)."
                      % (tr.get("club"), to_lin, to_lab))
                continue
            from_rid = round_ids.get((s["lineage"], s["season_label"], tr["from_round"])) if tr.get("from_round") else None
            to_rid = round_ids.get((to_lin, to_lab, tr["to_round"])) if tr.get("to_round") else None
            cur.execute(
                """INSERT INTO competition_transfer
                   (club_id, from_edition_id, from_round_id, from_rank,
                    to_edition_id, to_round_id, reason, notes)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (club_id[tr["club"]], from_eid, from_rid, tr.get("from_rank"),
                 to_eid, to_rid, tr.get("reason") or "group_third", tr.get("notes")))

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


def insert_standing_groups(cur, club_id, round_id, rnd):
    """Persist additive group / league-phase rows for one round."""
    for order, group in enumerate(rnd.get("groups") or [], start=1):
        cur.execute(
            "INSERT INTO standing_group (round_id, name, group_order) VALUES (?,?,?)",
            (round_id, group["name"], order))
        group_id = cur.lastrowid
        members = list(group.get("clubs") or [])
        for m in group.get("matches") or []:
            for k in (m.get("home"), m.get("away")):
                if k and k not in members:
                    members.append(k)
        for key in members:
            cur.execute(
                "INSERT INTO standing_member (group_id, club_id) VALUES (?,?)",
                (group_id, club_id[key]))
        for m in group.get("matches") or []:
            if not m.get("home") or not m.get("away"):
                continue
            walkover_id = club_id.get(m["walkover_winner"]) if m.get("walkover_winner") else None
            cur.execute(
                """INSERT INTO standing_match
                   (group_id, matchday, match_date, home_club_id, away_club_id,
                    home_score, away_score, awarded, walkover_winner_id,
                    venue, attendance, referee, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (group_id, m.get("matchday"), m.get("date"),
                 club_id[m["home"]], club_id[m["away"]],
                 m.get("hs"), m.get("as"),
                 1 if m.get("awarded") else 0, walkover_id,
                 m.get("venue"), m.get("att"), m.get("ref"), m.get("note")))


def verify_standings(season):
    """Check printed group tables against fixtures using the edition flag."""
    from tools.standings import rank_table, tables_match
    problems = []
    pf = season.get("points_for_win")
    tb = season.get("standings_tiebreak")
    for rnd in season["rounds"]:
        groups = rnd.get("groups") or []
        if not groups:
            continue
        if pf not in (2, 3):
            problems.append(
                "!! PTS  %s %s: group/league phase requires points_for_win 2 or 3 (got %r)"
                % (season["season_label"], rnd["name"], pf))
            continue
        for group in groups:
            clubs = list(group.get("clubs") or [])
            matches = group.get("matches") or []
            for m in matches:
                if m.get("hs") is None or m.get("as") is None:
                    continue
                if m.get("home") not in clubs or m.get("away") not in clubs:
                    problems.append(
                        "!! GRP  %s %s %s: %s v %s not in group clubs"
                        % (season["season_label"], rnd["name"], group["name"],
                           m.get("home"), m.get("away")))
            computed = rank_table(clubs, matches, pf, tb)
            printed = group.get("table") or []
            if printed:
                tag = "%s %s %s" % (season["season_label"], rnd["name"], group["name"])
                for msg in tables_match(computed, printed):
                    problems.append("!! TABLE %s: %s" % (tag, msg))
    return problems


def verify(cur, club_id, seasons=None):
    """Recompute each tie's aggregate from its legs and check it against `agg`.

    Group / league-phase tables are checked against printed standings when
    supplied. Classic Era knockout seasons have no groups and are unchanged.
    """
    problems = []
    for s in (SEASONS if seasons is None else seasons):
        problems.extend(verify_standings(s))
        for rnd in s["rounds"]:
            for tie in rnd.get("ties") or []:
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
                if tie["by"] == "away_goals":
                    if ga != gb:
                        problems.append(
                            f'!! AG   {tag}: decided_by=away_goals but aggregate is {ga}-{gb}, not level')
                    else:
                        aa = ab = 0
                        for idx, leg in enumerate(tie["legs"]):
                            if idx >= 2:
                                continue
                            h, aw, hs, as_, _ = leg_fields(leg)
                            if aw == a:
                                aa += as_
                            if aw == b:
                                ab += as_
                        winner = a if aa > ab else (b if ab > aa else None)
                        if winner != tie["win"]:
                            problems.append(
                                f'!! AG   {tag}: away goals {aa}-{ab} imply {winner}, data says {tie["win"]}')
    return problems


def report(cur):
    counts = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("lineage", "club", "club_name_history", "edition", "round", "tie", "match",
                        "standing_group", "standing_member", "standing_match", "competition_transfer")}
    print(f"Built {DB_PATH}")
    print("  " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    print("  All aggregates verified against RSSSF printed totals.")
    for row in cur.execute("SELECT season_label, competition_name FROM edition ORDER BY start_year"):
        print(f"    - {row[1]} {row[0]}")


if __name__ == "__main__":
    sys.exit(build(force="--force" in sys.argv))
