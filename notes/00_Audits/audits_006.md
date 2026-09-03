# audits_006.md - UI/UX overhaul landed on Hawkeye

Date: 2026-09-03 22:40 BST (Europe/London)
Branch: `feat/database-engineer` @ `e2d0854` (working tree dirty: modular `app.py` + untracked `ui/` and tests)
Role: UI/UX Desktop Application Specialist

## Result

The Classic Era viewer on `C:\EuroDatabase` is now the modular shell, not the 15,255-byte monolith. Helper tests and overhaul tests are green.

`python -m pytest -q` (Python 3.11): **84 passed** in 1.39s.

Period-accurate labels confirmed: MTK Budapest in 1955-56 displays as **Vörös Lobogó** via `ui.data.load_club_cache`, matching `queries.get_club_display_name`.

Headed GUI was not smoke-tested (no interactive display session in this run). `import app` and all helper tests pass without a window.

## Files actually on Hawkeye

| Path | Bytes | SHA-256 (16) | Status |
|---|---:|---|---|
| `app.py` | 10873 | `4b003705ddaa13dc` | modified vs HEAD (modular shell) |
| `ui/__init__.py` | 88 | `e13a3aae5a32e59f` | untracked |
| `ui/theme.py` | 1184 | `f2e060039fad1f4a` | untracked |
| `ui/formatters.py` | 6694 | `9997db105635fb9a` | untracked |
| `ui/data.py` | 14295 | `c0f176b43d535024` | untracked (was missing) |
| `ui/sidebar.py` | 6330 | `4abb4de602c6be31` | untracked |
| `ui/header.py` | 3387 | `b842636f239c5b0b` | untracked |
| `ui/tie_card.py` | 7867 | `d2596b0507fc2f31` | untracked |
| `ui/bracket_view.py` | 9929 | `a39ae0750386dd94` | untracked |
| `ui/club_dialog.py` | 6038 | `5f7397ef50ae885f` | untracked |
| `tests/test_ui_overhaul.py` | 7980 | `efe0809a4d1b1599` | untracked (was missing) |
| `tests/test_ui_helpers.py` | 6568 | `0b501256c32160c8` | unchanged; still `import app` |

Not overwritten: `schema.sql`, `queries.py`, `clubs.py`, `seasons.py`, `build_database.py`, `european_football.db`, Polly's data files, `audits_004.md`, `audits_005.md`.

Scratch deleted: `_tmp.b64`, `_pack.b64`, `_write_b64.py`.

## Layout pins (still in `app.py`)

- `self.header.grid(row=0, column=1, ...)`
- `self.scroll.grid(row=1, column=1, ...)`
- sidebar `rowspan=2`
- `self.protocol("WM_DELETE_WINDOW", ...)`
- `load_club_name_cache` re-exported from `ui.formatters`

## Not committed

Working tree is not UI-only (untracked `notes/00_Audits/audits_001.md`--`audits_005.md` from other agents; Polly/GitHub files already at HEAD). No commit, no push, no `git config`.

`audits_001.md` was a shipment log written before this landing; a short "Landed on Hawkeye" section should be appended there. `audits_005.md` is the GitHub sync-manager note, left intact.

## Remaining gaps

- Bracket connectors are geometric (feeder midpoint), not a UEFA-printed-page facsimile.
- Penalty shoot-outs format (`pens 5-4`) but seed data has unused `home_pens`/`away_pens`.
- Match dates still sparse outside finals (data gap).
- Light-mode custom colours apply on toggle; some CTk chrome still follows the blue theme.
- Headed GUI smoke-test not run in this session.
- Working tree also has small uncommitted viewer-doc edits in `README.md`, `CHANGELOG.md`, and `ROADMAP.md` (10 insertions); not committed here because the tree is not UI-only.

## Final check (same evening)

After the overhaul commit `2ef6bb5` on local `feat/ui-ux-overhaul`, one source-pin test still required the contiguous phrase `python build_database.py` inside `app.py` (the helper lives in `ui/formatters.py`). The module docstring was adjusted to:

`Run:           python app.py   (if the .db is missing, run: python build_database.py)`

Retest: **84 passed** in 1.78s (Python 3.11). That one-line docstring pin is uncommitted (`app.py` dirty vs `2ef6bb5`). Not committed: working tree still has other agents' audit notes. Not pushed.

Branch note: UI files were committed on `feat/ui-ux-overhaul` (not `feat/database-engineer`) so Polly's database-engineer HEAD at `e2d0854` is untouched.
