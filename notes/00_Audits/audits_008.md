# audits_008.md - Modern Era Parser (Phase 2b)

Date: 2026-09-03 (Europe/London)
Branch: `feat/modern-era-parser`
Worktree: `C:\EuroDatabase-parser` (from `feat/database-engineer`; does not touch `feat/stats-analyst`)
Executed: `agents/modern_era_parser.md`

## Proposal

Tournament structure is data, not code. Classic Era knockout `tie` / `match`
rows stay the golden foundation. 1990s Champions League group stages and the
36-club Swiss league phase are additive tables plus parsers, so the 1955-60
Real Madrid five-in-a-row cannot be rewritten to make a new format parse.

## What was implemented

### Schema (additive)

- `edition.points_for_win` (2 or 3, NULL on knockout-only editions)
- `edition.standings_tiebreak` (comma-separated criteria; never a calendar year)
- `round.phase_type` (`knockout` | `group` | `league`, default `knockout`)
- `standing_group`, `standing_member`, `standing_match`
- `competition_transfer` (mid-season movement between trophy lines)
- view `v_standing_results` (fixtures only; ranking is derived in Python)

### Parsers

- `tools/parse_group_stage.py` — RSSSF group-stage blocks
- `tools/parse_swiss_phase.py` — Swiss / league-phase listings + Transfers
- `tools/standings.py` — shared ranking engine
- `tools/phase_parse.py` — shared RSSSF match/table line parser
- Dry-run only; they do not write `european_football.db`

```
python tools/parse_group_stage.py tools/fixtures/cl_1991_92_groups.rsssf --season 1991-92 --points-for-win 2 --dry-run
python tools/parse_swiss_phase.py tools/fixtures/swiss_miniature.rsssf --season 2024-25 --points-for-win 3 --dry-run
```

### 1990s fragment

European Cup 1991-92 group stage (RSSSF: two groups of four, **2 points for a
win**) plus the Wembley final (Barcelona 1-0 Sampdoria aet). First Champions
League group phase; UEFA switched that competition to 3 points in 1995-96 —
stored as the edition flag, not hard-coded.

Fixture: `tools/fixtures/cl_1991_92_groups.rsssf`

### Swiss model

Schema + parser + tests prove 36 clubs × eight opponents, UEFA-style
tie-breakers, incomplete fixtures, and transfer links. A full 36-club ingest
is not seeded; `tools/fixtures/swiss_miniature.rsssf` is the documented dry-run.

### Golden data

Regression tests lock European Cup 1955-56 through 1959-60 champions (Real
Madrid), runners-up, tie/leg counts, final aggregates, and the Hampden Park
1960 attendance of 135000. Those seasons were not rewritten.

## Verification

- `python -m pytest tests -q`
- `python build_database.py --force`
- 1955-60 champions, aggregates, and notes unchanged

## Constraints honoured

- Worktree only; `C:\EuroDatabase` (`feat/stats-analyst`) left dirty and unmoved.
- No force-push. No push to `main`.
- No mutation of Classic Era 1955-60 seasons.
- Parsers do not write `european_football.db` except via `build_database.py --force`.
