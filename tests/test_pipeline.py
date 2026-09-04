# -*- coding: utf-8 -*-
"""Away-goals verification and CLI smoke tests."""

import os
import sqlite3
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from build_database import verify

DB_PATH = os.path.join(ROOT, "european_football.db")


class TestAwayGoalsVerify(unittest.TestCase):
    def _season(self, tie):
        return [{
            "lineage": "European Cup", "season_label": "1965-66", "start_year": 1965,
            "competition_name": "European Cup",
            "winner": "a", "runner_up": "b", "away_goals_active": True,
            "rounds": [{"name": "R", "ties": [tie]}],
        }]

    def test_away_goals_accepts_side_with_more_away_goals(self):
        tie = {
            "t1": "a", "t2": "b", "win": "b", "by": "away_goals", "agg": (1, 1),
            "legs": [("a", "b", 1, 1), ("b", "a", 0, 0)],
        }
        self.assertEqual(verify(None, {}, seasons=self._season(tie)), [])

    def test_away_goals_rejects_wrong_winner(self):
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "away_goals", "agg": (1, 1),
            "legs": [("a", "b", 1, 1), ("b", "a", 0, 0)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("AG" in p or "AWAY" in p for p in problems), problems)

    def test_away_goals_rejects_unequal_aggregates(self):
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "away_goals", "agg": (2, 1),
            "legs": [("a", "b", 2, 0), ("b", "a", 1, 0)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("AG" in p or "AWAY" in p for p in problems), problems)

    def _season_flag_off(self, tie):
        return [{
            "lineage": "European Cup", "season_label": "1955-56", "start_year": 1955,
            "competition_name": "European Cup",
            "winner": "a", "runner_up": "b", "away_goals_active": False,
            "rounds": [{"name": "R", "ties": [tie]}],
        }]

    def test_away_goals_rejected_when_edition_flag_is_false(self):
        """The away-goals rule wasn't introduced until 1965-66 - a Classic
        Era edition (away_goals_active=False) must not settle a tie by it."""
        tie = {
            "t1": "a", "t2": "b", "win": "b", "by": "away_goals", "agg": (1, 1),
            "legs": [("a", "b", 1, 1), ("b", "a", 0, 0)],
        }
        problems = verify(None, {}, seasons=self._season_flag_off(tie))
        self.assertTrue(any("away_goals_active=False" in p for p in problems), problems)

    def test_away_goals_accepted_when_edition_flag_is_true(self):
        tie = {
            "t1": "a", "t2": "b", "win": "b", "by": "away_goals", "agg": (1, 1),
            "legs": [("a", "b", 1, 1), ("b", "a", 0, 0)],
        }
        self.assertEqual(verify(None, {}, seasons=self._season(tie)), [])


