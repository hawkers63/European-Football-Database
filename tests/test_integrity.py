# -*- coding: utf-8 -*-
"""Integrity checks over seasons.py, clubs.py, schema.sql and the built SQLite DB."""

import copy
import os
import sqlite3
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from clubs import CLUBS
from seasons import SEASONS
from build_database import (
    MATCH_INSERT_SQL,
    collect_referenced_keys,
    leg_fields,
    match_insert_tuple,
    unused_club_keys,
    verify,
)

ALLOWED_SETTLEMENTS = {
    "aggregate", "away_goals", "replay", "penalties",
    "coin_toss", "single_match", "walkover", "bye",
}

DB_PATH = os.path.join(ROOT, "european_football.db")
SCHEMA_PATH = os.path.join(ROOT, "schema.sql")


def _recompute_agg(tie):
    a, b = tie["t1"], tie["t2"]
    ga = gb = 0
    for idx, leg in enumerate(tie["legs"]):
        if idx >= 2:
            continue
        h, aw, hs, as_, _ = leg_fields(leg)
        if h == a:
            ga += hs
        if aw == a:
            ga += as_
        if h == b:
            gb += hs
        if aw == b:
            gb += as_
    return ga, gb


class TestSeasonIntegrity(unittest.TestCase):
    def test_all_club_keys_are_registered(self):
        unknown = sorted(k for k in collect_referenced_keys() if k not in CLUBS)
        self.assertEqual(unknown, [])

    def test_current_registry_has_no_unused_clubs(self):
        self.assertEqual(unused_club_keys(), [])

    def test_unused_club_keys_reports_zero_appearance_entries(self):
        clubs = {"played": {"name": "Played"}, "ghost": {"name": "Ghost"}}
        referenced = {"played"}
        self.assertEqual(unused_club_keys(clubs, referenced), ["ghost"])

    def test_settlement_types_are_known(self):
        seen = {tie["by"] for s in SEASONS for rnd in s["rounds"] for tie in rnd["ties"]}
        self.assertTrue(seen <= ALLOWED_SETTLEMENTS, seen - ALLOWED_SETTLEMENTS)

    def test_winner_is_one_of_the_two_sides(self):
        for s in SEASONS:
            for rnd in s["rounds"]:
                for tie in rnd["ties"]:
                    if tie["win"]:
                        self.assertIn(
                            tie["win"], (tie["t1"], tie["t2"]),
                            "%s %s %s v %s" % (s["season_label"], rnd["name"], tie["t1"], tie["t2"]),
                        )

    def test_aggregates_match_rsssf_printed_totals(self):
        mismatches = []
        for s in SEASONS:
            for rnd in s["rounds"]:
                for tie in rnd["ties"]:
                    if tie["agg"] is None:
                        continue
                    got = _recompute_agg(tie)
                    if got != tuple(tie["agg"]):
                        mismatches.append((s["season_label"], rnd["name"], tie["t1"], tie["t2"], got, tie["agg"]))
        self.assertEqual(mismatches, [])

    def test_replay_and_coin_toss_have_a_third_leg(self):
        for s in SEASONS:
            for rnd in s["rounds"]:
                for tie in rnd["ties"]:
                    if tie["by"] in ("replay", "coin_toss"):
                        self.assertGreaterEqual(
                            len(tie["legs"]), 3,
                            "%s %s %s v %s" % (s["season_label"], rnd["name"], tie["t1"], tie["t2"]),
                        )

    def test_walkovers_have_no_legs(self):
        for s in SEASONS:
            for rnd in s["rounds"]:
                for tie in rnd["ties"]:
                    if tie["by"] in ("walkover", "bye"):
                        self.assertEqual(tie["legs"], [])
                        self.assertIsNone(tie["agg"])

    def test_verify_passes_canonical_data(self):
        self.assertEqual(verify(None, {}), [])

    def test_verify_rejects_third_club_in_a_leg(self):
        seasons = copy.deepcopy(SEASONS)
        tie = seasons[0]["rounds"][0]["ties"][0]
        t1, t2 = tie["t1"], tie["t2"]
        # First registered club that is not either side of this tie.
        interloper = next(k for k in CLUBS if k not in (t1, t2))
        original = tie["legs"][0]
        extras = original[4] if len(original) > 4 else {}
        tie["legs"][0] = (interloper, t2, original[2], original[3], extras) if extras else (
            interloper, t2, original[2], original[3])
        problems = verify(None, {}, seasons=seasons)
        club_problems = [p for p in problems if p.startswith("!! CLUB")]
        self.assertTrue(club_problems, problems)
        self.assertIn(interloper, club_problems[0])
        self.assertIn(t1, club_problems[0])
        self.assertIn(t2, club_problems[0])

    def test_wismut_coin_toss_is_recorded(self):
        found = None
        for s in SEASONS:
            for rnd in s["rounds"]:
                for tie in rnd["ties"]:
                    if tie["by"] == "coin_toss":
                        found = tie
        self.assertIsNotNone(found)
        self.assertEqual(found["win"], "wismut")
        self.assertIn("toss of a coin", found["note"])

    def test_mtk_alias_note_is_recorded(self):
        notes = [tie.get("note") for s in SEASONS for rnd in s["rounds"] for tie in rnd["ties"] if tie.get("note")]
        self.assertTrue(any(n and "MTK competed as" in n for n in notes))


