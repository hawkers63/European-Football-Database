# Changelog

## v1.4 - Stats analyst (head-to-head, goals, leaderboards)
- Shared helpers in `queries.py` derive head-to-head records, goal statistics
  and all-time club leaderboards from `match` / `tie` / `edition` rows (no
  denormalised career-total tables).
- `python cli.py h2h` reports matches, W-D-L from each side, goals, ties
  contested, lineage breakdown, and labelled walkovers (not silent 3-0).
- `python cli.py goals [club] [--season YYYY-YY]` prints scored/conceded,
  goal difference, average goals per match, finals goals and highest-scoring
  ties; season mode totals goals by round. Hat-trick notes appear only when
  stored in `match` / `tie.notes`.
- `python cli.py leaderboard {titles|matches|finals}` ranks the loaded
  database (sort order documented in the command output and audits_008.md).
- `tests/test_stats.py` rebuilds a fresh temporary database; covers H2H
  symmetry, Classic Era 1955-60 title facts, and leaderboard totals vs SQL.
- `build_database.build(..., db_path=)` lets tests rebuild without touching
  the working `european_football.db`.

## v1.3 - UI/UX overhaul
- Modular `ui/` package: sidebar, header, rich tie cards, knockout bracket, club profile.
- Fixtures List and Tournament Bracket views; columns follow `round_order`.
- Period-accurate names on every club label via a batched `get_club_display_name` cache.
- Yearbook colours (victory green #2ea043, brass gold #d4af37) with a Dark/Light toggle.
- Missing `european_football.db` shows an in-window instruction to run `python build_database.py`.

## v1.2 - Period names, multi-lineage, CLI & RSSSF import
- Additive `club_name_history` table with `get_club_display_name(club_id, edition_id)`
  (MTK 1955-56 displays as *Vörös Lobogó*; later seasons stay *MTK Budapest*).
- `LINEAGES` config (`lineages.py`) replaces the hardcoded European Cup lineage note;
  Cup Winners' Cup and Inter-Cities Fairs Cup notes included.
- Seeded European Cup **1960-61** (Benfica beat Barcelona) and inaugural
  European Cup Winners' Cup **1960-61** (Fiorentina beat Rangers), from RSSSF.
- Build verifies `by == 'away_goals'` when aggregates are level; pens columns
  continue to be populated from leg extras.
- New `cli.py` (`club`, `h2h`, `season`, `export --format json`) and
  `tools/import_rsssf.py` for drafting season blocks from RSSSF text.

## v1.1 - Classic Era, five-in-a-row
- Restructured seeding around a canonical club registry (`clubs.py`) keyed by
  short IDs, with fixtures in `seasons.py`. Adding a season is now one dict.
- Build-time verification: every tie's legs must reproduce RSSSF's printed
  aggregate, or the build aborts and writes nothing.
- Added European Cup **1956-57, 1957-58, 1958-59, 1959-60** (with 1955-56, the
  complete Real Madrid five-in-a-row): 76 clubs, 112 ties, 228 matches.
- Viewer: two-leg aggregate now excludes play-offs; play-offs, coin tosses and
  walkovers render distinctly.
- Docs: ROADMAP.md, DATA_GUIDE.md, CHANGELOG.md.

## v1.0 - Classic Era foundation
- SQLite schema for the unseeded two-legged knockout era.
- CustomTkinter season viewer with auto-aggregate and winner highlighting.
- Seeded the inaugural 1955-56 European Cup as a validation dataset.
