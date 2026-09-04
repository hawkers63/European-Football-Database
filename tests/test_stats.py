# -*- coding: utf-8 -*-
"""Head-to-head, goal statistics and leaderboard tests.

Rebuilds a fresh SQLite database into a temporary path so results never
depend on a stale european_football.db on disk.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from build_database import build
from queries import (
    classic_era_title_holders,
    club_record,
    connect,
    edition_goal_stats,
    find_club_id,
    h2h_is_complement,
    head_to_head,
    leaderboard,
    leaderboard_finals,
    leaderboard_matches,
    leaderboard_titles,
    season_goal_stats,
)


class TestStats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls._tmpdir.name, "stats_test.db")
        rc = build(force=True, db_path=cls.db_path)
        if rc != 0:
            raise RuntimeError("build failed for stats tests")
        cls.conn = connect(cls.db_path)
        cls.cur = cls.conn.cursor()
        cls.real_madrid = find_club_id(cls.cur, "Real Madrid")
        cls.reims = find_club_id(cls.cur, "Stade de Reims")
        cls.barcelona = find_club_id(cls.cur, "FC Barcelona")
        cls.eintracht = find_club_id(cls.cur, "Eintracht Frankfurt")
        cls.kups = find_club_id(cls.cur, "KuPS Kuopio")
        cls.benfica = find_club_id(cls.cur, "SL Benfica")
        cls.fiorentina = find_club_id(cls.cur, "Fiorentina")

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls._tmpdir.cleanup()

    # ----- head-to-head -------------------------------------------------

    def test_h2h_symmetry_real_madrid_barcelona(self):
        ab = head_to_head(self.cur, self.real_madrid, self.barcelona)
        ba = head_to_head(self.cur, self.barcelona, self.real_madrid)
        self.assertTrue(h2h_is_complement(ab, ba), (ab, ba))
        self.assertTrue(h2h_is_complement(ba, ab))

    def test_h2h_symmetry_several_pairs(self):
        pairs = (
            (self.real_madrid, self.reims),
            (self.real_madrid, self.eintracht),
            (self.benfica, self.barcelona),
        )
        for a, b in pairs:
            left = head_to_head(self.cur, a, b)
            right = head_to_head(self.cur, b, a)
            self.assertTrue(h2h_is_complement(left, right), (a, b))

    def test_real_madrid_reims_two_finals(self):
        rec = head_to_head(self.cur, self.real_madrid, self.reims)
        self.assertEqual(rec["matches_played"], 2)
        self.assertEqual(rec["ties_contested"], 2)
        self.assertEqual(rec["wins_a"], 2)
        self.assertEqual(rec["wins_b"], 0)
        self.assertEqual(rec["draws"], 0)
        self.assertEqual(rec["goals_a"], 6)  # 4-3 in 1956, 2-0 in 1959
        self.assertEqual(rec["goals_b"], 3)
        self.assertEqual(rec["walkovers"], [])
        self.assertEqual(rec["club_a_name"], "Real Madrid")
        self.assertEqual(rec["club_b_name"], "Stade de Reims")

    def test_real_madrid_barcelona_documented_aggregate(self):
        """1959-60 SF aggregate 6-2 plus 1960-61 first round 3-4."""
        rec = head_to_head(self.cur, self.real_madrid, self.barcelona)
        self.assertEqual(rec["matches_played"], 4)
        self.assertEqual(rec["ties_contested"], 2)
        self.assertEqual(rec["wins_a"], 2)
        self.assertEqual(rec["draws"], 1)
        self.assertEqual(rec["wins_b"], 1)
        self.assertEqual(rec["goals_a"], 9)  # 3+3 + 2+1
        self.assertEqual(rec["goals_b"], 6)  # 1+1 + 2+2
        sf = [m for m in rec["matches"] if m["season_label"] == "1959-60"]
        self.assertEqual(len(sf), 2)
        self.assertEqual(
            sum(m["home_score"] + m["away_score"] for m in sf), 8
        )
        rm_goals = 0
        barca_goals = 0
        for m in sf:
            if m["home_club_id"] == self.real_madrid:
                rm_goals += m["home_score"]
                barca_goals += m["away_score"]
            else:
                rm_goals += m["away_score"]
                barca_goals += m["home_score"]
        self.assertEqual((rm_goals, barca_goals), (6, 2))

    def test_walkover_is_labelled_not_scored_three_nil(self):
        rec = head_to_head(self.cur, self.eintracht, self.kups)
        self.assertEqual(rec["matches_played"], 0)
        self.assertEqual(rec["goals_a"], 0)
        self.assertEqual(rec["goals_b"], 0)
        self.assertEqual(rec["ties_contested"], 1)
        self.assertEqual(len(rec["walkovers"]), 1)
        wo = rec["walkovers"][0]
        self.assertEqual(wo["decided_by"], "walkover")
        self.assertEqual(wo["winner_club_id"], self.eintracht)
        self.assertEqual(wo["season_label"], "1959-60")
        # Complement still holds when the only meeting is a walkover.
        other = head_to_head(self.cur, self.kups, self.eintracht)
        self.assertTrue(h2h_is_complement(rec, other))

    # ----- Classic Era facts --------------------------------------------

    def test_classic_era_1955_60_champions(self):
        holders = classic_era_title_holders(self.cur)
        self.assertEqual([h["season_label"] for h in holders], [
            "1955-56", "1956-57", "1957-58", "1958-59", "1959-60",
        ])
        self.assertTrue(all(h["winner_name"] == "Real Madrid" for h in holders))
        self.assertEqual(
            [h["runner_up_name"] for h in holders],
            [
                "Stade de Reims",
                "Fiorentina",
                "Milan",
                "Stade de Reims",
                "Eintracht Frankfurt",
            ],
        )

    def test_real_madrid_five_titles_in_five_seasons(self):
        titles = [r for r in leaderboard_titles(self.cur) if r["club_id"] == self.real_madrid]
        self.assertEqual(len(titles), 1)
        self.assertEqual(titles[0]["titles"], 5)
        rec = club_record(self.cur, self.real_madrid)
        self.assertEqual(rec["titles"], 5)
        # 1961-62 European Cup final: runners-up to Benfica.
        self.assertEqual(rec["runner_up_finishes"], 1)
        self.assertEqual(rec["finals_reached"], 6)

    def test_eintracht_1959_60_runners_up(self):
        row = self.cur.execute(
            """SELECT w.name AS winner, r.name AS runner_up
                 FROM edition e
                 JOIN club w ON w.club_id = e.winner_club_id
                 JOIN club r ON r.club_id = e.runner_up_club_id
                WHERE e.season_label = '1959-60' AND e.competition_name = 'European Cup'"""
        ).fetchone()
        self.assertEqual(row["winner"], "Real Madrid")
        self.assertEqual(row["runner_up"], "Eintracht Frankfurt")
        finals = [r for r in leaderboard_finals(self.cur) if r["club_id"] == self.eintracht]
        self.assertEqual(finals[0]["finals_reached"], 1)
        self.assertEqual(finals[0]["titles"], 0)
        self.assertEqual(finals[0]["runner_up_finishes"], 1)

    def test_hampden_final_goals_count_once(self):
        rec = head_to_head(self.cur, self.real_madrid, self.eintracht)
        self.assertEqual(rec["matches_played"], 1)
        self.assertEqual(rec["goals_a"], 7)
        self.assertEqual(rec["goals_b"], 3)
        rm = club_record(self.cur, self.real_madrid)
        self.assertGreaterEqual(rm["finals_goals_for"], 7)
        # Highest-scoring tie involving Real Madrid includes the 7-3 final
        # (14-goal Jeunesse tie ranks above it).
        totals = {t["goals"] for t in rm["highest_scoring_ties"]}
        self.assertTrue(10 in totals or 14 in totals)

    # ----- leaderboards match direct SQL --------------------------------

    def test_title_leaderboard_matches_edition_sql(self):
        board = leaderboard_titles(self.cur)
        sql_total = self.cur.execute(
            "SELECT COUNT(*) AS n FROM edition WHERE winner_club_id IS NOT NULL"
        ).fetchone()["n"]
        self.assertEqual(sum(r["titles"] for r in board), sql_total)
        # Real Madrid still top on five titles; Benfica two (1960-61 and 1961-62).
        self.assertEqual(board[0]["name"], "Real Madrid")
        self.assertEqual(board[0]["rank"], 1)
        self.assertEqual(board[0]["titles"], 5)
        titles_by_name = {r["name"]: r["titles"] for r in board}
        self.assertEqual(titles_by_name["SL Benfica"], 2)
        self.assertEqual(titles_by_name["Fiorentina"], 1)

    def test_matches_leaderboard_double_counts_each_match(self):
        board = leaderboard_matches(self.cur)
        sql_matches = self.cur.execute(
            """SELECT COUNT(*) AS n FROM match
                WHERE home_score IS NOT NULL AND away_score IS NOT NULL"""
        ).fetchone()["n"]
        self.assertEqual(sum(r["matches_played"] for r in board), 2 * sql_matches)
        sql_goals = self.cur.execute(
            """SELECT COALESCE(SUM(home_score + away_score), 0) AS g FROM match
                WHERE home_score IS NOT NULL AND away_score IS NOT NULL"""
        ).fetchone()["g"]
        self.assertEqual(sum(r["goals_for"] for r in board), sql_goals)
        self.assertEqual(sum(r["goals_against"] for r in board), sql_goals)
        self.assertEqual(sum(r["goal_difference"] for r in board), 0)

    def test_finals_leaderboard_matches_edition_sql(self):
        board = leaderboard_finals(self.cur)
        sql_winners = self.cur.execute(
            "SELECT COUNT(*) AS n FROM edition WHERE winner_club_id IS NOT NULL"
        ).fetchone()["n"]
        sql_runners = self.cur.execute(
            "SELECT COUNT(*) AS n FROM edition WHERE runner_up_club_id IS NOT NULL"
        ).fetchone()["n"]
        self.assertEqual(sum(r["titles"] for r in board), sql_winners)
        self.assertEqual(sum(r["runner_up_finishes"] for r in board), sql_runners)
        self.assertEqual(sum(r["finals_reached"] for r in board), sql_winners + sql_runners)

    def test_leaderboard_dispatch(self):
        self.assertEqual(leaderboard(self.cur, "titles")[0]["name"], "Real Madrid")
        self.assertTrue(leaderboard(self.cur, "matches"))
        self.assertTrue(leaderboard(self.cur, "finals"))
        with self.assertRaises(ValueError):
            leaderboard(self.cur, "colour")

    def test_leaderboard_sort_order_titles(self):
        board = leaderboard_titles(self.cur)
        pairs = [(r["titles"], r["name"].lower()) for r in board]
        self.assertEqual(pairs, sorted(pairs, key=lambda p: (-p[0], p[1])))

    # ----- goals --------------------------------------------------------

    def test_edition_goals_match_sql(self):
        eid = self.cur.execute(
            "SELECT edition_id FROM edition WHERE season_label = '1959-60'"
        ).fetchone()["edition_id"]
        stats = edition_goal_stats(self.cur, eid)
        sql = self.cur.execute(
            """SELECT COALESCE(SUM(m.home_score + m.away_score), 0) AS g
                 FROM match m
                 JOIN tie t ON t.tie_id = m.tie_id
                 JOIN round r ON r.round_id = t.round_id
                WHERE r.edition_id = ?
                  AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL""",
            (eid,),
        ).fetchone()["g"]
        self.assertEqual(stats["total_goals"], sql)
        self.assertEqual(sum(r["goals"] for r in stats["rounds"]), sql)
        final = next(r for r in stats["rounds"] if r["name"] == "Final")
        self.assertEqual(final["goals"], 10)  # 7-3 Hampden

    def test_hat_trick_notes_only_when_stored(self):
        eid = self.cur.execute(
            "SELECT edition_id FROM edition WHERE season_label = '1959-60'"
        ).fetchone()["edition_id"]
        stats = edition_goal_stats(self.cur, eid)
        self.assertEqual(stats["hat_trick_notes"], [])
        match_id = self.cur.execute(
            """SELECT m.match_id FROM match m
                 JOIN tie t ON t.tie_id = m.tie_id
                 JOIN round r ON r.round_id = t.round_id
                WHERE r.edition_id = ? AND r.name = 'Final'""",
            (eid,),
        ).fetchone()["match_id"]
        self.cur.execute(
            "UPDATE match SET notes = ? WHERE match_id = ?",
            ("Di Stefano hat-trick recorded in match notes.", match_id),
        )
        try:
            updated = edition_goal_stats(self.cur, eid)
            self.assertEqual(len(updated["hat_trick_notes"]), 1)
            self.assertIn("Di Stefano hat-trick", updated["hat_trick_notes"][0]["notes"])
            self.assertEqual(updated["hat_trick_notes"][0]["source"], "match.notes")
        finally:
            self.cur.execute("UPDATE match SET notes = NULL WHERE match_id = ?", (match_id,))

    def test_season_goals_1960_61_two_lineages(self):
        editions = season_goal_stats(self.cur, "1960-61")
        names = {e["competition_name"] for e in editions}
        self.assertIn("European Cup", names)
        self.assertIn("European Cup Winners' Cup", names)

    def test_club_record_skips_walkovers(self):
        rec = club_record(self.cur, self.kups)
        self.assertEqual(rec["matches_played"], 0)
        self.assertEqual(rec["goals_for"], 0)
        self.assertEqual(rec["titles"], 0)

    def test_replay_legs_are_not_double_counted(self):
        # Real Madrid vs Rapid Wien 1956-57: two legs 4-2, 3-1 plus play-off 2-0.
        rec = club_record(self.cur, self.real_madrid, season_label="1956-57")
        sql = self.cur.execute(
            """SELECT COUNT(*) AS n FROM match m
                WHERE (m.home_club_id = ? OR m.away_club_id = ?)
                  AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL
                  AND m.tie_id IN (
                      SELECT t.tie_id FROM tie t
                      JOIN round r ON r.round_id = t.round_id
                      JOIN edition e ON e.edition_id = r.edition_id
                      WHERE e.season_label = '1956-57'
                  )""",
            (self.real_madrid, self.real_madrid),
        ).fetchone()["n"]
        self.assertEqual(rec["matches_played"], sql)

    def test_fresh_database_is_not_the_repo_file(self):
        repo_db = os.path.join(ROOT, "european_football.db")
        self.assertNotEqual(os.path.abspath(self.db_path), os.path.abspath(repo_db))
        self.assertTrue(os.path.exists(self.db_path))


if __name__ == "__main__":
    unittest.main()
