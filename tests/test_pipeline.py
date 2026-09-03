# -*- coding: utf-8 -*-
"""Away-goals verification and CLI smoke tests."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from build_database import verify


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


class TestCliHelp(unittest.TestCase):
    def test_cli_module_imports_and_parses_help(self):
        import cli
        with self.assertRaises(SystemExit) as ctx:
            cli.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()