# -*- coding: utf-8 -*-
"""Tests for tools/import_rsssf.py."""

import io
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.import_rsssf import (
    _is_ignorable_line,
    emit_tie_block,
    main,
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


class TestIgnoredLineReporting(unittest.TestCase):
    """notes_002 Finding 7: a malformed line must be reported by number, not
    silently dropped from a bulk transcription."""

    def test_blank_and_comment_lines_are_not_ignorable_warnings(self):
        self.assertTrue(_is_ignorable_line(""))
        self.assertTrue(_is_ignorable_line("# a comment"))
        self.assertTrue(_is_ignorable_line("Additional matches not yet dated"))

    def test_malformed_line_is_not_ignorable(self):
        self.assertFalse(_is_ignorable_line("this is not an RSSSF result line"))

    def test_main_reports_malformed_line_by_number(self):
        lines = (
            "Heart Of Midlothian      Sco  SL Benfica               Por   1-2  0-3  1-5\n"
            "this line is garbled and will not parse\n"
            "Real Madrid               Esp  Reims                    Fra   2-0\n"
        )
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(lines)
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = main(["--stdin", "--season", "1999-00"])
        finally:
            sys.stdin = original_stdin
        self.assertEqual(code, 0)
        self.assertIn("line 2", err.getvalue())
        self.assertIn("garbled", err.getvalue())

    def test_no_warning_when_every_line_parses(self):
        lines = (
            "Heart Of Midlothian      Sco  SL Benfica               Por   1-2  0-3  1-5\n"
        )
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(lines)
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = main(["--stdin", "--season", "1999-00"])
        finally:
            sys.stdin = original_stdin
        self.assertEqual(code, 0)
        self.assertNotIn("ignored", err.getvalue())


if __name__ == "__main__":
    unittest.main()