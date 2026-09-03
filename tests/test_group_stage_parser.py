# -*- coding: utf-8 -*-
"""Group-stage parser tests: points-for-win flag, ordering, incomplete, walkovers."""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.parse_group_stage import parse_group_stage
from tools.standings import rank_table, tables_match

FIXTURE = os.path.join(ROOT, "tools", "fixtures", "cl_1991_92_groups.rsssf")

INCOMPLETE = """
Group X
Real Madrid              (1) 2  Milan                    (0) 1
FC Barcelona             (0) 0  SL Benfica               (0) 0
# Real Madrid v Benfica not yet played

                           P  W  D  L  F  A Pts
REAL MADRID                1  1  0  0  2  1  3
FC BARCELONA               1  0  1  0  0  0  1
SL Benfica                 1  0  1  0  0  0  1
Milan                      1  0  0  1  1  2  0
"""

WALKOVER = """
Group Y
Real Madrid              (0) 3  Milan                    (0) 0  awarded walkover
FC Barcelona             (1) 1  SL Benfica               (0) 0

                           P  W  D  L  F  A Pts
REAL MADRID                1  1  0  0  3  0  3
FC BARCELONA               1  1  0  0  1  0  3
SL Benfica                 1  0  0  1  0  1  0
Milan                      1  0  0  1  0  3  0
"""


class TestGroupStageParser(unittest.TestCase):
    def test_1991_92_fixture_two_points_for_win(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            text = fh.read()
        parsed = parse_group_stage(text, points_for_win=2)
        self.assertEqual(len(parsed["groups"]), 2)
        names = [g["name"] for g in parsed["groups"]]
        self.assertEqual(names, ["Group A", "Group B"])
        for g in parsed["groups"]:
            self.assertEqual(g["problems"], [], g["problems"])
            self.assertEqual(g["unmatched"], [], g["unmatched"])
            self.assertEqual(len(g["clubs"]), 4)
            self.assertEqual(len(g["matches"]), 12)
            # 2 pts/win: leaders have 8 (Sampdoria) and 9 (Barcelona)
            self.assertEqual(g["computed_table"][0]["pts"], g["printed_table"][0]["pts"])
        self.assertEqual(parsed["groups"][0]["computed_table"][0]["club"], "sampdoria")
        self.assertEqual(parsed["groups"][0]["computed_table"][0]["pts"], 8)
        self.assertEqual(parsed["groups"][1]["computed_table"][0]["club"], "barcelona")
        self.assertEqual(parsed["groups"][1]["computed_table"][0]["pts"], 9)

    def test_three_points_flag_changes_ordering_math(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            text = fh.read()
        # Same fixtures with 3 pts/win disagree with the printed 2-pt table.
        parsed = parse_group_stage(text, points_for_win=3)
        self.assertTrue(parsed["groups"][0]["problems"])
        # Sampdoria would have 11 pts at 3-for-a-win (3W*3 + 2D).
        self.assertEqual(parsed["groups"][0]["computed_table"][0]["pts"], 11)

    def test_incomplete_group_marks_unplayed(self):
        parsed = parse_group_stage(INCOMPLETE, points_for_win=3)
        g = parsed["groups"][0]
        # Only two played matches; incomplete counts remain on rows that lack fixtures.
        self.assertEqual(len(g["matches"]), 2)
        # Computed table still ranks from played fixtures.
        self.assertEqual(g["computed_table"][0]["club"], "real_madrid")
        self.assertEqual(g["computed_table"][0]["pts"], 3)

    def test_awarded_walkover_counts(self):
        parsed = parse_group_stage(WALKOVER, points_for_win=3)
        g = parsed["groups"][0]
        self.assertTrue(any(m.get("awarded") for m in g["matches"]))
        self.assertEqual(g["problems"], [], g["problems"])
        row = next(r for r in g["computed_table"] if r["club"] == "real_madrid")
        self.assertEqual(row["gf"], 3)
        self.assertEqual(row["pts"], 3)

    def test_rank_table_never_infers_year(self):
        clubs = ["a", "b"]
        matches = [{"home": "a", "away": "b", "hs": 1, "as": 0}]
        two = rank_table(clubs, matches, 2)
        three = rank_table(clubs, matches, 3)
        self.assertEqual(two[0]["pts"], 2)
        self.assertEqual(three[0]["pts"], 3)
        with self.assertRaises(ValueError):
            rank_table(clubs, matches, 4)


if __name__ == "__main__":
    unittest.main()
