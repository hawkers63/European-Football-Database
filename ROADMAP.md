# Roadmap

The database treats tournament structure as data. The knockout foundation stays
stable while new competitions, seasons and phase types are added around it. This
keeps the verified Classic Era records usable as the project grows into group
stages and the modern league phase.

## Current verified snapshot

The v1.7 working baseline contains:

- 3 seeded competition lineages, 11 editions and 130 canonical clubs;
- 51 rounds, 238 ties and 477 matches (unchanged from v1.6 - v1.7 added no
  new season data);
- European Cup coverage from **1955-56 through 1962-63**;
- European Cup Winners' Cup coverage from the inaugural **1960-61** through
  **1961-62**;
- the inaugural Inter-Cities Fairs Cup **1955-58**;
- 182 passing automated tests; and
- a clean SQLite integrity check with aggregate and foreign-key validation.

The generated row counts are a point-in-time snapshot. They must be refreshed
whenever a season is added.

## Delivered releases

### v1.0 — Classic Era foundation

- [x] Created the SQLite knockout schema for lineages, editions, rounds, ties,
      matches and clubs.
- [x] Modelled two-legged ties, single-match finals, replays, coin tosses,
      walkovers and byes without hardcoding a tournament format in the UI.
- [x] Seeded the inaugural European Cup **1955-56** as the first complete
      validation season.
- [x] Shipped the first CustomTkinter season browser with calculated aggregates
      and winner highlighting.

### v1.1 — Five-in-a-row dataset and build verification

- [x] Reworked the source data around a canonical, keyed club registry and
      season dictionaries.
- [x] Added European Cup **1956-57 through 1959-60**, completing Real Madrid's
      five consecutive titles.
- [x] Added build-time verification: each tie's legs must reproduce the printed
      RSSSF aggregate before the database is committed.
- [x] Correctly represented play-offs, walkovers and coin-toss decisions in the
      generated data and viewer.

### v1.2 — Period names, multiple lineages and data tooling

- [x] Added `club_name_history` and period-accurate display-name queries.
- [x] Moved trophy identities into `LINEAGES`, including definitions for the
      European Cup, Cup Winners' Cup and Inter-Cities Fairs Cup.
- [x] Seeded the European Cup **1960-61** and the inaugural Cup Winners' Cup
      **1960-61**.
- [x] Added the command-line interface for club records, head-to-head results,
      season reports and JSON export.
- [x] Added the RSSSF drafting tool with alias matching, leg-orientation handling
      and aggregate checks.
- [x] Preserved penalty-shootout fields and enforced valid away-goals decisions
      in the build pipeline.

### v1.3 — Desktop viewer overhaul

- [x] Split the viewer into a modular `ui/` package.
- [x] Added Fixtures List and Tournament Bracket views, ordered by the stored
      round sequence.
- [x] Added searchable match cards, period-accurate club labels and clickable
      club profiles with match history.
- [x] Added champion and runner-up context, edition notes, attendance, venue,
      referee and historical tie-note rendering.
- [x] Added the yearbook-inspired light/dark theme and a clear in-window message
      when the generated database is missing.
- [x] Removed repeated per-club lookups, fixed layout overlap and dynamic text
      wrapping, and closed the SQLite connection cleanly on exit.

### v1.4 — Derived statistics

- [x] Added shared query helpers for head-to-head records, goal statistics and
      all-time club leaderboards.
- [x] Added CLI reports for goals, titles, matches, wins, goal difference and
      finals reached, all derived from match and edition rows.
- [x] Kept walkovers explicit and prevented unrecorded scorer or hat-trick data
      from being inferred.
- [x] Made database builds redirectable to a temporary path so tests never need
      to overwrite the working database.

### v1.5 — European Cup 1961-62

- [x] Seeded and verified the complete European Cup **1961-62**, including all
      55 match dates.
- [x] Added eight participating clubs and period names for Feijenoord and
      Valkeakosken Haka.
- [x] Recorded the season's withdrawals, byes, relocated fixture, abandoned leg
      and Juventus-Real Madrid play-off.
- [x] Extended importer aliases to distinguish Hibernians of Paola from
      Hibernian of Edinburgh.

### v1.6 — Classic competitions expansion

- [x] Seeded and verified European Cup **1962-63** (AC Milan's first title,
      beating holders Benfica at Wembley).
- [x] Seeded and verified Cup Winners' Cup **1961-62** (Atlético Madrid, after
      a replayed final against holders Fiorentina).
- [x] Seeded and verified the inaugural Inter-Cities Fairs Cup **1955-58**
      (Barcelona) - the lineage's first edition, mixing real clubs with
      ad-hoc city representative XIs across a four-group First Round.
