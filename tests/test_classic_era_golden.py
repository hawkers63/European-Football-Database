# -*- coding: utf-8 -*-
"""Lock Classic Era European Cup 1955-56..1959-60 golden facts.

Does not mutate seasons.py. Champions, runners-up and the Hampden Park
attendance of 135000 must stay exactly as seeded.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from seasons import SEASONS

DB_PATH = os.path.join(ROOT, "european_football.db")

CLASSIC = [
    ("1955-56", "real_madrid", "reims"),
    ("1956-57", "real_madrid", "fiorentina"),
    ("1957-58", "real_madrid", "milan"),
    ("1958-59", "real_madrid", "reims"),
    ("1959-60", "real_madrid", "eintracht"),
]


class TestClassicEraGoldenSeasons(unittest.TestCase):
    def _classic(self):
        by_label = {s["season_label"]: s for s in SEASONS
                    if s["lineage"] == "European Cup" and 1955 <= s["start_year"] <= 1959}
        return by_label

    def test_five_real_madrid_titles(self):
        by_label = self._classic()
        self.assertEqual(sorted(by_label), [c[0] for c in CLASSIC])
        for label, winner, runner in CLASSIC:
            s = by_label[label]
            self.assertEqual(s["winner"], winner, label)
            self.assertEqual(s["runner_up"], runner, label)
            self.assertNotIn("points_for_win", s)  # knockout-only; NULL at build
            self.assertTrue(all((rnd.get("phase_type") or "knockout") == "knockout"
                                for rnd in s["rounds"]))

    def test_hampden_135000_in_seed_data(self):
        s = self._classic()["1959-60"]
        found = False
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                for leg in tie["legs"]:
                    extras = leg[4] if len(leg) > 4 else {}
                    if extras.get("att") == 135000:
                        found = True
                        self.assertIn("Hampden", extras.get("venue") or "")
        self.assertTrue(found, "1959-60 final attendance 135000 missing from seasons.py")

    def test_no_groups_on_classic_rounds(self):
        for label, _, _ in CLASSIC:
            s = self._classic()[label]
            for rnd in s["rounds"]:
                self.assertFalse(rnd.get("groups"))


@unittest.skipUnless(os.path.exists(DB_PATH), "european_football.db not built yet")
class TestClassicEraGoldenDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_db_champions_and_hampden(self):
        rows = self.conn.execute(
            """SELECT e.season_label, w.name AS winner, r.name AS runner_up
               FROM edition e
               JOIN lineage l ON l.lineage_id = e.lineage_id
               JOIN club w ON w.club_id = e.winner_club_id
               JOIN club r ON r.club_id = e.runner_up_club_id
               WHERE l.name = 'European Cup' AND e.start_year BETWEEN 1955 AND 1959
               ORDER BY e.start_year"""
        ).fetchall()
        self.assertEqual(
            [(row["season_label"], row["winner"], row["runner_up"]) for row in rows],
            [
                ("1955-56", "Real Madrid", "Stade de Reims"),
                ("1956-57", "Real Madrid", "Fiorentina"),
                ("1957-58", "Real Madrid", "Milan"),
                ("1958-59", "Real Madrid", "Stade de Reims"),
                ("1959-60", "Real Madrid", "Eintracht Frankfurt"),
            ],
        )
        for row in rows:
            # Classic editions keep points_for_win NULL.
            pf = self.conn.execute(
                "SELECT points_for_win FROM edition WHERE season_label=?",
                (row["season_label"],),
            ).fetchone()[0]
            self.assertIsNone(pf)
        ham = self.conn.execute(
            "SELECT attendance, venue FROM match WHERE attendance=135000"
        ).fetchone()
        self.assertIsNotNone(ham)
        self.assertIn("Hampden", ham["venue"])


if __name__ == "__main__":
    unittest.main()
