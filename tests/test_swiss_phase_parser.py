# -*- coding: utf-8 -*-
"""Swiss / league-phase parser: derived table, opponent shape, competition_transfer."""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.parse_swiss_phase import opponents_map, parse_swiss_phase, swiss_invariants
from tools.standings import DEFAULT_SWISS_TIEBREAK

FIXTURE = os.path.join(ROOT, "tools", "fixtures", "swiss_miniature.rsssf")

SHAPE8 = """
League phase
Matchday 1
Real Madrid              (1) 1  Milan                    (0) 0
Real Madrid              (0) 2  FC Barcelona             (0) 1
Real Madrid              (1) 1  SL Benfica               (0) 0
Real Madrid              (0) 3  RSC Anderlecht           (0) 0
Real Madrid              (1) 2  Panathinaikos            (0) 0
Real Madrid              (0) 1  Red Star (Belgrade)      (0) 0
Real Madrid              (1) 1  Hibernian                (0) 0
Real Madrid              (0) 2  Partizan                 (0) 1
Milan                    (0) 0  FC Barcelona             (0) 0
"""


class TestSwissPhaseParser(unittest.TestCase):
    def test_miniature_derived_table_and_transfer(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            text = fh.read()
        parsed = parse_swiss_phase(text, points_for_win=3)
        self.assertEqual(len(parsed["phases"]), 1)
        phase = parsed["phases"][0]
        self.assertEqual(phase["name"], "League phase")
        self.assertEqual(phase["phase_type"], "league")
        self.assertEqual(phase["problems"], [], phase["problems"])
        self.assertEqual(phase["computed_table"][0]["club"], "barcelona")
        self.assertEqual(phase["computed_table"][0]["pts"], 6)
        self.assertEqual(phase["computed_table"][1]["club"], "real_madrid")
        self.assertEqual(phase["computed_table"][1]["pts"], 4)
        self.assertEqual(len(parsed["transfers"]), 1)
        tr = parsed["transfers"][0]
        self.assertEqual(tr["club"], "benfica")
        self.assertEqual(tr["from_rank"], 3)
        self.assertEqual(tr["reason"], "league_phase_drop")
        self.assertIn("Europa", tr["to_competition"])

    def test_default_swiss_tiebreak_is_data(self):
        self.assertIn("opponent_points", DEFAULT_SWISS_TIEBREAK)
        self.assertIn("away_goals_scored", DEFAULT_SWISS_TIEBREAK)

    def test_eight_opponent_shape_helper(self):
        # Miniature does not enforce 36x8; helper only fires at expect_clubs=36.
        with open(FIXTURE, encoding="utf-8") as fh:
            text = fh.read()
        phase = parse_swiss_phase(text, points_for_win=3)["phases"][0]
        self.assertEqual(swiss_invariants(phase, expect_clubs=36), [])
        # Artificial 8-opponent check on a crafted club.
        matches = [
            {"home": "real_madrid", "away": c, "hs": 1, "as": 0}
            for c in ("milan", "barcelona", "benfica", "anderlecht",
                      "panathinaikos", "red_star", "hibernian", "partizan")
        ]
        opp = opponents_map(matches)
        self.assertEqual(len(opp["real_madrid"]), 8)
        fake = {
            "clubs": ["real_madrid"] + sorted(opp["real_madrid"]),
            "opponents": {k: sorted(v) for k, v in opp.items()},
        }
        # 9 clubs total, not 36 — invariants skipped.
        self.assertEqual(swiss_invariants(fake, expect_clubs=36), [])
        # When expect_clubs matches length, enforce eight opponents.
        fake["clubs"] = ["real_madrid"]  # wrong size vs expect
        # expect_clubs=1 would check real_madrid has 8 — craft properly:
        clubs = ["real_madrid"] + sorted(opp["real_madrid"])
        phase2 = {"clubs": clubs, "opponents": {k: sorted(v) for k, v in opp.items()}}
        problems = swiss_invariants(phase2, expect_clubs=len(clubs), expect_opponents=8)
        # real_madrid has 8; others have 1 each — expect problems for the others.
        self.assertTrue(any("opponents" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