- [x] Extended `verify()` with settlement-shape checks (single_match,
      replay/coin_toss, walkover/bye and a one-leg "aggregate" are all now
      rejected when their leg count doesn't match `decided_by`) - the exact
      class of bug behind the Vorwärts-Linfield fix earlier in this release.
- [x] Made `build_database.py --force` atomic: it rebuilds into a temporary
      file and only replaces the working database after `verify()` passes,
      so a failed rebuild can no longer delete the last known-good database.
- [x] Fixed a cursor-reuse bug in `cli.py` (`_export_edition()` and
      `cmd_season()`) that silently truncated JSON exports and printed only
      a tie's first leg regardless of how many it actually had.
- [x] `tools/import_rsssf.py` now reports ignored non-blank lines by number
      instead of silently dropping malformed input during bulk transcription.
- [x] 31 new canonical clubs across the three editions.
- [ ] Edition-level source provenance in a machine-checkable form, and a
      measured match-date backfill for pre-1961-62 editions, are deferred to
      a future data pass rather than blocking this release.

### v1.7 — Yearbook navigation and statistics wiring

- [x] Added `club_campaign()`, `edition_chronology()` and
      `winner_path_club_ids()` query helpers, plus `cli.py path <club>
      <season>` and `cli.py chronology <season>` subcommands.
- [x] `LEADERBOARD_KINDS` now includes `wins` and `gd` - the underlying
      leaderboard functions already existed but weren't exposed to the CLI.
- [x] `club_record()`'s hat-trick notes are now scoped to `season_label`
      when given, instead of always being all-time.
- [x] `verify()` rejects `decided_by=away_goals` when the edition's
      `away_goals_active` flag is false, ahead of any 1965-66+ seeding.
- [x] The desktop viewer's club profile now reuses `queries.club_campaign()`
      for a new "Campaign" section (that club's route through the currently
      loaded season, including walkovers) - the first place the viewer
      consumes a shared `queries.py` helper instead of its own SQL.
- [x] Ties on the tournament champion's route are outlined in victory green
      on both the fixtures list and the bracket.

### Engineering baseline completed across v1.x

- [x] Added regression coverage for database integrity, the build pipeline,
      display names, RSSSF import, statistics and display-free UI helpers.
- [x] Hardened validation against unknown clubs in legs, invalid winners,
      malformed settlement types, duplicate clubs and unused registry entries.
- [x] Added GitHub Actions gates for a clean database rebuild and the full test
      suite on pushes and pull requests.
- [x] Added agent briefs, a GitHub issue template and a local GitHub parity
      checker for repeatable specialist work.

## Completed work awaiting integration

### Modern-era parser prototype

The remote `feat/modern-era-parser` branch at `ddd27c0` contains substantial
v2.0/v3.0 groundwork, but it is not part of the v1.5 baseline:

- [x] Additive phase, standings and competition-transfer schema prototypes.
- [x] Per-edition points and ordered standings-tiebreak configuration.
- [x] Deterministic group-table calculations and RSSSF group-stage parsing.
- [x] A 1991-92 European Cup group-stage source fragment and regression tests.
- [x] A Swiss/league-phase parser with a miniature validation fixture.
- [ ] Reconcile the branch with the v1.5 statistics and 1961-62 data changes.
- [ ] Review and merge it through the v2.0 release gates before treating those
      schema and parser capabilities as shipped.

This work stays separate from v1.6 so the next Classic Era data release remains
small and reviewable.

## Planned releases

### v2.0 — Group Stage Era

**Goal:** support tournaments that mix knockout rounds with one or more groups,
using additive schema changes that leave existing ties and matches intact.

Planned scope:

- [ ] Integrate and review the existing phase, group-membership, points-system
      and ordered-tiebreak prototype against the current v1.x baseline.
- [ ] Promote the group-table and RSSSF parser prototypes from miniature/source
      fragments to a complete, reproducible pilot edition.
- [ ] Add CLI and JSON representations for group tables.
- [ ] Render group tables alongside the existing fixture and bracket views.
- [ ] Use the **1991-92 European Cup** as the first mixed knockout/group
      validation edition before adding further Champions League seasons.

Release gates:

- Rebuilding and querying all v1.x knockout editions produces the same verified
  results as before the migration.
- Group-table tests cover points, every configured tiebreak, incomplete groups
  and equal-record edge cases.
- The pilot edition can be inspected end to end in the database, CLI and viewer.

Not in scope: the 36-team single-league phase or movement between competitions.

### v3.0 — Modern League Phase

**Goal:** represent current UEFA formats without special-casing one season in
application code.

Planned scope:

- [ ] Integrate the existing league-phase schema/parser prototype after v2.0 is
      stable.
- [ ] Expand the miniature fixture into a complete 36-team league phase with
      eight scheduled opponents per club and matchday-aware fixtures.
- [ ] Store and verify the full, ordered UEFA league-phase tiebreak policy as
      edition data.
- [ ] Model qualification bands and movement from the league table into the
      knockout play-off and round of 16.
- [ ] Model documented movement between competition lineages where a season's
      rules require it.
- [ ] Apply the existing per-edition away-goals flag across historical knockout
      seasons, including its introduction and later abolition, with boundary
      regression tests.
- [ ] Add scalable table, qualification-band and downstream-bracket views for a
      complete modern edition.

Release gates:

- A complete 36-team edition rebuilds from source, reproduces its published
  table and qualification positions, and renders without manual corrections.
- Classic knockout and v2.0 group-stage regression suites remain green.

## Release discipline

Every data or schema release must:

1. keep canonical club identities and competition lineages consistent;
2. derive aggregates and statistics from verified match rows;
3. preserve the Classic Era golden-data tests;
4. keep UI changes separate from data-calibration changes where practical; and
5. pass the database rebuild and full automated test suite before merge.

## Data source

Historical results are transcribed from **RSSSF** (the Rec.Sport.Soccer
Statistics Foundation), James M. Ross's European competition pages. RSSSF content
is free to reproduce with acknowledgement.
