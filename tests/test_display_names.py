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


class TestSeasons196162(unittest.TestCase):
    def _ec(self):
        hits = [s for s in SEASONS
                if s["season_label"] == "1961-62" and s["lineage"] == "European Cup"]
        self.assertEqual(len(hits), 1)
        return hits[0]

    def test_european_cup_1961_62_champion_and_runner_up(self):
        s = self._ec()
        self.assertEqual(s["winner"], "benfica")
        self.assertEqual(s["runner_up"], "real_madrid")
        self.assertFalse(s["away_goals_active"])

    def test_benfica_tottenham_semi_aggregate(self):
        """RSSSF: Benfica 3-1, 1-2 Tottenham — 4-3 aggregate."""
        s = self._ec()
        found = None
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                if {tie["t1"], tie["t2"]} == {"benfica", "tottenham"}:
                    found = tie
        self.assertIsNotNone(found)
        self.assertEqual(found["agg"], (4, 3))
        self.assertEqual(found["win"], "benfica")
        self.assertEqual(found["by"], "aggregate")

    def test_juventus_real_madrid_playoff(self):
        s = self._ec()
        found = None
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                if {tie["t1"], tie["t2"]} == {"juventus", "real_madrid"}:
                    found = tie
        self.assertIsNotNone(found)
        self.assertEqual(found["by"], "replay")
        self.assertEqual(found["agg"], (1, 1))
        self.assertEqual(found["win"], "real_madrid")
        self.assertEqual(len(found["legs"]), 3)

    def test_linfield_withdrew_after_first_leg(self):
        s = self._ec()
        found = None
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                if {tie["t1"], tie["t2"]} == {"vorwarts", "linfield"}:
                    found = tie
        self.assertIsNotNone(found)
        self.assertEqual(found["win"], "vorwarts")
        self.assertEqual(found["by"], "walkover")
        self.assertIsNone(found["agg"])
        self.assertEqual(len(found["legs"]), 0)
        self.assertIn("withdrew", found["note"].lower())
        self.assertIn("3-0", found["note"])


class TestCWC196162(unittest.TestCase):
    def _cwc(self):
        hits = [s for s in SEASONS
                if s["season_label"] == "1961-62" and s["lineage"] == "European Cup Winners' Cup"]
        self.assertEqual(len(hits), 1)
        return hits[0]

    def _tie(self, s, a, b):
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                if {tie["t1"], tie["t2"]} == {a, b}:
                    return tie
        return None

    def test_champion_and_runner_up(self):
        s = self._cwc()
        self.assertEqual(s["winner"], "atletico")
        self.assertEqual(s["runner_up"], "fiorentina")
        self.assertFalse(s["away_goals_active"])

    def test_ujpest_floriana_prelim_aggregate(self):
        """RSSSF: Floriana 2-5, 2-10 Ujpesti Dozsa - 4-15 aggregate."""
        s = self._cwc()
        found = self._tie(s, "floriana", "ujpest")
        self.assertIsNotNone(found)
        self.assertEqual(found["agg"], (4, 15))
        self.assertEqual(found["win"], "ujpest")
        self.assertEqual(found["by"], "aggregate")

    def test_final_was_a_single_match_replayed_not_a_two_legged_playoff(self):
        """Atletico Madrid 1-1 aet Fiorentina at Hampden Park, then a
        straight replay in Stuttgart - agg=None, exactly 2 legs, no
        aggregate concept between the two independent matches."""
        s = self._cwc()
        found = self._tie(s, "atletico", "fiorentina")
        self.assertIsNotNone(found)
        self.assertEqual(found["by"], "replay")
        self.assertIsNone(found["agg"])
        self.assertEqual(len(found["legs"]), 2)
        self.assertEqual(found["win"], "atletico")

    def test_motor_jena_fixtures_relocated_away_from_east_germany(self):
        """Cold War travel restrictions (shortly after the Berlin Wall went
        up) meant every Motor Jena tie that should have been played at an
        opponent's ground, or the opponent's leg at Jena's opponents ground,
        was instead relocated - a documented recurring oddity this season."""
        s = self._cwc()
        relocated = 0
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                if "motor_jena" not in (tie["t1"], tie["t2"]):
                    continue
                for leg in tie["legs"]:
                    extras = leg[4] if len(leg) > 4 else {}
                    if "relocated" in (extras.get("venue") or ""):
                        relocated += 1
        self.assertGreaterEqual(relocated, 3)


