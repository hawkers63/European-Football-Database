# audits_002.md — QA & Bug Auditor findings

Date: 2026-09-03 (Europe/London)
Branch: `feat/database-engineer`
Executed: `agents/qa_auditor.md`

## Summary

Forensic QA pass on the Classic Era viewer and build pipeline. All eleven audit targets were confirmed and fixed. Automated tests: **50 passed**. `python build_database.py --force` rebuilt a clean database (lineage=1, club=76, edition=5, round=24, tie=112, match=228; European Cup 1955–60 aggregates verified against RSSSF).

## Defects (all confirmed)

| # | Defect | Severity | Fix |
|---|--------|----------|-----|
| 1 | Tie notes discarded when matches exist | High | Notes render in a distinct italic amber callout under scores (`compose_tie_detail`) |
| 2 | Match attendance ignored in extras | Medium | Append e.g. `135,000 spectators` via `format_attendance` |
| 3 | `edition.notes` / `runner_up_club_id` unused | Medium | Sidebar/header banner: Champions, Runner-up, edition notes |
| 4 | Header + scroll both `row=0, column=1` | High | Header `row=0`, scroll `row=1`; sidebar `rowspan=2` |
| 5 | Hardcoded `wraplength=680` | Low | `<Configure>` binding via `wraplength_for_width` |
| 6 | SQLite connection never closed | Medium | `WM_DELETE_WINDOW` closes cursor/conn then `destroy` |
| 7 | N+1 `SELECT name FROM club` per club per leg | Medium | Preload `club_id → name` cache in `_render_edition` |
| 8 | Third-club legs silently omitted in `verify()` | High | Fail verification if `h`/`aw` not in `(t1, t2)` |
| 9 | Unused `clubs.py` keys never warned | Low | stdout WARNING (currently 0 unused) |
| 10 | `INSERT INTO match` omitted `home_pens`/`away_pens` | Medium | Extract from extras; schema already had the columns |
| 11 | Replay/coin-toss header showed only aggregate | High | e.g. `5-5 (Replay: 7-0)` / `4-4 (Coin Toss)` |

## Proof

- `format_attendance(135000)` → `135,000 spectators` (Hampden 1960 final still stored as `attendance=135000`).
- `compose_tie_detail(['MTK 6-3 Anderlecht'], 'MTK competed as Vörös Lobogó this season.')` keeps the note when match parts exist.
- Wismut coin-toss note remains in the database and can render.
- Layout pins: `self.header.grid(row=0, column=1, ...)` / `self.scroll.grid(row=1, column=1, ...)`.

## Files touched (QA pass)

- `app.py`
- `build_database.py`
- `tests/__init__.py`
- `tests/test_integrity.py`
- `tests/test_ui_helpers.py`
- `pytest.ini`
- `schema.sql` inspected, unchanged (pens/attendance/notes/runner-up already present)

## Verification

```
cd C:\EuroDatabase
python -m pytest tests -q
python build_database.py --force
```

50 passed; rebuild exit 0.

## Remaining risks

- Wraplength tracks card `<Configure>`; no headed UI snapshot tests.
- Note callout italic depends on the platform font.
- No live season supplies `home_pens`/`away_pens`; INSERT path is unit-tested only.
- Unused-club warning is stdout-only (will not fail CI).