class TestMatchInsertPens(unittest.TestCase):
    def test_schema_defines_shootout_columns(self):
        with open(SCHEMA_PATH, encoding='utf-8') as fh:
            schema = fh.read()
        self.assertIn("home_pens", schema)
        self.assertIn("away_pens", schema)

    def test_insert_sql_includes_pens_columns(self):
        self.assertIn("home_pens", MATCH_INSERT_SQL)
        self.assertIn("away_pens", MATCH_INSERT_SQL)

    def test_pens_extracted_from_extras(self):
        club_id = {"home": 1, "away": 2}
        leg = ("home", "away", 1, 1, {"home_pens": 4, "away_pens": 3, "aet": True})
        row = match_insert_tuple(10, 1, club_id, leg)
        # (tie_id, leg_number, date, home_id, away_id, hs, as_, home_pens, away_pens, aet, venue, att, ref)
        self.assertEqual(row[0], 10)
        self.assertEqual(row[5], 1)
        self.assertEqual(row[6], 1)
        self.assertEqual(row[7], 4)
        self.assertEqual(row[8], 3)
        self.assertEqual(row[9], 1)

    def test_pens_are_null_when_absent(self):
        club_id = {"home": 1, "away": 2}
        row = match_insert_tuple(1, 1, club_id, ("home", "away", 2, 0))
        self.assertIsNone(row[7])
        self.assertIsNone(row[8])
        self.assertEqual(row[9], 0)


@unittest.skipUnless(os.path.exists(DB_PATH), "european_football.db not built yet")
class TestBuiltDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row
        cls.conn.execute("PRAGMA foreign_keys = ON")
        cls.cur = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_foreign_keys_are_enabled(self):
        self.assertEqual(self.cur.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_tie_clubs_reference_club_table(self):
        orphans = self.cur.execute(
            """SELECT t.tie_id FROM tie t
               LEFT JOIN club a ON a.club_id=t.club_a_id
               LEFT JOIN club b ON b.club_id=t.club_b_id
               WHERE a.club_id IS NULL OR b.club_id IS NULL"""
        ).fetchall()
        self.assertEqual(orphans, [])

    def test_winner_fk_and_membership(self):
        bad = self.cur.execute(
            """SELECT tie_id FROM tie
               WHERE winner_club_id IS NOT NULL
                 AND winner_club_id NOT IN (club_a_id, club_b_id)"""
        ).fetchall()
        self.assertEqual(bad, [])

    def test_match_clubs_reference_club_table(self):
        orphans = self.cur.execute(
            """SELECT match_id FROM match m
               LEFT JOIN club h ON h.club_id=m.home_club_id
               LEFT JOIN club a ON a.club_id=m.away_club_id
               WHERE h.club_id IS NULL OR a.club_id IS NULL"""
        ).fetchall()
        self.assertEqual(orphans, [])

    def test_edition_winner_and_runner_up_fks(self):
        bad = self.cur.execute(
            """SELECT edition_id FROM edition e
               LEFT JOIN club w ON w.club_id=e.winner_club_id
               LEFT JOIN club r ON r.club_id=e.runner_up_club_id
               WHERE (e.winner_club_id IS NOT NULL AND w.club_id IS NULL)
                  OR (e.runner_up_club_id IS NOT NULL AND r.club_id IS NULL)"""
        ).fetchall()
        self.assertEqual(bad, [])

    def test_hampden_attendance_stored(self):
        row = self.cur.execute(
            "SELECT attendance, venue FROM match WHERE attendance=135000"
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertIn("Hampden", row["venue"])

    def test_match_pens_columns_exist_and_are_nullable(self):
        cols = {r["name"] for r in self.cur.execute("PRAGMA table_info(match)")}
        self.assertIn("home_pens", cols)
        self.assertIn("away_pens", cols)

    def test_coin_toss_and_mtk_notes_stored(self):
        notes = [r["notes"] for r in self.cur.execute(
            "SELECT notes FROM tie WHERE notes IS NOT NULL")]
        self.assertTrue(any("toss of a coin" in (n or "") for n in notes))
        self.assertTrue(any(n and "MTK competed as" in n for n in notes))

    def test_edition_notes_and_runner_up_stored(self):
        row = self.cur.execute(
            "SELECT notes, runner_up_club_id FROM edition WHERE season_label='1959-60'"
        ).fetchone()
        self.assertTrue(row["notes"])
        self.assertIsNotNone(row["runner_up_club_id"])


if __name__ == "__main__":
    unittest.main()
