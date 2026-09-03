# Changelog

## v1.3 - Group / Swiss phase foundations (additive)
- Schema: dition.points_for_win, dition.standings_tiebreak, 
ound.phase_type,
  plus standing_group / standing_member / standing_match, competition_transfer,
  and view _standing_results. Knockout 	ie / match unchanged.
- 	ools/standings.py derives rankings from fixtures (2- or 3-point editions,
  UEFA-style tie-breaks including head-to-head and Swiss strength-of-schedule).
- Parsers: 	ools/parse_group_stage.py, 	ools/parse_swiss_phase.py, shared
  	ools/phase_parse.py. Points-for-a-win is always an edition flag, never a year.
  Parsers do not write the database.
- Seeded 1991-92 European Cup group stage + final fragment (points_for_win=2).
  Parser fixtures: 	ools/fixtures/cl_1991_92_groups.rsssf and
  	ools/fixtures/swiss_miniature.rsssf.
- Classic Era 1955-60 golden lock tests; group/Swiss parser tests.
- Build populates the new columns/tables and verifies printed group tables.

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

## v1.1 — Classic Era, five-in-a-row
- Restructured seeding around a canonical club registry (`clubs.py`) keyed by
  short IDs, with fixtures in `seasons.py`. Adding a season is now one dict.
- Build-time verification: every tie's legs must reproduce RSSSF's printed
  aggregate, or the build aborts and writes nothing.
- Added European Cup **1956-57, 1957-58, 1958-59, 1959-60** (with 1955-56, the
  complete Real Madrid five-in-a-row): 76 clubs, 112 ties, 228 matches.
- Viewer: two-leg aggregate now excludes play-offs; play-offs, coin tosses and
  walkovers render distinctly.
- Docs: ROADMAP.md, DATA_GUIDE.md, CHANGELOG.md.

## v1.0 — Classic Era foundation
- SQLite schema for the unseeded two-legged knockout era.
- CustomTkinter season viewer with auto-aggregate and winner highlighting.
- Seeded the inaugural 1955-56 European Cup as a validation dataset.
