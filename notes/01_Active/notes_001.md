# Audit Report — European Football Database (Classic Era)

Lead QA Engineer audit of `C:\EuroDatabase`. Defects were verified against the
live source (not the hunches alone), then fixed with the smallest safe change.
British English throughout. No data was invented and nothing was committed.

**Date:** 3 September 2026  
**Scope:** `app.py`, `build_database.py`, `schema.sql`, `clubs.py`, `seasons.py`  
**Out of scope:** git commit / push; files outside `C:\EuroDatabase`

---

## Summary

| # | Hunch | Verdict | Severity |
|---|-------|---------|----------|
| 1 | Shadowed tie notes | **Confirmed and fixed** | High |
| 2 | Unrendered match attendance | **Confirmed and fixed** | Medium |
| 3 | Ignored `edition.notes` and `runner_up_club_id` | **Confirmed and fixed** | Medium |
| 4 | Header and scroll share `row=0, column=1` | **Confirmed and fixed** | High |
| 5 | Hardcoded `wraplength=680` | **Confirmed and fixed** | Low |
| 6 | SQLite connection never closed | **Confirmed and fixed** | Medium |
| 7 | N+1 club-name queries in `_render_tie` | **Confirmed and fixed** | Medium |
| 8 | `verify()` silently omits third-club legs | **Confirmed and fixed** | High |
| 9 | Unused clubs never warned | **Confirmed and fixed** (none unused today) | Low |
| 10 | `INSERT INTO match` omits `home_pens` / `away_pens` | **Confirmed and fixed** (schema already had the columns) | Medium |
| 11 | Replay / coin-toss header shows only aggregate | **Confirmed and fixed** | High |

`schema.sql` was inspected and left unchanged: `home_pens`, `away_pens`,
`attendance`, `edition.notes` and `runner_up_club_id` were already defined.

---

## Defect 1 — Shadowed tie notes

**Severity:** High  

**Description:** In `_render_tie`, match lines were joined into `detail` and the
`else` branch fell back to `tie["notes"]` only when there were no legs. Any tie
that had both scores *and* a historical note dropped the note.

