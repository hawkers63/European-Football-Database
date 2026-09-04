# audits_010 - CustomTkinter v1.3 UI slice keep-green (Hawkeye)

Date: 2026-09-03 23:16 BST (Europe/London)
Agent: UI keep-green executor on Hawkeye
Machine: Hawkeye `db77ad96-8cd3-440f-8eaa-beaaa8c875bd`
Root: `C:\EuroDatabase` (shared checkout only; did not touch EuroDatabase-dbeng or EuroDatabase-parser)

## Checkout

- Branch at first survey: `feat/season-1961-62` @ `370fd2d` (dirty mix: CHANGELOG, DATA_GUIDE, build_database.py, cli.py, queries.py, test_stats.py).
- Other agents then committed stats work and switched this checkout.
- Branch at pytest / this note: `feat/stats-analyst` @ `449225c` (full `449225c011e82b14616642bc8978d719adaaed1b`).
- `feat/ui-ux-overhaul` at `2417fea`, behind origin by 2 (untouched).
- `main` at `6374927` (untouched).
- Did not push, force-push, git config, or commit.

## UI package

Modular v1.3 viewer is present.

- `app.py` docstring: European Football Database viewer (Classic Era); imports `ui.formatters` (re-exported for tests) and the rest of `ui.*`.
- `ui/`: `__init__.py`, `bracket_view.py`, `club_dialog.py`, `data.py`, `formatters.py`, `header.py`, `sidebar.py`, `theme.py`, `tie_card.py`.
- UI tests: `tests/test_ui_helpers.py`, `tests/test_ui_overhaul.py`.

`audits_009.md` already existed (Tony keep-green note on the same SHA); this file is the next free N.

## pytest (Python 3.11)

Interpreter: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe`
Command: `python -m pytest -q --tb=line`

1. Earlier full suite (when HEAD was `bc666e4` on this tree): **104 passed** in 5.11s.
2. Full suite on `449225c`: **1 failed, 103 passed** in 5.67s.
   - Failure is **not UI**: `tests/test_integrity.py::TestSeasonIntegrity::test_current_registry_has_no_unused_clubs`
   - Unused club ids: `b1913`, `feyenoord`, `gornik`, `haka`, `hibernians_malta`, `monaco`, `nurnberg`, `tottenham`
   - Left unfixed: registry/season data, not a UI display-name bug. Constraints forbid rewriting `seasons.py` / `clubs.py` / `queries.py` unless a UI bug.
3. UI slice `tests/test_ui_helpers.py` + `tests/test_ui_overhaul.py`: **40 passed** in 2.29s.

UI slice is **green**. No `app.py` / `ui/*` / `tests/test_ui_*.py` edits.

## Files changed by this pass

None (no UI failure; no commit). This note only.

## Leftover dirty files (other agents; left untouched)

`git status -sb` at write time:

```
## feat/stats-analyst
 M CHANGELOG.md
 M DATA_GUIDE.md
 M ROADMAP.md
 M clubs.py
 M seasons.py
 M tests/test_display_names.py
 M tests/test_import_rsssf.py
 M tests/test_stats.py
 M tools/import_rsssf.py
?? _write_audit_010.py
?? notes/00_Audits/audits_009.md
```

CHANGELOG was not conflicted on this pass.
