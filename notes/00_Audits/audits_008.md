# audits_008 - Stats analyst (head-to-head, goals, leaderboards)

Date: 2026-09-03 ~23:15 BST (Europe/London)
Agent: stats_analyst (executor on Hawkeye)
Machine: Hawkeye `db77ad96-8cd3-440f-8eaa-beaaa8c875bd`
Root: `C:\EuroDatabase`
Branch: `feat/stats-analyst` (fast-forwarded from `origin/feat/ui-ux-overhaul`; includes `agents/season_seeder.md`)

Statistical figures below are **derived** from verified `match` / `tie` / `edition` rows after `python build_database.py --force`. Totals are never stored as denormalised career tables. Joins use `club_id`; period names (`club_name_history`) are display-only.

## Method and invariants

- **Club identity.** Canonical `club.name` is for display and CLI lookup. Every aggregate joins on `club_id`.
- **Two-legged ties** count as two matches; play-offs, replays and single-leg finals each count as a match. Replay legs are not double-counted against the printed aggregate.
- **Walkovers / byes** are labelled (`decided_by` = `walkover` or `bye`) and are **not** silently scored 3-0 unless a `match` row actually records that scoreline. KuPS Kuopio v Eintracht Frankfurt, 1959-60 qualifying, is the Classic Era example: 0 matches, 0 goals, one labelled walkover.
- **Extra time.** Scores already stored on the match row (including after extra time) are used as-is.
- **Hat-tricks.** Notes are printed only when `match.notes` or `tie.notes` contain a hat-trick token. Scorers are never invented. The loaded database currently stores none.
- **British English** in CLI help, docstrings and leaderboard labels (*programme*, *labelled*; `colour` is rejected as an unknown leaderboard kind).
- **UTF-8** throughout. Historical country codes remain (ESP, FRG, GDR, TCH, YUG, SAA).
- **Golden fixtures.** `seasons.py` Classic Era rows were not rewritten to chase a statistic.

Helpers live in `queries.py` so the CustomTkinter viewer can consume the same numbers later. CLI commands: `python cli.py h2h`, `goals`, `leaderboard`.

## Leaderboard definitions

All-time boards rank the **loaded** database, not a hard-coded UEFA list. Kind names and sort order are `queries.LEADERBOARD_KINDS` / `queries.LEADERBOARD_SORT`. Rank is 1-based after the sort (ties broken by the remaining keys; there is no dense-rank collapse).

| Kind | Meaning | Sort (then canonical club name A-Z) |
|------|---------|-------------------------------------|
| `titles` | Trophies won from `edition.winner_club_id` | titles descending |
| `matches` | Played / W-D-L / goals from scored `match` rows | matches played desc, then wins desc, then goal difference desc |
| `finals` | Finals reached = champion + runner-up (`edition.winner_club_id` + `runner_up_club_id`) | finals reached desc, then titles desc |

Documented but not exposed on the CLI (available as functions): `wins` (wins desc, then matches, then GD) and `gd` (goal difference desc, then matches, then wins).

Walkover-only clubs (for example KuPS) do not appear on the matches board because they have no scored match rows; they still appear on titles/finals if they won or reached a final (they have not).

## Statistical findings (loaded database)

Build report: `lineage=2`, `club=91`, `club_name_history=9`, `edition=7`, `round=33`, `tie=148`, `match=297`. All aggregates verified against RSSSF printed totals. Scope is European Cup 1955-56 through 1960-61 plus the inaugural European Cup Winners' Cup 1960-61.

### Classic Era 1955-60 (European Cup)

Real Madrid won **five titles in five seasons**. Eintracht Frankfurt were **1959-60 runners-up**.

| Season | Champion | Runner-up |
|--------|----------|-----------|
| 1955-56 | Real Madrid | Stade de Reims |
| 1956-57 | Real Madrid | Fiorentina |
| 1957-58 | Real Madrid | Milan |
| 1958-59 | Real Madrid | Stade de Reims |
| 1959-60 | Real Madrid | Eintracht Frankfurt |

1960-61 (outside the five-in-a-row, still in the loaded file): European Cup — SL Benfica beat FC Barcelona; Cup Winners' Cup — Fiorentina beat Rangers.

### Title leaderboard

1. Real Madrid (ESP) — 5
2. Fiorentina (ITA) — 1 (CWC 1960-61)
3. SL Benfica (POR) — 1 (European Cup 1960-61)

### Finals reached (champion + runner-up)