**Reproduction:** Open 1955-56 First Round, MTK v Anderlecht. The note
"MTK competed as Vörös Lobogó this season." is stored on the tie but never
appeared. Same for 1957-58 Gwardia v Wismut ("Wismut progressed on the toss of
a coin…").

**Fix:** `compose_tie_detail(parts, notes)` returns match text and notes
separately. Notes render in a distinct italic amber callout (`NOTE` colour)
beneath the score line when present. Walkovers with no legs still show the note.

**Regression:** `tests/test_ui_helpers.py::TestNotesNotShadowed`

---

## Defect 2 — Unrendered match attendance

**Severity:** Medium  

**Description:** `m["attendance"]` is stored (Hampden 1960 final: `att=135000`)
but the extras list only considered venue, date and referee.

**Reproduction:** 1959-60 Final, Real Madrid 7-3 Eintracht Frankfurt at Hampden
Park. Attendance 135,000 never appeared in the card.

**Fix:** `format_attendance` appends `135,000 spectators` (thousands separators)
when the value is present.

**Regression:** `TestAttendance`, `TestBuiltDatabase.test_hampden_attendance_stored`

---

## Defect 3 — Ignored edition notes and runner-up

**Severity:** Medium  

**Description:** `edition.notes` and `runner_up_club_id` are written by the
builder and never read by the viewer. The sidebar showed only the champion.

**Reproduction:** Any season. 1959-60 stores runner-up Eintracht Frankfurt and
the Hampden note; the UI showed only Real Madrid.

**Fix:** Edition query now `LEFT JOIN`s the runner-up. Sidebar champion banner
includes "Runner-up" via `format_champion_banner`. Edition notes appear in a
wrapped dim label under the banner.

**Regression:** `TestChampionBanner`, `TestBuiltDatabase.test_edition_notes_and_runner_up_stored`

---

## Defect 4 — Header and scroll overlap

**Severity:** High  

**Description:** `_build_main` placed both `self.header` and `self.scroll` in
`row=0, column=1` with different `pady` (`(20,0)` vs `(64,16)`). On DPI scaling
or larger fonts the scrollable frame and the title occupy the same grid cell.

**Reproduction:** Launch `app.py` and inspect grid info, or resize with large
fonts — the season title and first round heading collide.

**Fix:** Main window now uses two rows: header `row=0`, scroll `row=1`
(`weight=1`). Sidebar `rowspan=2` so it still fills the height.

**Regression:** `TestLayoutRegression.test_header_and_scroll_use_distinct_rows`

---

## Defect 5 — Hardcoded wraplength

**Severity:** Low  

**Description:** Tie-card labels used a static `wraplength=680`. Maximising the
window left long match lines wrapping too early (or, on a narrow window, too
late).

**Fix:** `wraplength_for_width` plus a `<Configure>` binding on each card.
Labels still start at 680 and then track card width minus padding.

**Regression:** `TestWraplength`

---

## Defect 6 — SQLite connection never closed

**Severity:** Medium  

**Description:** `connect()` ran in `__init__` and `mainloop` ended without
closing the connection or cursor.

**Fix:** `protocol("WM_DELETE_WINDOW", self._on_close)` closes cursor then
connection, then `destroy()`.

**Regression:** `TestLayoutRegression.test_window_close_closes_connection`

---

## Defect 7 — N+1 club-name queries

**Severity:** Medium  

**Description:** `_render_tie` used a lambda `SELECT name FROM club WHERE club_id=?`
for each side of the tie and again for every leg. A 16-tie round meant dozens of
identical lookups.

**Fix:** `load_club_name_cache(cur)` loads `club_id → name` once per
`_render_edition`. `_club_name` reads the cache (with a one-shot fallback).

**Regression:** `TestClubCache`, `TestLayoutRegression.test_club_names_preloaded`

---

## Defect 8 — Third-club legs silently omitted

**Severity:** High  

**Description:** `verify()` tallied goals only when `h`/`aw` matched `t1`/`t2`.
A copy-paste third club contributed to neither total. If the remaining goals
still matched `agg`, the build succeeded.

**Reproduction:** Temporarily set a leg of Servette v Real Madrid to
`(milan, real_madrid, …)`. Old `verify()` would not raise `!! CLUB`.

**Fix:** Every leg must have `h in (a, b)` and `aw in (a, b)`; otherwise
`!! CLUB …` aborts the build.

**Regression:** `TestSeasonIntegrity.test_verify_rejects_third_club_in_a_leg`

---

## Defect 9 — Unused clubs never warned

**Severity:** Low  

**Description:** `collect_referenced_keys()` drives which clubs are inserted.
A key added to `clubs.py` but never used in `seasons.py` produced no warning.

**Fix:** `unused_club_keys()` prints a `WARNING` listing zero-appearance keys.
The build still succeeds (a warning, not a hard fail). Current data has none.

**Regression:** `test_unused_club_keys_reports_zero_appearance_entries`,
`test_current_registry_has_no_unused_clubs`

---

## Defect 10 — Shootout columns omitted from INSERT

**Severity:** Medium  

**Description:** `schema.sql` already defines `match.home_pens` and
`match.away_pens`. The builder's `INSERT INTO match` listed neither column, so
even a future extras dict with `home_pens` / `away_pens` would be dropped.
No current season has penalty data; the defect is the silent drop, not missing
results.

**Fix:** `MATCH_INSERT_SQL` and `match_insert_tuple` extract `home_pens` and
`away_pens` from extras (NULL when absent). Schema unchanged.

**Regression:** `TestMatchInsertPens`

---

## Defect 11 — Replay / coin-toss header looks like a scoring error

**Severity:** High  

**Description:** Two-legged ties settled by a play-off or coin toss showed only
the level aggregate (`5-5`, `4-4`) with the winner highlighted in green, which
reads as a bug.

**Reproduction:** 1956-57 Preliminary Round, Dortmund v Spora (5-5, play-off 7-0)
showed `5-5` in green. 1957-58 Gwardia v Wismut showed `4-4` after a 1-1 play-off
and a coin toss.

**Fix:** `format_score_header` now renders `5-5 (Replay: 7-0)` and
`4-4 (Coin Toss)`. Plain aggregates and single-match finals are unchanged.

**Regression:** `TestScoreHeader`

---

## Tests

```
cd C:\EuroDatabase
python -m pytest tests -q
```

(`python -m unittest discover tests` is also supported.)

* `tests/test_integrity.py` — foreign keys, RSSSF aggregates, settlement types,
  third-club rejection, pens insert, notes stored in SQLite.
* `tests/test_ui_helpers.py` — attendance, note formatting, score headers,
  wraplength, layout regression, club-name cache.

---

## Remaining risks

* CustomTkinter `<Configure>` can fire often while resizing; wraplength is only
  written when the computed value changes, but a very large window still wraps
  per card rather than per monitor.
* `CTkFont(..., slant="italic")` for the note callout depends on the platform
  font supporting italic; if it does not, Tk falls back to roman.
* No season currently supplies `home_pens` / `away_pens`, so the INSERT path is
  unit-tested but not exercised by live data.
* Unused-club warning is stdout-only; it will not fail CI until someone treats
  warnings as errors.
* GUI rendering of notes and attendance is covered by helpers plus source
  regression tests, not a headed UI snapshot (no display automation in this
  pass).
