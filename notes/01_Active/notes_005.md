# notes_005 — Next five releases: one feature each

**Date:** 4 September 2026  
**Author:** Mark  
**Scope:** Read-only survey of the v1.5 baseline and documented expansion plans.  
**Constraint:** No existing file was modified, moved, renamed or deleted. This note is the only new artefact.

---

## Executive summary

The working baseline is **v1.5**, as recorded in [`ROADMAP.md`](../../ROADMAP.md), [`README.md`](../../README.md), [`CHANGELOG.md`](../../CHANGELOG.md) and [`DATA_GUIDE.md`](../../DATA_GUIDE.md). Verified snapshot:

| Measure | Count |
|---------|------:|
| Seeded competition lineages | 2 (European Cup; European Cup Winners' Cup) |
| Configured lineages in `LINEAGES` | 3 (Inter-Cities Fairs Cup inserted at build time, still unseeded) |
| Editions | 8 |
| Canonical clubs | 99 |
| Rounds | 38 |
| Ties | 176 |
| Matches | 351 |
| Automated tests | 119 passing |
| European Cup coverage | 1955-56 through 1961-62 |
| Cup Winners' Cup coverage | inaugural 1960-61 only |

The generated SQLite file rebuilds cleanly (`PRAGMA integrity_check = ok`; empty `foreign_key_check`). Aggregates are computed, never stored. Classic Era golden data (European Cup **1955-56 through 1959-60**) remains the immutable regression floor.

Active unreleased work lives under **v1.6 Classic competitions expansion** in `CHANGELOG.md`: the `match.notes` write path, insertion of every configured lineage (so the Fairs Cup appears in the competition menu), scoping of `club_name_history` to editions a club actually contested, and the Vorwärts–Linfield 1961-62 settlement recast as a walkover (match count 352 → 351). Those pipeline fixes are in the tree; the three target editions are not.

Long-term milestones are unchanged: **v2.0 Group Stage Era** (unintegrated `feat/modern-era-parser` at `ddd27c0`) and **v3.0 Modern League Phase**. [`ROADMAP.md`](../../ROADMAP.md) does not currently name **v1.7** or **v2.1**. This note proposes them so that each of the next five releases owns exactly one high-value feature, drawn only from documented plans, unintegrated prototypes and recorded gaps.

**Save destination:** [`notes/01_Active/notes_005.md`](notes_005.md) (directory write succeeded; no download fallback).

Release sequence proposed here:

| Release | Feature |
|---------|---------|
| **v1.6** | Classic competitions expansion (EC 1962-63, CWC 1961-62, Fairs Cup 1955-58) |
| **v1.7** | Yearbook campaign path, edition chronology and champion-route overlay |
| **v2.0** | Group Stage Era: merge the parser prototype and complete the 1991-92 European Cup |
| **v2.1** | Group-table desktop viewer and group-era continuation |
| **v3.0** | Modern 36-team league phase, qualification bands and cross-lineage movement |

Group-stage and Swiss-format work stays out of every v1.x release, matching the ROADMAP v1.6 “not in scope” clause and the [`season_seeder.md`](../../agents/season_seeder.md) / [`modern_era_parser.md`](../../agents/modern_era_parser.md) split.

---

## Feature 1 — Classic competitions expansion

- **Title:** Seed and verify European Cup 1962-63, Cup Winners' Cup 1961-62, and the inaugural Inter-Cities Fairs Cup 1955-58.
- **Target Release:** v1.6

### Codebase source and evidence

This is the documented next data programme, not an inferred gap:

- [`ROADMAP.md`](../../ROADMAP.md) § “Planned releases / v1.6 — Classic competitions expansion”: seed EC **1962-63**, CWC **1961-62**, and the first Fairs Cup edition (**1955-58**); add clubs, period names, importer aliases and documented oddities; store full match dates when the source provides them and begin a measured backfill; record edition-level source provenance in a machine-checkable form; refresh README and data-guide coverage figures.
- [`CHANGELOG.md`](../../CHANGELOG.md) “Unreleased - v1.6”: “Next data targets are European Cup **1962-63**, Cup Winners' Cup **1961-62** and the inaugural Inter-Cities Fairs Cup **1955-58**.”
- [`DATA_GUIDE.md`](../../DATA_GUIDE.md) lines 8–10: the v1.6 queue is those three editions.
- [`agents/season_seeder.md`](../../agents/season_seeder.md) Tasks 2–4 and Deliverable 1: same three targets; 1961-62 is complete; Fairs Cup reuses the configured lineage rather than inventing a rebrand year.
- [`lineages.py`](../../lineages.py): Inter-Cities Fairs Cup is already a trophy thread (“Predecessor to the UEFA Cup / UEFA Europa League (1955 to 1971)”) but has no season dictionary in [`seasons.py`](../../seasons.py).
- [`notes/01_Active/notes_002.md`](notes_002.md) recommended next-step 8 and [`notes/01_Active/notes_003.md`](notes_003.md) recommended next-step 6: resume Classic Era coverage with those three editions as independently reviewable pull requests, accommodating the Fairs Cup’s multi-year edition label.
- [`notes/00_Audits/audits_009.md`](../00_Audits/audits_009.md): “Inter-Cities Fairs Cup is in LINEAGES but unseeded in seasons.py — Jenny/season seeder territory.”
- [`notes/01_Active/notes_004.md`](notes_004.md) Finding 7: 1961-62 byes (Benfica, Fenerbahçe, Haka) are documented in notes but not modelled as `bye` ties — a known modelling gap to resolve as v1.6 seeding proceeds, not by inventing RSSSF participant lists.

Unreleased v1.6 pipeline work already landed in the tree and must not be re-done: `MATCH_INSERT_SQL` / `match_insert_tuple()` now persist `match.notes`; `build_database.py` inserts every `LINEAGES` entry up front; `_editions_contested_by()` scopes period names; Vorwärts–Linfield is a walkover with zero legs.

### Technical specification

Architectural touchpoints (additive only; no group tables, no Swiss logic, no broad UI redesign):

| Surface | Work |
|---------|------|
| [`seasons.py`](../../seasons.py) | Append three season dictionaries under the existing public `SEASONS` contract. Fairs Cup **1955-58** uses a multi-year `season_label` (not a hard-coded rebrand). Treat 1955-60 European Cup dictionaries as immutable golden data. |
| [`clubs.py`](../../clubs.py) | New canonical keys only; period names via `CLUB_NAME_HISTORY`, never free-text aliases as identity. |
| [`lineages.py`](../../lineages.py) | Reuse the existing Fairs Cup entry; do not add a fourth lineage for this release. |
| [`tools/import_rsssf.py`](../../tools/import_rsssf.py) | Draft `L()` blocks; extend aliases so new clubs do not fuzzy-match existing ones (precedent: Hibernians of Paola vs Hibernian of Edinburgh in v1.5). Report ignored non-blank lines by line number ([`notes_002.md`](notes_002.md) Finding 7) before the importer is relied on for bulk transcription. |
| [`build_database.py`](../../build_database.py) `verify()` | Extend settlement checks as specified in [`notes_004.md`](notes_004.md) Fix A (`single_match`, `replay` / `coin_toss`, `walkover` / `bye`, one-leg “aggregate”). Current `verify()` (from line 224) still only recomputes two-leg aggregates and away-goals winners. |
| `edition` / `schema.sql` | Record edition-level source provenance in a consistent, machine-checkable form (ROADMAP v1.6). Prefer an additive nullable column or a structured `edition.notes` convention — not a rewrite. Do not invent missing attendance or referee data. |
| [`cli.py`](../../cli.py) `_export_edition()` | Nested `cur.execute()` loops still reuse a single lazy cursor ([`notes_002.md`](notes_002.md) blocker 1). Materialise with `fetchall()` (or a fresh cursor per loop) so 1955-56 exports 4 rounds / 15 ties / 29 matches, and include `match.notes` on exported legs. |
| Atomic rebuild | `build(force=True)` still `os.remove`s the destination before verifying ([`notes_002.md`](notes_002.md) blocker 3). Validate a temporary sibling, then replace only after source, aggregate, foreign-key and integrity checks pass. |
| Docs | Refresh [`README.md`](../../README.md) and [`DATA_GUIDE.md`](../../DATA_GUIDE.md) coverage figures after the rebuild. |

Optional but in ROADMAP v1.6 scope: backfill ISO `match_date` for earlier editions where RSSSF provides them. The 1961-62 European Cup is already fully dated (55/55); [`notes_002.md`](notes_002.md) recorded 63 dated matches of 352 at the then-current snapshot. Do not fabricate dates.

### Prioritisation rationale

v1.6 is already the named next release. The knockout schema, club registry, multi-lineage model, RSSSF importer and viewer are complete through v1.5; the remaining v1.x work is **data**, not architecture ([`season_seeder.md`](../../agents/season_seeder.md) §1). Mixing the `feat/modern-era-parser` schema into this release would violate ROADMAP’s “not in scope” clause and the instruction that Classic Era data releases remain small and reviewable. The three editions also turn the already-inserted Fairs Cup lineage from an empty menu entry into a queryable competition, which is the last configured trophy line without a season.

### Verification and release gate criteria

- `python build_database.py --force` completes with every printed aggregate verified, no foreign-key violations, and the last known-good database preserved if verification fails.
- `python -m pytest -q` passes, including champion, runner-up and at least one representative aggregate for **each** new edition, plus Classic Era 1955-60 golden-data regressions unchanged.
- Fairs Cup 1955-58 is visible in `python cli.py season 1955-58` (or the edition’s chosen label) and in the viewer competition menu.
- `python cli.py export 1955-56 --format json` yields exactly 4 rounds, 15 ties and 29 matches; `python cli.py export 1960-61 --format json` returns both lineages without truncation.
- `PRAGMA integrity_check` is `ok`; unused-club warning is empty.
- European Cup 1955-56 through 1959-60 dictionaries, notes, attendances and club keys are byte-for-byte equivalent in verified aggregates.
- README / DATA_GUIDE coverage figures match the post-rebuild `build_database.py` report.

---

## Feature 2 — Yearbook campaign path, chronology and champion-route overlay

- **Title:** Club campaign path, dated edition chronology, and champion-route highlighting over the existing knockout viewer.
- **Target Release:** v1.7

### Codebase source and evidence

v1.7 is not named in ROADMAP. It is assembled from unintegrated prototypes and recorded product gaps that are explicitly **not** group-stage work and that notes_004 asked to land after the v1.6 pipeline fixes:

- [`notes/01_Active/notes_004.md`](notes_004.md) Feature 1 (`club_campaign` / `python cli.py path benfica 1961-62`): a club’s rounds, opponents, settlements and scorelines in one edition — “the yearbook page that stakeholders are particularly interested in when selecting a club.” The function is specified in full; it does not exist in [`queries.py`](../../queries.py).
- [`notes/01_Active/notes_004.md`](notes_004.md) Feature 2 (`edition_chronology` / `python cli.py chronology`): dated matches only, oldest to newest, with a dated/total coverage footer so the v1.6 date backfill has a measurable threshold. Undated rows are omitted, never invented.
- [`notes/01_Active/notes_004.md`](notes_004.md) Feature 3 (`winner_path_club_ids`): highlight the champion’s route on the existing fixtures list and bracket using the yearbook victory-green token (`#2ea043` in [`ui/theme.py`](../../ui/theme.py)); no new widget class.
- [`notes/01_Active/notes_004.md`](notes_004.md) Finding 5 / Fix D: `leaderboard_wins` and `leaderboard_goal_difference` exist and `LEADERBOARD_SORT` documents `wins` / `gd`, but `LEADERBOARD_KINDS` in [`queries.py`](../../queries.py) line 20 is still `("titles", "matches", "finals")` and [`cli.py`](../../cli.py) `cmd_leaderboard` only prints those three.
- [`notes/01_Active/notes_004.md`](notes_004.md) Finding 6 / Fix E: `club_record(..., season_label=)` does not scope `hat_trick_notes()` ( [`queries.py`](../../queries.py) line 384 still calls `hat_trick_notes(db, club_id=club_id)`).
- [`notes/00_Audits/audits_008.md`](../00_Audits/audits_008.md) remaining gaps: “The viewer does not yet call the new helpers (club profile still uses its own batched SQL).” [`ui/club_dialog.py`](../../ui/club_dialog.py) is fed by `ui.data.fetch_club_profile`; nothing in `ui/` imports the stats helpers from `queries.py` (only tests do, besides `cli.py`).
- [`agents/stats_analyst.md`](../../agents/stats_analyst.md) Task 3: leaderboards must be reusable functions “so the CustomTkinter viewer can consume the same numbers later.”
- [`notes/01_Active/notes_000.md`](notes_000.md): the original product thesis is a digital *Yearbook of European Football* — campaign pages, dated chronologies and a highlighted winner’s path are that thesis, not a new architecture.
- ROADMAP v1.6 “Not in scope: group tables, Swiss-format logic or a broad UI redesign” — this feature is query/CLI plus a highlight flag on existing cards, which is why it waits until the v1.6 data programme is green rather than inflating that release.

Related sequencing constraint (not the title feature, but a documented hard gate on the same Classic Era track): [`agents/database_engineer.md`](../../agents/database_engineer.md) Task 3, [`notes_002.md`](notes_002.md) item 6 and [`notes_003.md`](notes_003.md) §7 require `verify()` to reject `decided_by='away_goals'` when `edition.away_goals_active` is false **before** seeding reaches 1965-66. ROADMAP currently parks the full historical flag programme in v3.0, which is too late for Classic Era continuation. v1.7 should land the verifier (positive and negative tests against the flag) even if no 1965-66 edition is seeded in this release.

### Technical specification

No new tables. Shared helpers first; CLI and viewer consume the same functions.

| Surface | Work |
|---------|------|
| [`queries.py`](../../queries.py) | Add `club_campaign(db, club_id, season_label)`, `edition_chronology(db, season_label)` and `winner_path_club_ids(db, edition_id)` exactly as specified in notes_004 (walkovers included; scorelines only from stored match rows; empty set when `winner_club_id` is NULL). |
| [`cli.py`](../../cli.py) | New subparsers `path` and `chronology`. Extend `LEADERBOARD_KINDS` to `("titles", "matches", "wins", "gd", "finals")` and print `wins` / `gd` with the existing matches layout (Fix D). |
| [`queries.py`](../../queries.py) `club_record()` | When `season_label` is set, collect `hat_trick_notes` per edition of that label (Fix E). |
| [`ui/data.py`](../../ui/data.py) | `fetch_edition_payload` / `fetch_club_profile` call the new helpers (and existing `club_record` / `head_to_head`) instead of a second SQL stack. |
| [`ui/club_dialog.py`](../../ui/club_dialog.py) | Render the campaign path for the loaded season on the club profile. |
| [`ui/tie_card.py`](../../ui/tie_card.py) / [`ui/bracket_view.py`](../../ui/bracket_view.py) / `App._render_fixtures` | Pass `highlight=True` into `render_tie_card` when both sides are in `winner_path_club_ids`. Use the existing victory-green token; do not add a new view. |
| [`build_database.py`](../../build_database.py) `verify()` | Reject `by == "away_goals"` unless that edition’s `away_goals_active` is true; add positive/negative tests. Edition-driven, no hard-coded year. |
| [`tests/test_stats.py`](../../tests/test_stats.py) / [`tests/test_ui_helpers.py`](../../tests/test_ui_helpers.py) | Temporary `build(..., db_path=)` coverage: Benfica 1961-62 path (Austria Wien → Nürnberg → Tottenham → Real Madrid); 1961-62 chronology length equals dated-match count; Real Madrid 1959-60 path includes Eintracht; season-scoped hat-trick notes; `leaderboard wins` / `gd`. |

JSON export should already be structurally complete from v1.6; v1.7 may add an optional `campaign` / `chronology` object but must not require it.

### Prioritisation rationale

v1.6 grows the archive; v1.7 makes a season *readable as a yearbook* without opening the group-stage branch. The three notes_004 helpers are independently deployable, share one query module, and were written to wait until the Linfield/name-history/notes write-path fixes were in. Wiring the v1.4 statistics helpers into the viewer is the last documented stats-analyst leftover and belongs with the club-profile campaign page rather than with v2.0 schema work. Holding this until after the three new editions exist also means the first chronology footer is measured against a broader dated set (1961-62 already 55/55, plus whatever v1.6 backfills).

### Verification and release gate criteria

- `python build_database.py --force` remains green; 1955-60 golden data unchanged.
- `python -m pytest -q` passes, including new campaign / chronology / winner-path / leaderboard-kind / season-scoped hat-trick tests on a temporary database.
- `python cli.py path benfica 1961-62` prints First Round Austria Wien, Quarter-Finals Nürnberg, Semi-Finals Tottenham, Final Real Madrid, with stored scorelines and settlements.
- `python cli.py chronology 1961-62` lists only ISO-dated rows, ordered oldest to newest, and prints a `dated/total` footer that matches `SELECT COUNT(*) FROM match WHERE match_date IS NOT NULL` for that season.
- `python cli.py leaderboard wins` and `python cli.py leaderboard gd` run and honour `LEADERBOARD_SORT`.
- `python cli.py goals benfica --season 1961-62` does not leak hat-trick notes from other seasons.
- Viewer: opening Benfica from the 1961-62 edition shows the campaign path; fixtures/bracket highlight only ties on the champion’s route; light and dark modes still render.
- `verify()` rejects a synthetic `by='away_goals'` edition with `away_goals_active=False`, and accepts a synthetic level-aggregate away-goals winner when the flag is true.

---

## Feature 3 — Group Stage Era: parser integration and the 1991-92 pilot

- **Title:** Integrate the modern-era parser prototype and promote the 1991-92 European Cup from a source fragment to a complete mixed knockout/group validation edition.
- **Target Release:** v2.0

### Codebase source and evidence

- [`ROADMAP.md`](../../ROADMAP.md) § “Completed work awaiting integration / Modern-era parser prototype”: remote `feat/modern-era-parser` at `ddd27c0` already contains additive phase, standings and competition-transfer schema prototypes; per-edition points and ordered standings-tiebreak configuration; deterministic group-table calculations and RSSSF group-stage parsing; a 1991-92 European Cup group-stage source fragment and regression tests; a Swiss/league-phase parser with a miniature validation fixture. **Not** in the v1.5 baseline. Remaining checkboxes: reconcile with v1.5 statistics and 1961-62 data; review and merge through v2.0 gates.
- [`ROADMAP.md`](../../ROADMAP.md) § “v2.0 — Group Stage Era”: integrate that prototype against the current v1.x baseline; promote miniature/source fragments to a complete, reproducible pilot; add CLI and JSON representations for group tables; use **1991-92 European Cup** as the first mixed knockout/group validation edition. Explicitly **not in scope:** the 36-team single-league phase or movement between competitions.
- [`schema.sql`](../../schema.sql) header: group stages and the Swiss league phase are “DELIBERATELY absent — they arrive in v2.0 and v3.0 as additive feature updates, never as a rewrite of this foundation.”
- [`agents/modern_era_parser.md`](../../agents/modern_era_parser.md) Task 2: model group phases as an additive `standings` (or equivalent) phase type linked to a `round`; capture the early-1990s switch from 2 points to 3 points for a win as a per-edition flag; honour points, goal difference and head-to-head as specified by the edition; prefer extending `tools/import_rsssf.py` or adding `tools/parse_group_stage.py`.
- [`notes/01_Active/notes_003.md`](notes_003.md) § “Group/Swiss Foundations”: ~1,900 lines on `feat/modern-era-parser`; proof of concept, not completed v2/v3 coverage; full 36-club ingestion and league-table UI remain unfinished. Recommended next-step 4: repair and rebase the parser onto updated main; rename its colliding `audits_008.md`; strip changelog control characters; assign a non-conflicting release label (the parser changelog currently reuses v1.3).
- [`notes/01_Active/notes_002.md`](notes_002.md) recommended next-step 9: keep “schema capability,” “representative sample,” “complete historical edition,” and “viewer support” as **distinct** milestones. This v2.0 feature is the first three; viewer support is v2.1.
- [`notes/01_Active/notes_000.md`](notes_000.md) Version 2.0: introduce the Group phase type and sorting algorithms with a flag for 2- vs 3-point wins.

### Technical specification

Additive schema only. Existing `tie` / `match` rows remain intact. Swiss/league-phase tables may be present as unused capability but must not be required to build Classic Era editions.

| Surface | Work |
|---------|------|
| [`schema.sql`](../../schema.sql) | Additive phase / group-membership / points-system / ordered-tiebreak / standings tables or nullable columns on `edition` and `round`, as already prototyped on `feat/modern-era-parser`. No breaking rewrite. Update the stale “Schema v1.0” / “club-name history is a later concern” comments in the same pass. |
| `tools/parse_group_stage.py` (or an extension of [`tools/import_rsssf.py`](../../tools/import_rsssf.py)) | RSSSF group-stage blocks → structured season fragments; 2- vs 3-point flag is per edition, never a hard-coded year. |
| [`build_database.py`](../../build_database.py) | Deterministic group-table verification (points, every configured tiebreak, incomplete groups, equal-record edge cases) alongside existing knockout `verify()`. |
| [`seasons.py`](../../seasons.py) / [`clubs.py`](../../clubs.py) | Complete **1991-92 European Cup** (groups **and** knockout) as the pilot edition; register new clubs with stable keys. The current fragment (group stage/final only) is not sufficient. |
| [`queries.py`](../../queries.py) / [`cli.py`](../../cli.py) | Shared standings helpers; `python cli.py season 1991-92` prints group tables; `python cli.py export 1991-92 --format json` includes standings. No UI-only SQL. |
| Docs / changelog hygiene | Rebase onto post-v1.7 main; unique audit-note number; parser changes labelled v2.0 (not another v1.3); no control characters in `CHANGELOG.md`. |

Do **not** in this release: render league tables in CustomTkinter (v2.1); ingest a 36-team league phase (v3.0); model mid-season movement between lineages (v3.0; explicitly out of ROADMAP v2.0).

### Prioritisation rationale

The parser branch is the largest unintegrated prototype in the repository and is already the named v2.0 goal. It must not merge during v1.6/v1.7 because it overlaps `CHANGELOG.md`, `DATA_GUIDE.md`, `build_database.py`, `queries.py`, `clubs.py`, `seasons.py`, the importer and the roadmap, and because Classic Era golden data must remain the reviewable floor. Completing 1991-92 (rather than leaving a group/final fragment) is the ROADMAP release gate that turns “schema capability” into a reproducible historical edition. Viewer work is deliberately split to v2.1 following notes_002/notes_003: a green CLI/JSON pilot is a smaller, auditable merge than a simultaneous standings UI.

### Verification and release gate criteria

- Rebuilding and querying all v1.x knockout editions produces the same verified results as before the migration (same champions, aggregates, match counts for 1955-60; v1.6/v1.7 editions unchanged).
- `python build_database.py --force` and `python -m pytest -q` pass, including new group-table tests for points, every configured tiebreak, incomplete groups and equal-record edge cases, plus Classic Era golden-data regressions.
- 1991-92 European Cup rebuilds from source end to end: groups, knockout, champion and runner-up match RSSSF; `python cli.py season 1991-92` and `python cli.py export 1991-92 --format json` expose standings without a headed UI.
- Parsers do not write `european_football.db` except via `build_database.py`.
- No force-push to `main`; work lands on a feature branch after rebase onto current main.

---

## Feature 4 — Group-table desktop viewer and group-era continuation

- **Title:** Render group tables alongside fixtures and bracket views, and continue group-era editions on the now-stable standings model.
- **Target Release:** v2.1

### Codebase source and evidence

ROADMAP currently bundles viewer standings inside v2.0. This note splits them to v2.1 because the project’s own audits insist on that separation, and because v2.0 is already a large schema-and-pilot merge:

- [`ROADMAP.md`](../../ROADMAP.md) v2.0 planned scope still includes “Render group tables alongside the existing fixture and bracket views” and the gate “The pilot edition can be inspected end to end in the database, CLI and viewer.” After v2.0 the CLI/database half of that gate is done; the viewer half becomes the v2.1 feature.
- [`notes/01_Active/notes_000.md`](notes_000.md): Group UI display logic is “Render standard league tables. Calculate points, goal difference, and head-to-head statistics.”
- [`notes/01_Active/notes_002.md`](notes_002.md) step 9: “Constructing the standings UI using shared ranking/query code rather than relying solely on UI-specific SQL”; keep viewer support as its own milestone.
- [`notes/01_Active/notes_003.md`](notes_003.md) remaining product gaps: “Addition of league-table rendering to the viewer”; recommended next-step 8: “Finalise the v2 user experience following the establishment of the parser foundation” — display group standings, reuse shared helpers, complete further group-era coverage, headed tests for navigation/resize/light-dark/period names.
- [`agents/ui_ux_developer.md`](../../agents/ui_ux_developer.md): view switcher is currently Fixtures List / Tournament Bracket only; no standings mode. Acceptance text still says “all 5 seeded seasons”, already stale — replace with “all loaded editions.”
- [`agents/modern_era_parser.md`](../../agents/modern_era_parser.md) Task 2 covers 1990s Champions League group stages in the plural; ROADMAP v2.0 uses 1991-92 as the *first* validation edition “before adding further Champions League seasons.” Those further seasons are the data half of v2.1.
- Dual group stages of the later 1990s are the original notes_000 “1999 dual-group-stage labyrinth” and must be data, not a second schema rewrite, once the 1991-92 single-group-phase model is in production.

### Technical specification

| Surface | Work |
|---------|------|
| [`ui/`](../../ui/) new `standings_view.py` (or equivalent) | Yearbook-styled group table: points, goal difference, head-to-head per the edition’s stored tiebreak order. Highlight qualification / elimination bands only when those bands are stored as data. |
| [`ui/header.py`](../../ui/header.py) | Extend the segmented view switcher: Fixtures List / Tournament Bracket / Group Tables. Knockout-only editions hide or disable the third mode rather than showing an empty grid. |
| [`ui/data.py`](../../ui/data.py) | Load standings from the v2.0 shared `queries.py` helpers; no UI-only SQL. |
| [`ui/theme.py`](../../ui/theme.py) | Reuse brass gold `#d4af37` for qualified sides and victory green `#2ea043` for group winners; do not introduce a parallel palette. |
| [`app.py`](../../app.py) | Wire the third view into the existing sidebar season load path. |
| [`seasons.py`](../../seasons.py) | After the viewer can render 1991-92, add the next group-era European Cup edition(s) one pull request at a time (same seeder discipline as v1.6). Dual group stages, when first encountered, are additional phase rows, not a new table family. |
| Tests | Display-free helpers for table ordering and qualification highlighting; headed smoke where a virtual display is available ([`notes_002.md`](notes_002.md) step 10). |

Windows packaging / PyInstaller, recorded as “Not Started” in [`notes_002.md`](notes_002.md), remains **after** schema, data and UI integration have stabilised ([`notes_003.md`](notes_003.md) step 9). It is a distribution concern, not this feature.

### Prioritisation rationale

A group-stage database that can only be inspected from the CLI fails the yearbook thesis. Splitting the viewer to v2.1 keeps the v2.0 merge reviewable (schema + 1991-92 + CLI) and gives the UI specialist a stable ranking API to consume. Further 1990s editions belong here rather than in v2.0 so that 1991-92 stays a single pilot, and rather than in v3.0 so that the Swiss-model work does not absorb unfinished group-era coverage. Cross-lineage transfers stay out: ROADMAP v2.0 forbids them, and notes_003 warns against conflating them with the 36-team league phase.

### Verification and release gate criteria

- 1991-92 European Cup group tables render in the desktop viewer beside fixtures and bracket; switching seasons that have no groups does not crash or show a blank pane.
- Table order matches the v2.0 CLI/JSON standings for every group of the pilot edition (and any additional group-era edition seeded in this release).
- `python build_database.py --force` and `python -m pytest -q` pass; Classic Era and 1991-92 regressions remain green.
- Manual or virtual-display smoke: resize, light/dark, period names, notes, attendance, and an irregular / bye-containing knockout round still behave.
- No UI-only SQL: deleting `queries.py` standings helpers would break the viewer tests.
- Further group-era editions, if included, each have champion / runner-up / representative group-table tests against RSSSF.

---

## Feature 5 — Modern 36-team league phase

- **Title:** Represent the current UEFA league phase as data: 36 clubs, eight opponents, ordered tiebreaks, qualification bands, downstream knockouts and documented movement between lineages.
- **Target Release:** v3.0

### Codebase source and evidence

- [`ROADMAP.md`](../../ROADMAP.md) § “v3.0 — Modern League Phase”: integrate the existing league-phase schema/parser prototype after v2.0 is stable; expand the miniature fixture into a complete 36-team league phase with eight scheduled opponents per club and matchday-aware fixtures; store and verify the full ordered UEFA league-phase tiebreak policy as edition data; model qualification bands and movement from the league table into the knockout play-off and round of 16; model documented movement between competition lineages where a season’s rules require it; apply the existing per-edition away-goals flag across historical knockout seasons, including its introduction and later abolition, with boundary regression tests; add scalable table, qualification-band and downstream-bracket views for a complete modern edition.
- [`agents/modern_era_parser.md`](../../agents/modern_era_parser.md) Task 3: 36 clubs, eight opponents each, single table, UEFA tie-breakers; standings are a derived view; allow mid-season movement between competitions (third-placed clubs dropping into the Europa League) as data links, not special-case code.
- [`notes/01_Active/notes_000.md`](notes_000.md) Version 3.0 originally framed “third-placed Champions League teams dropping into the UEFA Cup/Europa League mid-season”; the same note’s League (Swiss) display logic is “a single extensive 36-team table, sorting by points and UEFA tiebreakers.”
- [`notes/01_Active/notes_003.md`](notes_003.md): the parser brief currently conflates the 36-team league phase with the older third-place-to-Europa transfer mechanism — “distinct historical formatting issues and should be documented separately.” Both belong in v3.0 as two stored mechanisms on one release, not as one special-case. Full 36-club ingestion is unfinished; the parser branch has only a miniature Swiss sample.
- [`schema.sql`](../../schema.sql) `edition.away_goals_active` already exists; ROADMAP v3.0 is where the flag is applied across introduction (1965-66) and abolition (2021) with boundary tests. The *verifier* that refuses away-goals decisions when the flag is false is a v1.7 gate (Feature 2); v3.0 is the historical population of the flag and the 2021 abolition boundary.
- Competition-transfer modelling is listed among the unintegrated `feat/modern-era-parser` prototypes in ROADMAP “Completed work awaiting integration,” but ROADMAP v2.0 places movement between competitions out of scope until this release.

A scorer / goal-event table ([`audits_008.md`](../00_Audits/audits_008.md) remaining gap) is **not** this feature. Hat-trick boards must not invent names; that model can follow once `match.notes` round-trips (already a v1.6 write path) are in actual use.

### Technical specification

| Surface | Work |
|---------|------|
| [`schema.sql`](../../schema.sql) | Promote the Swiss/league-phase prototype: matchday on `match` or an additive fixture table; qualification-band rows as data; a competition-transfer / continuation link between editions of different lineages. Additive, nullable, Classic Era-safe. |
| Parser | Expand the miniature Swiss fixture into a complete 36-team edition (eight opponents per club). Input: RSSSF / UEFA league-phase match lists. Output: season fragments plus tests. |
| [`build_database.py`](../../build_database.py) | Verify the full ordered UEFA league-phase tiebreak policy as edition data; reproduce the published table and qualification positions; abort the build on mismatch without writing. |
| [`queries.py`](../../queries.py) / [`cli.py`](../../cli.py) | Derived 36-row table, qualification bands, and downstream knockout path; JSON export of a complete modern edition. |
| [`ui/`](../../ui/) | Scalable table, qualification-band shading and a downstream bracket for play-off → round of 16, reusing v2.1 standings chrome rather than a one-season special case. |
| Away-goals historical programme | Populate `away_goals_active` correctly from introduction through abolition; boundary regression tests (last season on, first season off). Application code continues to read the edition flag, never a hard-coded year. |
| Transfers | Store documented CL → UEFA Cup / Europa League (and later analogue) movement as data links between ties/editions, so a club’s campaign path (v1.7 helper) can cross lineages in a single season without special-case UI. |

### Prioritisation rationale

v3.0 is the named long-term milestone and must wait until the group-era model is stable (v2.0 schema + 1991-92, v2.1 viewer and further group seasons). The miniature Swiss parser is groundwork, not a shippable edition; promoting it before group tables exist in the viewer would repeat the v2.0 fragment problem at larger scale. Qualification bands, matchdays and cross-lineage transfers are exactly the “structure is data” principle in [`schema.sql`](../../schema.sql): they must not be special-cased for one season in `app.py`. The 2021 away-goals abolition belongs here with the modern ruleset; the 1965-66 introduction is already guarded by the v1.7 verifier so Classic Era seeding need not stall on this release.

### Verification and release gate criteria

- A complete 36-team edition rebuilds from source, reproduces its published table and qualification positions, and renders without manual corrections.
- Each club has eight scheduled league-phase opponents; matchdays are stored and queryable.
- Ordered UEFA tiebreaks are edition data: tests cover points, goal difference, head-to-head, and further configured breakers, including incomplete records.
- Qualification bands (play-off vs round of 16 vs elimination) match the published season; the downstream bracket is generated from those bands, not hand-wired.
- A documented cross-lineage transfer (third-placed / drop-down side) is queryable as a data link; `club_campaign` for that club in that season-label lists both competitions.
- Away-goals boundary tests: a 1965-66 (or first on-flag) edition accepts `decided_by='away_goals'`; a post-abolition edition rejects it; Classic Era 1955-60 remains `away_goals_active=0` with no such settlements.
- Classic knockout (v1.x) and v2.0/v2.1 group-stage regression suites remain green.
- `python build_database.py --force` and `python -m pytest -q` pass on the combined dataset.

---

## Work recorded but not scheduled as a title feature

These remain documented and should not be forgotten, but they are gates, tooling or later follow-ons rather than the five release titles:

| Item | Source | Disposition |
|------|--------|-------------|
| Extended `verify()` settlement types (Fix A) | notes_004 | v1.6 gate |
| JSON export cursor truncation; `match.notes` on export | notes_002 | v1.6 gate |
| Atomic `--force` replacement | notes_002 | v1.6 gate |
| Loud RSSSF importer omissions | notes_002 | v1.6 seeder tooling |
| Split `seasons.py` into competition/year modules once it grows past the current ~650-line, eight-edition file | notes_002 step 8 | Begin when v1.6 adds the Fairs Cup; keep the public `SEASONS` contract |
| Wins / GD leaderboard wiring; season-scoped hat-trick notes | notes_004 Fix D/E | v1.7 |
| Edition-driven away-goals *verifier* | database_engineer.md; notes_003 §7 | v1.7 gate (population/abolition remain v3.0) |
| Bye ties for documented 1961-62 byes | notes_004 Finding 7 | Model only from an RSSSF participant list, during v1.6+ seeding |
| Scorer / `goal` event table | audits_008 | After notes are actually stored and queried; do not invent scorers |
| Windows packaging, PyInstaller, release tags | notes_002 / notes_003 | After v2.1 UI integration, not a data release |
| GitHub/docs drift (stale schema comments, agent catalogue, issue form, hard-coded row counts) | notes_003 | Hygiene alongside whichever release next touches those files |
| Headed GUI smoke across every loaded edition | notes_002 step 10; notes_003 step 8 | v2.1 gate |

---

## Suggested application order

1. Land the remaining v1.6 pipeline gates (extended `verify()`, atomic rebuild, export `fetchall()`, importer silence), then seed EC 1962-63, CWC 1961-62 and Fairs Cup 1955-58 as separate pull requests.  
2. Ship v1.7 yearbook navigation (campaign, chronology, champion route, stats-in-viewer, away-goals verifier) against that wider Classic Era set.  
3. Only then rebase `feat/modern-era-parser` and complete 1991-92 as v2.0.  
4. Productise group tables in the desktop viewer and continue 1990s editions as v2.1.  
5. Expand the miniature Swiss fixture into a full 36-team league phase, with qualification bands and cross-lineage transfers, as v3.0.

Do not merge group-stage or Swiss-phase work into v1.6 or v1.7. Do not rewrite the 1955-60 dictionaries to chase a statistic or a new phase type.
