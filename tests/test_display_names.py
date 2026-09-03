# -*- coding: utf-8 -*-
"""Period club-name display and multi-lineage smoke tests."""

import os
import sqlite3
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from clubs import CLUBS, CLUB_NAME_HISTORY
from lineages import LINEAGES
from queries import get_club_display_name
from seasons import SEASONS

DB_PATH = os.path.join(ROOT, "european_football.db")


class TestClubNameHistoryData(unittest.TestCase):
    def test_mtk_entry_present(self):
        hits = [e for e in CLUB_NAME_HISTORY
                if e["club"] == "mtk" and e["season_label"] == "1955-56"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["name_used"], "Vörös Lobogó")

    def test_history_clubs_are_registered(self):
        missing = sorted({e["club"] for e in CLUB_NAME_HISTORY if e["club"] not in CLUBS})
        self.assertEqual(missing, [])


class TestLineagesConfig(unittest.TestCase):
    def test_expected_lineages_documented(self):
        for name in ("European Cup", "European Cup Winners' Cup", "Inter-Cities Fairs Cup"):
            self.assertIn(name, LINEAGES)
            self.assertTrue(LINEAGES[name])

    def test_seeded_lineages_have_config(self):
        for s in SEASONS:
            self.assertIn(s["lineage"], LINEAGES)


class TestSeasons196061(unittest.TestCase):
    def test_european_cup_1960_61_present(self):
        hits = [s for s in SEASONS
                if s["season_label"] == "1960-61" and s["lineage"] == "European Cup"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["winner"], "benfica")
        self.assertEqual(hits[0]["runner_up"], "barcelona")

    def test_cwc_1960_61_present(self):
        hits = [s for s in SEASONS
                if s["season_label"] == "1960-61"
                and s["lineage"] == "European Cup Winners' Cup"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["winner"], "fiorentina")
        self.assertEqual(hits[0]["runner_up"], "rangers")


@unittest.skipUnless(os.path.exists(DB_PATH), "european_football.db not built yet")
class TestDisplayNameAgainstDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row
        cls.conn.execute("PRAGMA foreign_keys = ON")
        cls.cur = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def _mtk_id(self):
        row = self.cur.execute(
            "SELECT club_id FROM club WHERE name = ?", ("MTK Budapest",)
        ).fetchone()
        self.assertIsNotNone(row)
        return row["club_id"]

    def test_mtk_1955_56_is_voros_lobogo(self):
        eid = self.cur.execute(
            "SELECT edition_id FROM edition WHERE season_label = '1955-56'"
        ).fetchone()["edition_id"]
        name = get_club_display_name(self.cur, self._mtk_id(), eid)
        self.assertEqual(name, "Vörös Lobogó")

    def test_mtk_other_season_is_canonical(self):
        # MTK does not appear after 1955-56 in seeded data, but canonical fallback
        # must still apply for any later edition id.
        later = self.cur.execute(
            "SELECT edition_id FROM edition WHERE season_label = '1959-60'"
        ).fetchone()["edition_id"]
        name = get_club_display_name(self.cur, self._mtk_id(), later)
        self.assertEqual(name, "MTK Budapest")

    def test_club_name_history_table_populated(self):
        n = self.cur.execute("SELECT COUNT(*) AS c FROM club_name_history").fetchone()["c"]
        self.assertGreaterEqual(n, 1)

    def test_two_lineages_in_1960_61(self):
        rows = self.cur.execute(
            """SELECT l.name FROM edition e
               JOIN lineage l ON l.lineage_id = e.lineage_id
               WHERE e.season_label = '1960-61'
               ORDER BY l.name"""
        ).fetchall()
        names = [r["name"] for r in rows]
        self.assertIn("European Cup", names)
        self.assertIn("European Cup Winners' Cup", names)


if __name__ == "__main__":
    unittest.main()
