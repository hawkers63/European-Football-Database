# -*- coding: utf-8 -*-
"""Tests for tools/import_rsssf.py."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.import_rsssf import (
    emit_tie_block,
    match_club,
    parse_rsssf_line,
    validate_aggregate,
)


class TestParseRsssf(unittest.TestCase):
    def test_ross_summary_line_hearts_benfica(self):
        line = "Heart Of Midlothian      Sco  SL Benfica               Por   1-2  0-3  1-5"
        parsed = parse_rsssf_line(line)
        self.assertEqual(parsed["type"], "tie")
        self.assertEqual(parsed["a_key"], "hearts")
        self.assertEqual(parsed["b_key"], "benfica")
        self.assertEqual(parsed["leg1"], (1, 2))
        self.assertEqual(parsed["leg2_home"], (3, 0))
        self.assertEqual(parsed["agg"], (1, 5))
        self.assertEqual(validate_aggregate(parsed), [])

    def test_playoff_brackets(self):
        line = ("SK Rapid Vienna          Aut  Wismut Karl-Marx-Stadt   GDR   "
                "3-1  0-2  3-3  [1-0]y")
        parsed = parse_rsssf_line(line)
        self.assertEqual(parsed["agg"], (3, 3))
        self.assertEqual(parsed["playoff"], (1, 0))
        self.assertEqual(parsed["leg2_home"], (2, 0))
        self.assertEqual(validate_aggregate(parsed), [])
        block = emit_tie_block(parsed)
        self.assertIn('"by": "replay"', block)
        self.assertIn("rapid_wien", block)

    def test_second_named_home_orientation(self):
        line = "Heart Of Midlothian Sco SL Benfica Por 1-2  3-0  1-5"
        parsed = parse_rsssf_line(line)
        self.assertEqual(parsed["leg2_home"], (3, 0))
        self.assertEqual(validate_aggregate(parsed), [])

    def test_walkover_becomes_note(self):
        parsed = parse_rsssf_line(
            "Wismut Karl-Marx-Stadt (GDR) walkover, Glenavon (Nir) withdrew"
        )
        self.assertEqual(parsed["type"], "note")

    def test_fuzzy_legia(self):
        key, conf = match_club("Legia Warsaw")
        self.assertEqual(key, "cwks_warsaw")
        self.assertGreaterEqual(conf, 0.9)

    def test_hibernians_malta_not_edinburgh(self):
        key, conf = match_club("Hibernians (Paola)")
        self.assertEqual(key, "hibernians_malta")
        self.assertGreaterEqual(conf, 0.9)
        key2, _ = match_club("Hibernian")
        self.assertEqual(key2, "hibernian")

    def test_1961_62_juventus_real_playoff_line(self):
        line = ("Juventus                 Ita  Real Madrid              Esp   "
                "0-1  1-0  1-1  [1-3]x")
        parsed = parse_rsssf_line(line)
        self.assertEqual(parsed["agg"], (1, 1))
        self.assertEqual(parsed["playoff"], (1, 3))
        self.assertEqual(parsed["a_key"], "juventus")
        self.assertEqual(parsed["b_key"], "real_madrid")
        self.assertEqual(validate_aggregate(parsed), [])
        block = emit_tie_block(parsed)
        self.assertIn('"by": "replay"', block)
        self.assertIn("real_madrid", block)


if __name__ == "__main__":
    unittest.main()