class TestEC196263(unittest.TestCase):
    def _ec(self):
        hits = [s for s in SEASONS
                if s["season_label"] == "1962-63" and s["lineage"] == "European Cup"]
        self.assertEqual(len(hits), 1)
        return hits[0]

    def _tie(self, s, a, b):
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                if {tie["t1"], tie["t2"]} == {a, b}:
                    return tie
        return None

    def test_champion_and_runner_up(self):
        s = self._ec()
        self.assertEqual(s["winner"], "milan")
        self.assertEqual(s["runner_up"], "benfica")
        self.assertFalse(s["away_goals_active"])

    def test_milan_union_lux_first_round_aggregate(self):
        """RSSSF: Milan 8-0, 6-0 US Luxembourg - 14-0 aggregate."""
        s = self._ec()
        found = self._tie(s, "milan", "union_lux")
        self.assertIsNotNone(found)
        self.assertEqual(found["agg"], (14, 0))
        self.assertEqual(found["win"], "milan")
        self.assertEqual(found["by"], "aggregate")

    def test_servette_feyenoord_needed_a_genuine_playoff_leg(self):
        """Level 4-4 on aggregate over two real legs, then a third play-off
        leg in Dusseldorf (Feyenoord won it 3-1 aet) - the ordinary
        two-legged-tie-plus-play-off replay shape, unlike the CWC final."""
        s = self._ec()
        found = self._tie(s, "servette", "feyenoord")
        self.assertIsNotNone(found)
        self.assertEqual(found["by"], "replay")
        self.assertEqual(found["agg"], (4, 4))
        self.assertEqual(len(found["legs"]), 3)
        self.assertEqual(found["win"], "feyenoord")

    def test_reims_home_legs_relocated_to_paris(self):
        s = self._ec()
        relocated = 0
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                if "reims" not in (tie["t1"], tie["t2"]):
                    continue
                for leg in tie["legs"]:
                    extras = leg[4] if len(leg) > 4 else {}
                    if "Paris" in (extras.get("venue") or ""):
                        relocated += 1
        self.assertGreaterEqual(relocated, 2)


class TestFairsCup195558(unittest.TestCase):
    def _fc(self):
        hits = [s for s in SEASONS
                if s["season_label"] == "1955-58" and s["lineage"] == "Inter-Cities Fairs Cup"]
        self.assertEqual(len(hits), 1)
        return hits[0]

    def _tie(self, s, a, b):
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                if {tie["t1"], tie["t2"]} == {a, b}:
                    return tie
        return None

    def test_champion_and_runner_up(self):
        s = self._fc()
        self.assertEqual(s["winner"], "barcelona")
        self.assertEqual(s["runner_up"], "london_xi")
        self.assertFalse(s["away_goals_active"])

    def test_final_was_two_legged_unlike_other_finals_this_era(self):
        """Barcelona 2-2 London XI at Stamford Bridge, then 6-0 at Camp Nou -
        8-2 on aggregate, matching RSSSF's own stated result."""
        s = self._fc()
        found = self._tie(s, "london_xi", "barcelona")
        self.assertIsNotNone(found)
        self.assertEqual(found["by"], "aggregate")
        self.assertEqual(found["agg"], (2, 8))
        self.assertEqual(found["win"], "barcelona")
        self.assertEqual(len(found["legs"]), 2)

    def test_group_a_barcelona_qualified_after_a_withdrawal(self):
        s = self._fc()
        found = self._tie(s, "barcelona", "kbu_copenhagen")
        self.assertIsNotNone(found)
        self.assertEqual(found["agg"], (7, 3))
        self.assertEqual(found["win"], "barcelona")
        self.assertIn("withdrew", found["note"].lower())

    def test_group_d_round_robin_has_two_genuine_draws(self):
        """London XI topped Group D on points despite drawing twice - neither
        drawn tie has (or needs) a winner."""
        s = self._fc()
        drawn = [
            self._tie(s, "london_xi", "frankfurt_xi"),
            self._tie(s, "frankfurt_xi", "basel_xi"),
        ]
        for tie in drawn:
            self.assertIsNotNone(tie)
            self.assertIsNone(tie["win"])
            self.assertEqual(tie["agg"][0], tie["agg"][1])

    def test_semi_final_needed_a_genuine_playoff(self):
        s = self._fc()
        found = self._tie(s, "birmingham", "barcelona")
        self.assertIsNotNone(found)
        self.assertEqual(found["by"], "replay")
        self.assertEqual(found["agg"], (4, 4))
        self.assertEqual(len(found["legs"]), 3)
        self.assertEqual(found["win"], "barcelona")