class TestSettlementShapeVerify(unittest.TestCase):
    """Fix A: decided_by must match the legs actually present."""

    def _season(self, tie):
        return [{
            "lineage": "European Cup", "season_label": "1965-66", "start_year": 1965,
            "competition_name": "European Cup",
            "winner": "a", "runner_up": "b", "away_goals_active": True,
            "rounds": [{"name": "R", "ties": [tie]}],
        }]

    def test_one_leg_aggregate_is_rejected(self):
        """The exact Vorwarts-Linfield shape before it was fixed to a walkover."""
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "aggregate", "agg": (3, 0),
            "legs": [("a", "b", 3, 0)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("LEGS" in p and "aggregate" in p for p in problems), problems)

    def test_two_leg_aggregate_is_accepted(self):
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "aggregate", "agg": (3, 1),
            "legs": [("a", "b", 2, 0), ("b", "a", 1, 1)],
        }
        self.assertEqual(verify(None, {}, seasons=self._season(tie)), [])

    def test_single_match_with_two_legs_is_rejected(self):
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "single_match", "agg": (2, 2),
            "legs": [("a", "b", 1, 1), ("b", "a", 1, 1)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("single_match" in p for p in problems), problems)

    def test_single_match_score_must_imply_winner(self):
        tie = {
            "t1": "a", "t2": "b", "win": "b", "by": "single_match", "agg": (2, 0),
            "legs": [("a", "b", 2, 0)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("single-match score implies" in p for p in problems), problems)

    def test_replay_without_playoff_leg_is_rejected(self):
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "replay", "agg": (2, 2),
            "legs": [("a", "b", 1, 1), ("b", "a", 1, 1)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("requires a play-off leg" in p for p in problems), problems)

    def test_replay_playoff_score_must_imply_winner(self):
        tie = {
            "t1": "a", "t2": "b", "win": "b", "by": "replay", "agg": (2, 2),
            "legs": [("a", "b", 1, 1), ("b", "a", 1, 1), ("a", "b", 2, 0)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("play-off score implies" in p for p in problems), problems)

    def test_single_match_final_replayed_is_accepted(self):
        """A one-off final drawn and replayed outright (no two real legs, so
        agg=None) - the CWC 1961-62 final shape: Atletico Madrid 1-1 aet
        Fiorentina, replay Atletico Madrid 3-0 Fiorentina."""
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "replay", "agg": None,
            "legs": [("a", "b", 1, 1), ("a", "b", 3, 0)],
        }
        self.assertEqual(verify(None, {}, seasons=self._season(tie)), [])

    def test_single_match_final_replay_wrong_leg_count_is_rejected(self):
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "replay", "agg": None,
            "legs": [("a", "b", 1, 1)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("expects exactly 2 legs" in p for p in problems), problems)

    def test_single_match_final_replay_score_must_imply_winner(self):
        tie = {
            "t1": "a", "t2": "b", "win": "b", "by": "replay", "agg": None,
            "legs": [("a", "b", 1, 1), ("a", "b", 3, 0)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("replay score implies" in p for p in problems), problems)

    def test_walkover_with_legs_is_rejected(self):
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "walkover", "agg": None,
            "legs": [("a", "b", 3, 0)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("should have 0 legs" in p for p in problems), problems)

    def test_walkover_without_winner_is_rejected(self):
        tie = {
            "t1": "a", "t2": "b", "win": None, "by": "walkover", "agg": None,
            "legs": [],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("no declared winner" in p for p in problems), problems)

    def test_walkover_zero_legs_no_agg_with_winner_is_accepted(self):
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "walkover", "agg": None,
            "legs": [],
        }
        self.assertEqual(verify(None, {}, seasons=self._season(tie)), [])

    def test_unknown_settlement_type_is_rejected(self):
        tie = {
            "t1": "a", "t2": "b", "win": "a", "by": "extra_time", "agg": (2, 1),
            "legs": [("a", "b", 2, 1)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("unknown decided_by" in p for p in problems), problems)

    def test_winner_must_be_one_of_the_two_clubs(self):
        tie = {
            "t1": "a", "t2": "b", "win": "c", "by": "single_match", "agg": (1, 0),
            "legs": [("a", "b", 1, 0)],
        }
        problems = verify(None, {}, seasons=self._season(tie))
        self.assertTrue(any("is not a or b" in p for p in problems), problems)


class TestCliHelp(unittest.TestCase):
    def test_cli_module_imports_and_parses_help(self):
        import cli
        with self.assertRaises(SystemExit) as ctx:
            cli.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


@unittest.skipUnless(os.path.exists(DB_PATH), "european_football.db not built yet")
class TestCmdSeasonLegDisplay(unittest.TestCase):
    """cmd_season()'s per-leg loop reused one cursor with get_club_display_name()
    inside it, the same bug already fixed in _export_edition() - it silently
    printed only "L1" for every tie regardless of how many legs it had."""

    def test_three_leg_replay_prints_all_three_legs(self):
        import io
        from contextlib import redirect_stdout
        import cli

        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(["season", "1955-58"])
        text = out.getvalue()
        # Birmingham City v Barcelona semi-final: two legs plus a play-off.
        start = text.index("Birmingham City vs")
        end = text.index("\n\n", start)
        block = text[start:end]
        self.assertIn("L1:", block)
        self.assertIn("L2:", block)
        self.assertIn("L3:", block)


@unittest.skipUnless(os.path.exists(DB_PATH), "european_football.db not built yet")
class TestCmdPathAndChronology(unittest.TestCase):
    def _run(self, argv):
        import io
        from contextlib import redirect_stdout
        import cli

        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(argv)
        return out.getvalue()

    def test_path_prints_full_campaign_in_round_order(self):
        text = self._run(["path", "benfica", "1961-62"])
        self.assertLess(
            text.index("First Round"), text.index("Quarter-Finals"))
        self.assertLess(
            text.index("Quarter-Finals"), text.index("Semi-Finals"))
        # "Final" is a substring of "Semi-Finals", so anchor on the distinct
        # "[WON ] Final" round header instead.
        self.assertLess(text.index("Semi-Finals"), text.index("] Final ("))
        self.assertIn("Real Madrid", text)

    def test_path_includes_walkover_with_no_score_line(self):
        text = self._run(["path", "eintracht", "1959-60"])
        self.assertIn("[walkover]", text)
        self.assertIn("withdrew", text)

    def test_path_unknown_season_exits_with_message(self):
        with self.assertRaises(SystemExit):
            self._run(["path", "benfica", "1899-00"])

    def test_chronology_prints_dated_footer(self):
        text = self._run(["chronology", "1961-62"])
        self.assertIn("matches dated", text)
        self.assertIn("European Cup", text)
        self.assertIn("European Cup Winners' Cup", text)

    def test_chronology_unknown_season_exits_with_message(self):
        with self.assertRaises(SystemExit):
            self._run(["chronology", "1899-00"])

    def test_leaderboard_wins_and_gd_print_the_matches_table(self):
        for kind in ("wins", "gd"):
            text = self._run(["leaderboard", kind, "--limit", "3"])
            self.assertIn("Played", text)
            self.assertIn("GD", text)


@unittest.skipUnless(os.path.exists(DB_PATH), "european_football.db not built yet")
class TestExportEdition(unittest.TestCase):
    """_export_edition() used to reuse one cursor across nested loops and the
    get_club_display_name() lookups inside them, silently truncating results -
    these lock in the real round/tie/match counts per edition."""

    @classmethod
    def setUpClass(cls):
        from cli import _export_edition
        cls._export_edition = staticmethod(_export_edition)
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row
        cls.cur = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def _counts(self, payload):
        rounds = payload["rounds"]
        ties = sum(len(r["ties"]) for r in rounds)
        matches = sum(len(t["legs"]) for r in rounds for t in r["ties"])
        return len(rounds), ties, matches

    def test_1955_56_exports_all_rounds_ties_and_matches(self):
        eid = self.cur.execute(
            "SELECT edition_id FROM edition WHERE season_label = '1955-56'"
        ).fetchone()["edition_id"]
        payload = self._export_edition(self.cur, eid)
        self.assertEqual(self._counts(payload), (4, 15, 29))

    def test_two_lineages_in_1960_61_both_export_in_full(self):
        editions = self.cur.execute(
            "SELECT edition_id, competition_name FROM edition WHERE season_label = '1960-61'"
        ).fetchall()
        self.assertEqual(len(editions), 2)
        by_name = {}
        for row in editions:
            payload = self._export_edition(self.cur, row["edition_id"])
            by_name[row["competition_name"]] = self._counts(payload)
        self.assertEqual(by_name["European Cup"], (5, 27, 51))
        self.assertEqual(by_name["European Cup Winners' Cup"], (4, 9, 18))

    def test_exported_leg_includes_notes_key(self):
        eid = self.cur.execute(
            "SELECT edition_id FROM edition WHERE season_label = '1955-56'"
        ).fetchone()["edition_id"]
        payload = self._export_edition(self.cur, eid)
        leg = payload["rounds"][0]["ties"][0]["legs"][0]
        self.assertIn("notes", leg)


if __name__ == "__main__":
    unittest.main()