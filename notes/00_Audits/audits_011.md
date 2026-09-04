# audits_009 — Modern-era parser Phase 2b (Hawkeye)

**Branch:** `feat/modern-era-parser`  
**Worktree:** `C:\EuroDatabase-parser`  
**Date:** 3 September 2026 (Europe/London)  
**Note:** `audits_008.md` is reserved for the stats track; this report is 009.

## What landed

### Schema (additive only)
- `edition.points_for_win`, `edition.standings_tiebreak`
- `round.phase_type` (`knockout` | `group` | `league`)
- `standing_group`, `standing_member`, `standing_match`
- `competition_transfer` (mid-season movement as data)
- View `v_standing_results`
- Knockout `tie` / `match` unchanged. Rankings are derived, never stored.

### Build
- `build_database.py` populates the new columns/tables.
- Verifies printed group tables via `tools/standings.py` when supplied.
- Classic Era knockout path unchanged (`points_for_win` NULL).

### Parsers & engine
- `tools/standings.py` — shared sorter (2/3 pts, H2H, Swiss strength-of-schedule).
- `tools/phase_parse.py` — shared RSSSF block parser.
- `tools/parse_group_stage.py` — group blocks → season fragments.
- `tools/parse_swiss_phase.py` — league-phase listings → fragments + transfers.
- Fixtures: `tools/fixtures/cl_1991_92_groups.rsssf`, `tools/fixtures/swiss_miniature.rsssf`.

### Seed data
- Clubs: `sampdoria`, `sparta_prague`, `dynamo_kyiv` (+ RSSSF aliases).
- Season fragment: European Cup **1991-92** group stage + final (`points_for_win=2`).
- **1955-60 golden data in `seasons.py` was not mutated.**

### Tests & docs
- `tests/test_classic_era_golden.py`, `test_group_stage_parser.py`, `test_swiss_phase_parser.py`
- Integrity extended for additive schema + 1991-92 seed.
- `DATA_GUIDE.md`, `CHANGELOG.md` (v1.3), `ROADMAP.md` ticks for completed items.

## Deliberately not done
- Full 36-club 2024-25 Swiss ingest.
- Viewer league-table rendering.
- Continuing Classic Era season seeding beyond existing coverage.
- Helper scripts `_patch_*.py` deleted; not committed.

## Safety
- Worktree only: `C:\EuroDatabase-parser`.
- No force-push; `european_football.db` gitignored; parsers do not write the DB.

## Parallel note
udits_008.md is reserved for the stats track. A leftover draft with that
name was left untracked and is not part of this commit.
