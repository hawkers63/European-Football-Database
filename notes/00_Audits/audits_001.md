# audits_001.md - UI/UX Desktop Application Specialist shipment

Date: 2026-09-03 (Europe/London)
Branch: `feat/ui-ux-overhaul` (fast-forwarded onto `feat/database-engineer` @ e2d0854; originally cut from 84cbb1f)

## Features shipped

- Modular `ui/` package: sidebar, header, rich tie cards, knockout bracket, club profile dialog, yearbook palette, batched data loaders.
- Period-accurate club names on every on-screen label via a per-edition cache that mirrors `queries.get_club_display_name` (MTK 1955-56 displays as Vörös Lobogó). Canonical name plus `club_name_history` aliases appear on the club profile.
- Fixtures List and Tournament Bracket view modes. Bracket columns follow `round_order` (not round name), draw connectors from winning feeders, and tolerate byes, walkovers, 4- vs 5-round seasons, and missing feeders. Click a node for a legs inspector (venues, dates, attendances).
- Rich cards: country pills using stored association codes (FRG/GDR/TCH/SAA/YUG/ESP/FRA), score pill with existing `format_score_header` behaviour, per-leg aet/pens badges, metadata badges, notes callout with an info icon (no CTk italic fonts).
- Club names are clickable and open a profile: record (ties, wins, losses, titles, runner-up finishes) and match history from batched SQL.
- Yearbook colours: victory green `#2ea043`, brass gold `#d4af37`, Dark/Light toggle.
- Performance: one long-lived SQLite connection (Row factory, `PRAGMA foreign_keys=ON`); prefetch all matches for the edition and aggregate in Python; in-memory search; CTkOptionMenu `.set()` guarded so it does not double-render.
- Missing `european_football.db` shows an in-window instruction to run `python build_database.py` (no `sys.exit`).
- Write-gated `<Configure>` wraplength on tie cards kept.

## Files added

- `ui/__init__.py`
- `ui/theme.py`
- `ui/formatters.py` (helpers; re-exported from `app.py`)
- `ui/data.py`
- `ui/sidebar.py`
- `ui/header.py`
- `ui/tie_card.py`
- `ui/bracket_view.py`
- `ui/club_dialog.py`
- `tests/test_ui_overhaul.py`

## Files changed

- `app.py` — shell only (connect, caches, navigation, wiring, missing-db window, mainloop). Layout pins kept: header row 0, scroll row 1, sidebar `rowspan=2`, `WM_DELETE_WINDOW`.
- `tests/test_ui_helpers.py` — unchanged; still `import app`.
- `ROADMAP.md` — bracket-view item ticked.
- `CHANGELOG.md` — v1.3 UI/UX overhaul.
- `README.md` — `ui/` package noted in the file table.

## How to run

```
cd C:\EuroDatabase
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe app.py
```

If the database is missing: `python build_database.py` then launch `app.py` again.

## Verification

- `python -m pytest`: **84 passed** (Polly's database tests plus new UI helper tests).
- `App()` constructed and destroyed on Hawkeye (headed session available).
- Helpers re-exported: `app.WIN == "#2ea043"`, `app.NOTE == "#d4af37"`.

## Remaining gaps

- Bracket connectors are geometric (feeder midpoint), not a UEFA-printed-page facsimile; irregular early rounds (11 qualifying ties into 8) will show leftover space rather than a perfect binary tree.
- Penalty shoot-outs are formatted (`pens 5-4`) but none are present in the current seed data (`home_pens`/`away_pens` unused in the DB).
- Match dates are still sparse outside finals (data gap, not a UI gap).
- Light-mode custom colours are applied on toggle; a few native CTk chrome bits still follow the blue theme.
- Concurrent untracked audit notes (`audits_002.md` onwards) from other agents were left untouched and are not part of this commit.

## Landed on Hawkeye

Date: 2026-09-03 22:40 BST (Europe/London)

Modular viewer is now on `C:\EuroDatabase` (`feat/database-engineer` working tree). `app.py` is the 10,873-byte shell; `ui/` includes `data.py` and `bracket_view.py`; `tests/test_ui_overhaul.py` is present. pytest: 84 passed. Details: `audits_006.md`.
