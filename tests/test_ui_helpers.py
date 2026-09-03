# -*- coding: utf-8 -*-
"""Unit tests for UI helper functions (aggregates, notes, attendance, layout)."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import app


class TestAttendance(unittest.TestCase):
    def test_hampden_format(self):
        self.assertEqual(app.format_attendance(135000), "135,000 spectators")

    def test_smaller_crowd(self):
        self.assertEqual(app.format_attendance(38239), "38,239 spectators")

    def test_missing(self):
        self.assertIsNone(app.format_attendance(None))
        self.assertIsNone(app.format_attendance(""))

    def test_included_in_match_extras(self):
        fragments = app.match_extra_fragments({
            "venue": "Hampden Park, Glasgow",
            "match_date": "1960-05-18",
            "referee": "Jack Mowat (Scotland)",
            "attendance": 135000,
        })
        self.assertEqual(fragments[0], "Hampden Park, Glasgow")
        self.assertIn("135,000 spectators", fragments)
        self.assertTrue(any(f.startswith("ref ") for f in fragments))

    def test_attendance_omitted_when_absent(self):
        fragments = app.match_extra_fragments({"venue": "Paris", "match_date": None,
                                              "referee": None, "attendance": None})
        self.assertEqual(fragments, ["Paris"])


class TestNotesNotShadowed(unittest.TestCase):
    def test_notes_kept_when_match_parts_exist(self):
        note = "MTK competed as V\u00f6r\u00f6s Lobog\u00f3 this season."
        detail, callout = app.compose_tie_detail(["MTK 6-3 Anderlecht"], note)
        self.assertIn("6-3", detail)
        self.assertEqual(callout, note)

    def test_wismut_coin_toss_note_survives_legs(self):
        note = "Wismut progressed on the toss of a coin after the play-off finished level."
        parts = ["Gwardia 3-1 Wismut", "Wismut 3-1 Gwardia"]
        detail, callout = app.compose_tie_detail(parts, note)
        self.assertTrue(detail)
        self.assertEqual(callout, note)

    def test_walkover_notes_still_surface(self):
        detail, callout = app.compose_tie_detail([], "KuPS Kuopio withdrew.")
        self.assertEqual(detail, "")
        self.assertEqual(callout, "KuPS Kuopio withdrew.")

    def test_empty_notes(self):
        detail, callout = app.compose_tie_detail(["A 1-0 B"], None)
        self.assertEqual(callout, "")
        self.assertEqual(detail, "A 1-0 B")


class TestScoreHeader(unittest.TestCase):
    def test_replay_shows_decider(self):
        legs = [
            {"leg_number": 1, "home_score": 4, "away_score": 3},
            {"leg_number": 2, "home_score": 2, "away_score": 1},
            {"leg_number": 3, "home_score": 7, "away_score": 0},
        ]
        self.assertEqual(app.format_score_header(5, 5, "replay", legs), "5-5 (Replay: 7-0)")

    def test_coin_toss_annotated(self):
        legs = [
            {"leg_number": 1, "home_score": 3, "away_score": 1},
            {"leg_number": 2, "home_score": 3, "away_score": 1},
            {"leg_number": 3, "home_score": 1, "away_score": 1},
        ]
        self.assertEqual(app.format_score_header(4, 4, "coin_toss", legs), "4-4 (Coin Toss)")

    def test_single_match_uses_spaced_dash(self):
        legs = [{"leg_number": 1, "home_score": 7, "away_score": 3}]
        self.assertEqual(app.format_score_header(7, 3, "single_match", legs), "7 - 3")

    def test_walkover_without_legs(self):
        self.assertEqual(app.format_score_header(0, 0, "walkover", []), "w/o")

    def test_plain_aggregate_unchanged(self):
        legs = [
            {"leg_number": 1, "home_score": 4, "away_score": 0},
            {"leg_number": 2, "home_score": 0, "away_score": 3},
        ]
        self.assertEqual(app.format_score_header(4, 3, "aggregate", legs), "4-3")


class TestMatchLine(unittest.TestCase):
    def test_aet_and_attendance(self):
        line = app.format_match_line("Real Madrid", "Milan", {
            "home_score": 3, "away_score": 2, "after_extra_time": 1,
            "venue": "Heysel Stadium, Brussels", "match_date": "1958-05-28",
            "referee": "Albert Dusch (West Germany)", "attendance": 67000,
        })
        self.assertIn("(aet)", line)
        self.assertIn("67,000 spectators", line)
        self.assertIn("Heysel Stadium, Brussels", line)


class TestChampionBanner(unittest.TestCase):
    def test_includes_runner_up(self):
        text = app.format_champion_banner("Real Madrid", "Eintracht Frankfurt")
        self.assertIn("Champions", text)
        self.assertIn("Real Madrid", text)
        self.assertIn("Runner-up", text)
        self.assertIn("Eintracht Frankfurt", text)

    def test_winner_only(self):
        text = app.format_champion_banner("Real Madrid", None)
        self.assertIn("Real Madrid", text)
        self.assertNotIn("Runner-up", text)


class TestWraplength(unittest.TestCase):
    def test_subtracts_padding(self):
        self.assertEqual(app.wraplength_for_width(708, padding=28), 680)

    def test_minimum_floor(self):
        self.assertEqual(app.wraplength_for_width(50, padding=28, minimum=200), 200)

    def test_bad_width(self):
        self.assertEqual(app.wraplength_for_width(None), 200)


class TestLayoutRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, 'app.py'), encoding='utf-8') as fh:
            cls.src = fh.read()

    def test_header_and_scroll_use_distinct_rows(self):
        self.assertIn('self.header.grid(row=0, column=1', self.src)
        self.assertIn('self.scroll.grid(row=1, column=1', self.src)
        self.assertNotIn('self.scroll.grid(row=0, column=1', self.src)

    def test_sidebar_spans_both_rows(self):
        self.assertIn("rowspan=2", self.src)

    def test_window_close_closes_connection(self):
        self.assertIn('self.protocol("WM_DELETE_WINDOW"', self.src)
        self.assertIn("self.conn.close()", self.src)

    def test_club_names_preloaded(self):
        self.assertIn("load_club_name_cache", self.src)


class TestClubCache(unittest.TestCase):
    def test_load_club_name_cache_shape(self):
        class FakeCursor:
            def execute(self, sql):
                return [{"club_id": 1, "name": "Real Madrid"},
                        {"club_id": 2, "name": "Reims"}]
        cache = app.load_club_name_cache(FakeCursor())
        self.assertEqual(cache[1], "Real Madrid")
        self.assertEqual(cache[2], "Reims")


if __name__ == "__main__":
    unittest.main()
