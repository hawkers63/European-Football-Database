# Changelog

## v1.6 - Classic competitions expansion
- Seeded and verified the inaugural Inter-Cities Fairs Cup **1955-58** (third
  and final v1.6 target edition): FC Barcelona beat London XI 8-2 on
  aggregate over a two-legged final. Sourced directly from RSSSF
  (`rsssf.org/ec/ec195758.html#icfc`). The lineage's first-ever edition
  turns the previously-empty menu entry (fixed earlier in v1.6) into a real
  competition. 9 new canonical clubs, several of them ad-hoc city
  representative XIs (the original Fairs Cup premise, before it settled
  into a normal club competition) rather than ordinary clubs.
  - The First Round was four small groups, not a straight knockout - two
    groups reduced to a single played tie after a third entrant withdrew
    without playing (Vienna XI, Cologne XI - named in prose only, no club
    registry entry since they never appear in a match); the other two were
    3-way round-robins, one producing two genuine drawn ties (`win=None`
    under `by="aggregate"`, already a supported shape).
  - `season_label="1955-58"` is the first multi-year label in the dataset;
    confirmed nothing in build/query/UI code parses its format beyond
    exact-match comparison, so no schema or code change was needed for it.
  - `lineage=3, club=130, edition=11, round=51, tie=238, match=477`.
- **Found and fixed** while exercising the CLI on this data: `cmd_season()`
  had the exact cursor-reuse bug already fixed in `_export_edition()` -
  `get_club_display_name()` reused the same cursor mid-iteration over a
  tie's legs, so `python cli.py season` only ever printed a tie's first
  leg regardless of how many it actually had. This affected every
  multi-leg tie already in the database, not just the new data.
- Seeded and verified European Cup **1962-63** (second of the three v1.6
  target editions): AC Milan won their first European Cup, beating holders
  Benfica 2-1 at Wembley. Sourced directly from RSSSF
  (`rsssf.org/ec/ec196263.html`), leg-by-leg cross-checked before entry.
  7 new canonical clubs. Reims played several home legs at Parc des
  Princes in Paris rather than their own ground; two ties (Servette-
  Feyenoord, Feyenoord-Vasas) went to a genuine two-legged-tie-plus-
  play-off replay, exercising the ordinary 3-leg `replay` shape alongside
  the new 2-leg agg=None shape from the CWC final.
  - `lineage=3, club=121, edition=10, round=48, tie=227, match=454`.
- Seeded and verified Cup Winners' Cup **1961-62** (first of the three v1.6
  target editions): Atlético Madrid won UEFA's first directly-organised
  Cup Winners' Cup, beating holders Fiorentina in a replayed final (1-1 aet
  at Hampden Park, then 3-0 in Stuttgart). Sourced directly from RSSSF
  (`rsssf.org/ec/ec196162.html`), cross-checked leg-by-leg against an
  independent account before entry. 15 new canonical clubs. Several
  fixtures were relocated to neutral venues for Cold War travel-restriction
  reasons (Motor Jena's East German away legs; Atlético's semi-final second
  leg moved to Sweden since Francoist Spain had no diplomatic relations
  with the GDR) - all recorded as leg notes.
  - Introduces a new settlement shape: `by="replay"` with `agg=None` for a
    single match that finished level and was replayed outright (a drawn
    cup final), as opposed to the existing two-legged-tie-plus-play-off
    shape. `verify()`'s Fix A settlement checks now branch on `agg is None`
    to validate each shape correctly (2 legs vs 3+).
  - `lineage=3, club=114, edition=9, round=43, tie=198, match=395`.
- Fixed `match.notes` being schema'd but never written. `queries.py`
  (`_MATCH_SELECT`, `hat_trick_notes()`) already read it, but
  `MATCH_INSERT_SQL` / `match_insert_tuple()` never included it, so
  per-leg detail (a hat-trick, an abandoned or relocated match) could only
  live on `tie.notes`. `L(..., notes="...")` now flows through to
  `match.notes` with no new helper needed. No existing season data moved -
  this is the write-path fix, not a data migration.
- Fixed the `lineage` table only getting rows for lineages with a seeded
  edition. The Inter-Cities Fairs Cup is configured in `LINEAGES` but has no
  season yet, so it never got inserted - `app.py`'s competition menu (which
  reads `lineage` directly, not via `edition`) and any other lineage-first
  tooling couldn't see it. `build_database.py` now inserts every entry in
  `LINEAGES` up front; `lineage` row count goes from 2 to 3. The menu now
  offers "Inter-Cities Fairs Cup" with an empty season list (`_on_season`
  already no-ops when there's no matching edition, so this doesn't crash).
- Fixed `club_name_history` attaching a club's period name to every edition
  sharing its season_label, regardless of lineage. `cwks_warsaw` (Legia
  Warsaw) and `wismut` only played the European Cup in 1960-61, but were
  also getting a history row on that year's Cup Winners' Cup edition, which
  they never entered. `build_database.py` now scopes each entry to editions
  the club actually contested (`_editions_contested_by`); `club_name_history`
  row count drops from 11 to 9 accordingly.
- Fixed the Vorwärts–Linfield 1961-62 Preliminary tie: it was stored as
  `decided_by=aggregate` with a single leg, which `verify()` could not catch
  (aggregate checks only sum legs, they don't require two of them). Now
  modelled as a walkover with zero legs, matching every other withdrawal in
  the dataset; the played 3-0 stays recorded in the tie's note. Match count
  drops from 352 to 351 accordingly.
- Established v1.5 as the completed working baseline and reconciled README,
  roadmap, release gates and agent task metadata with the live repository,
  ahead of the three-edition data programme above.

## v1.5 - European Cup 1961-62
- Seeded European Cup **1961-62** from RSSSF (James M. Ross): Benfica retained the
  trophy, beating Real Madrid 5-3 in Amsterdam.
- Eight new clubs in `clubs.py` (Nürnberg, Hibernians of Paola, Feyenoord,
  Górnik Zabrze, Tottenham, Monaco, B1913 Odense, Haka). Period names for
  Feijenoord and Valkeakosken Haka.
- Oddities recorded: Linfield withdrew after a 3-0 first leg; Vorwärts–Rangers
  2nd leg relocated to Malmö and replayed after fog; Juventus–Real Madrid
  play-off in Paris. Holders Benfica, Fenerbahçe and Haka had byes.
- `tools/import_rsssf.py` aliases extended for the new clubs (Hibernians must
  not fuzzy-match Hibernian Edinburgh).

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