class TestClassicEraGoldenUnchanged(unittest.TestCase):
    def test_five_in_a_row_champions(self):
        expected = {
            "1955-56": ("real_madrid", "reims"),
            "1956-57": ("real_madrid", "fiorentina"),
            "1957-58": ("real_madrid", "milan"),
            "1958-59": ("real_madrid", "reims"),
            "1959-60": ("real_madrid", "eintracht"),
        }
        for label, (winner, runner) in expected.items():
            hits = [s for s in SEASONS
                    if s["season_label"] == label and s["lineage"] == "European Cup"]
            self.assertEqual(len(hits), 1, label)
            self.assertEqual(hits[0]["winner"], winner, label)
            self.assertEqual(hits[0]["runner_up"], runner, label)

    def test_1955_56_servette_real_madrid_aggregate(self):
        s = next(x for x in SEASONS
                 if x["season_label"] == "1955-56" and x["lineage"] == "European Cup")
        tie = s["rounds"][0]["ties"][0]
        self.assertEqual(tie["t1"], "servette")
        self.assertEqual(tie["t2"], "real_madrid")
        self.assertEqual(tie["agg"], (0, 7))


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

    def test_all_configured_lineages_inserted(self):
        """Every LINEAGES entry must exist in the table even before its first
        edition is seeded (this used to fail for the then-unseeded Fairs Cup)."""
        rows = self.cur.execute("SELECT name FROM lineage").fetchall()
        names = {r["name"] for r in rows}
        for expected in LINEAGES:
            self.assertIn(expected, names)

    def test_fairs_cup_has_its_inaugural_edition(self):
        row = self.cur.execute(
            """SELECT e.season_label, COUNT(*) OVER () AS c FROM edition e
               JOIN lineage l ON l.lineage_id = e.lineage_id
               WHERE l.name = 'Inter-Cities Fairs Cup'"""
        ).fetchone()
        self.assertEqual(row["c"], 1)
        self.assertEqual(row["season_label"], "1955-58")

    def test_name_history_scoped_to_contested_lineage_not_shared_label(self):
        """cwks_warsaw and wismut only played the European Cup in 1960-61, not
        the Cup Winners' Cup - their period names must not leak onto the CWC
        edition just because it shares the "1960-61" season_label."""
        rows = self.cur.execute(
            """SELECT c.name AS club, l.name AS lineage
               FROM club_name_history h
               JOIN club c ON c.club_id = h.club_id
               JOIN edition e ON e.edition_id = h.edition_id
               JOIN lineage l ON l.lineage_id = e.lineage_id
               WHERE h.season_label = '1960-61'"""
        ).fetchall()
        by_club = {r["club"]: r["lineage"] for r in rows}
        self.assertEqual(by_club.get("CWKS Warsaw"), "European Cup")
        self.assertEqual(by_club.get("Wismut Karl-Marx-Stadt"), "European Cup")


if __name__ == "__main__":
    unittest.main()