1. Real Madrid — 5 finals, 5 titles, 0 runner-up
2. Fiorentina — 2 (1 title, 1 runner-up: lost 1956-57 EC, won 1960-61 CWC)
3. Stade de Reims — 2 (0 titles, 2 runner-up: 1955-56 and 1958-59)
then Benfica 1/1/0; Eintracht Frankfurt, FC Barcelona, Milan, Rangers each 1 final, 0 titles.

### Matches / goal difference (top of board)

Real Madrid: played 39, won 27, goals 115-46, GD +69, average 2.95 scored per match, finals goals 18-8 in 5 matches. Rangers 24 played; Reims 20 / +30; Milan 20 / +14. Across the whole file, the sum of `matches_played` equals twice the scored match rows, and the sum of goal difference is 0 (each goal is for one club and against the other).

### Head-to-head (symmetry holds)

`head_to_head(A, B)` is the complement of `head_to_head(B, A)` (wins, goals, walkover count and match count swap sides; draws unchanged). Checked for Real Madrid v Reims, Real Madrid v Barcelona, Real Madrid v Eintracht, Benfica v Barcelona, and the walkover pair Eintracht v KuPS.

- **Real Madrid v Stade de Reims:** 2 matches (both European Cup finals), 2-0-0, goals 6-3 (4-3 Parc des Princes 13 June 1956; 2-0 Neckarstadion 3 June 1959).
- **Real Madrid v FC Barcelona:** 4 matches / 2 ties; 2 wins, 1 draw, 1 loss; goals 9-6. 1959-60 semi-final aggregate 6-2; 1960-61 first round 3-4 on aggregate (two legs, not a silent walkover).
- **Real Madrid v Eintracht Frankfurt:** 1 match, 7-3 (Hampden Park final, 18 May 1960). Counted once.
- **Eintracht Frankfurt v KuPS Kuopio:** 0 matches, 1 walkover (1959-60 qualifying), awarded to Eintracht. Not 3-0.

### Highest-scoring ties involving Real Madrid

1. 1959-60 First Round v Jeunesse Esch — 14 goals (2 legs)
2. 1956-57 First Round v SK Rapid Wien — 12 goals (3 legs, including play-off)
3. 1957-58 Quarter-Finals v Sevilla CF — 12 goals (2 legs)
4. 1959-60 Final v Eintracht Frankfurt — 10 goals (1 leg)
5. 1955-56 Semi-Finals v Milan — 9 goals (2 legs)

### 1959-60 programme goals

218 goals in scored matches: Qualifying 74/20, First Round 74/18, Quarter-Finals 36/9, Semi-Finals 24/4, Final 10/1. Hat-trick notes stored: none (tests inject a note to prove the filter, then roll it back).

## CLI (smoke, rebuilt database)

```
python cli.py h2h real_madrid reims
python cli.py leaderboard titles
python cli.py goals real_madrid
python cli.py goals --season 1959-60
python cli.py leaderboard matches
python cli.py leaderboard finals --limit 10
```

`h2h` prints matches, W-D-L from each side, goals, ties contested, lineage breakdown, labelled walkovers, then each leg. `goals` accepts a club and/or `--season`. `leaderboard` prints the documented sort line.

## Tests

`tests/test_stats.py` rebuilds a **fresh temporary** SQLite file via `build(force=True, db_path=...)` so results never depend on a stale `european_football.db`. Coverage: H2H symmetry, Real Madrid/Reims finals, Barcelona aggregate, labelled walkover, Classic Era champions, Eintracht 1959-60 runners-up, Hampden counted once, leaderboard totals versus direct SQL, hat-trick notes only when stored, 1960-61 two lineages, replay legs not double-counted.

Verification on Hawkeye:

- `python build_database.py --force` — pass (RSSSF aggregates verified).
- `python -m pytest tests -q` — **104 passed** in 2.30s (includes new stats tests).
- CLI smokes above — pass.
- `agents/season_seeder.md` and `AGENTS.md` were not modified.

## Files

- `queries.py` — shared H2H, goal and leaderboard helpers.
- `cli.py` — `h2h`, `goals`, `leaderboard` (plus existing `club` / `season` / `export`).
- `build_database.py` — `build(force, db_path=...)` for temporary test databases.
- `tests/test_stats.py` — stats suite on a temp DB.
- `CHANGELOG.md` — v1.4; `DATA_GUIDE.md` — section 7.

## Remaining gaps

- No scorer table, so hat-trick / top-scorer boards cannot be derived until notes or a future `goal` table exist. Do not invent names.
- The viewer does not yet call the new helpers (club profile still uses its own batched SQL).
- Leaderboards are all-time over the loaded file only; they will grow as later seasons are seeded, which is intended.
