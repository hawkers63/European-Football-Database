# -*- coding: utf-8 -*-
"""Cheap, display-free tests for the UI overhaul helpers."""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import app
from ui.data import (
    fetch_edition_payload,
    load_club_cache,
    map_feeders,
    organise_bracket_columns,
)
from ui.formatters import missing_database_message


class TestPensInMatchLine(unittest.TestCase):
    def test_pens_annotated(self):
        line = app.format_match_line("Fiorentina", "Rangers", {
            "home_score": 2, "away_score": 1,
            "after_extra_time": 0,
            "home_pens": 5, "away_pens": 4,
        })
        self.assertIn("pens 5-4", line)
        self.assertIn("Fiorentina", line)

    def test_pens_sit_beside_aet(self):
        line = app.format_match_line("A", "B", {
            "home_score": 1, "away_score": 1,
            "after_extra_time": 1,
            "home_pens": 3, "away_pens": 0,
        })
        self.assertIn("(aet)", line)
        self.assertIn("(pens 3-0)", line)

    def test_pens_omitted_when_absent(self):
        line = app.format_match_line("A", "B", {
            "home_score": 2, "away_score": 0,
        })
        self.assertNotIn("pens", line)


class TestMissingDatabasePath(unittest.TestCase):
    def test_helper_mentions_build_command(self):
        text = missing_database_message("C:/tmp/european_football.db")
        self.assertIn("european_football.db", text)
        self.assertIn("python build_database.py", text)

    def test_main_block_does_not_sys_exit_on_missing_db(self):
        with open(os.path.join(ROOT, "app.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn('sys.exit("european_football.db not found', src)
        self.assertIn("python build_database.py", src)
        self.assertIn("missing_database_message", src)
        self.assertIn("_build_missing_db", src)


class TestBracketHelpers(unittest.TestCase):
    def test_columns_follow_round_order_not_name(self):
        rounds = [
            {"round_order": 2, "name": "Qualifying", "ties": [
                {"tie_id": 2, "club_a_id": 1, "club_b_id": 2, "winner_club_id": 1},
            ]},
            {"round_order": 1, "name": "Final", "ties": [
                {"tie_id": 1, "club_a_id": 3, "club_b_id": 4, "winner_club_id": 3},
            ]},
        ]
        cols = organise_bracket_columns(rounds)
        self.assertEqual([c["round_order"] for c in cols], [1, 2])
        self.assertEqual(cols[0]["name"], "Final")

    def test_feeders_match_winners(self):
        r1 = {"round_order": 1, "name": "Semi-Finals", "ties": [
            {"tie_id": 1, "club_a_id": 1, "club_b_id": 2, "winner_club_id": 1},
            {"tie_id": 2, "club_a_id": 3, "club_b_id": 4, "winner_club_id": 3},
        ]}
        r2 = {"round_order": 2, "name": "Final", "ties": [
            {"tie_id": 3, "club_a_id": 1, "club_b_id": 3, "winner_club_id": 1},
        ]}
        cols = organise_bracket_columns([r1, r2])
        self.assertEqual(cols[1]["slots"][0]["feeders"], [0, 1])

    def test_missing_feeder_is_none(self):
        r1 = {"round_order": 1, "name": "Qualifying", "ties": [
            {"tie_id": 1, "club_a_id": 1, "club_b_id": 2, "winner_club_id": 1},
        ]}
        r2 = {"round_order": 2, "name": "Quarter-Finals", "ties": [
            {"tie_id": 2, "club_a_id": 1, "club_b_id": 9, "winner_club_id": 1},
        ]}
        cols = organise_bracket_columns([r1, r2])
        self.assertEqual(cols[1]["slots"][0]["feeders"][0], 0)
        self.assertIsNone(cols[1]["slots"][0]["feeders"][1])

    def test_four_and_five_round_lengths(self):
        def dummy(n):
            return [
                {"round_order": i, "name": "Round-%s" % i, "ties": [
                    {"tie_id": i, "club_a_id": i, "club_b_id": i + 10,
                     "winner_club_id": i},
                ]}
                for i in range(1, n + 1)
            ]
        self.assertEqual(len(organise_bracket_columns(dummy(4))), 4)
        self.assertEqual(len(organise_bracket_columns(dummy(5))), 5)

    def test_map_feeders_tolerates_empty_previous(self):
        mapped, leftovers = map_feeders([], [
            {"tie_id": 1, "club_a_id": 1, "club_b_id": 2, "winner_club_id": 1},
        ])
        self.assertEqual(len(mapped), 1)
        self.assertIsNone(mapped[0]["feeder_a"])
        self.assertEqual(leftovers, [])


class TestDisplayNameCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = os.path.join(ROOT, "european_football.db")
        if not os.path.exists(cls.db):
            raise unittest.SkipTest("european_football.db is not built")
        cls.conn = app.connect(cls.db)
        cls.cur = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_cache_matches_get_club_display_name(self):
        from queries import get_club_display_name
        editions = [r["edition_id"] for r in self.cur.execute(
            "SELECT edition_id FROM edition ORDER BY edition_id")]
        self.assertTrue(editions)
        for eid in editions:
            cache = load_club_cache(self.cur, edition_id=eid)
            sample = list(cache)[:12]
            for cid in sample:
                expected = get_club_display_name(self.cur, cid, eid)
                self.assertEqual(
                    cache[cid]["display_name"], expected,
                    "edition %s club %s" % (eid, cid))

    def test_mtk_1955_is_period_accurate(self):
        from queries import get_club_display_name
        row = self.cur.execute(
            "SELECT club_id FROM club WHERE name LIKE 'MTK%'").fetchone()
        self.assertIsNotNone(row)
        club_id = row[0]
        eid = self.cur.execute(
            "SELECT edition_id FROM edition WHERE season_label='1955-56'"
        ).fetchone()[0]
        cache = load_club_cache(self.cur, edition_id=eid)
        used = get_club_display_name(self.cur, club_id, eid)
        self.assertEqual(cache[club_id]["display_name"], used)
        self.assertIn("Lobog", used)

    def test_payload_attaches_matches_and_stops_n_plus_one_shape(self):
        eid = self.cur.execute(
            "SELECT edition_id FROM edition ORDER BY edition_id LIMIT 1"
        ).fetchone()[0]
        payload = fetch_edition_payload(self.cur, eid)
        self.assertIn("rounds", payload)
        self.assertTrue(payload["rounds"])
        for rnd in payload["rounds"]:
            for tie in rnd["ties"]:
                self.assertIn("matches", tie)
                self.assertIn("aggregate", tie)
        self.assertGreater(payload["match_count"], 0)
        self.assertGreater(payload["goal_count"], 0)

    def test_every_seeded_edition_has_bracket_columns(self):
        rows = list(self.cur.execute(
            "SELECT edition_id, season_label FROM edition ORDER BY edition_id"))
        self.assertGreaterEqual(len(rows), 7)
        for row in rows:
            payload = fetch_edition_payload(self.cur, row[0])
            cols = organise_bracket_columns(payload["rounds"])
            self.assertEqual(len(cols), len(payload["rounds"]))
            self.assertEqual(
                [c["round_order"] for c in cols],
                [r["round_order"] for r in payload["rounds"]],
            )


class TestLayoutSourceStillPinned(unittest.TestCase):
    def test_overhaul_keeps_helper_layout_pins(self):
        with open(os.path.join(ROOT, "app.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("load_club_name_cache", src)
        self.assertIn('self.header.grid(row=0, column=1', src)
        self.assertIn('self.scroll.grid(row=1, column=1', src)
        self.assertIn("rowspan=2", src)
        self.assertIn('self.protocol("WM_DELETE_WINDOW"', src)
        self.assertIn("self.conn.close()", src)


if __name__ == "__main__":
    unittest.main()
