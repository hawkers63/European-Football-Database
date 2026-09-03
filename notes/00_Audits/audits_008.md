# audits_008 - Stats analyst (head-to-head, goals, leaderboards)

Date: 2026-09-03 ~23:15 BST (Europe/London)
Agent: stats_analyst (executor on Hawkeye)
Machine: Hawkeye `db77ad96-8cd3-440f-8eaa-beaaa8c875bd`
Root: `C:\EuroDatabase`
Branch: `feat/stats-analyst` off `feat/ui-ux-overhaul` @ `2417fea`

## Mission

Produce trustworthy head-to-head records, goal statistics and all-time club
leaderboards from `european_football.db`. Every figure is a SELECT over
verified `match` / `tie` / `edition` rows. Period names are display-only;
joins use `club_id`. `seasons.py` Classic Era fixtures were not rewritten.

## Helpers (`queries.py`)

- `head_to_head(db, a, b)` - matches, W-D-L each side, goals, ties contested, lineage breakdown, labelled walkovers
- `h2h_is_complement(left, right)` - A vs B is the side-swapped complement of B vs A
- `club_record(db, club_id, season_label=None)` - played / W-D-L / GF-GA / GD / average / finals goals / highest-scoring ties / titles
- `edition_goal_stats` / `season_goal_stats` - total goals per edition and per round; hat-trick notes only if stored
- `leaderboard_titles` / `leaderboard_matches` / `leaderboard_finals` - all-time rankings over the loaded database
- `classic_era_title_holders` - European Cup champions 1955-56 to 1959-60
- `build(..., db_path=)` - tests rebuild a fresh temporary database

Match rows with a NULL scoreline are skipped. Extra-time scores already stored
on the row are used as-is. Each match is counted once (two-legged ties = two
matches; play-offs / replays / single-leg finals each count). Walkovers have
no match rows and are never silently scored 3-0.

Hat-trick notes are listed only when `match.notes` or `tie.notes` contain
"hat-trick". The seeded Classic Era data currently stores none; scorers are
not invented.

## Leaderboard definitions

Derived from the loaded database, not a hard-coded UEFA list. Documented sort
order (`queries.LEADERBOARD_SORT`):

- `titles` - `edition.winner_club_id` counts; sort titles DESC, canonical name ASC
- `matches` - scored match rows (each side); sort played DESC, wins DESC, GD DESC, name ASC
- `finals` - champion + runner-up on `edition`; sort finals reached DESC, titles DESC, name ASC

`wins` and `gd` helpers exist for the viewer; the CLI surfaces the three kinds
required by the brief.

Invariants checked against direct SQL:

- sum of titles = COUNT of editions with a winner
- sum of matches played across clubs = 2 x scored match rows
- sum of goals for = sum of goals against = sum of (home+away) scores
- sum of goal difference = 0
- sum of finals reached = winners + runners-up

## Classic Era findings (loaded database, 1955-61)

European Cup champions 1955-60 (five titles in five seasons):

- 1955-56 Real Madrid (runner-up Stade de Reims)
- 1956-57 Real Madrid (runner-up Fiorentina)
- 1957-58 Real Madrid (runner-up Milan)
- 1958-59 Real Madrid (runner-up Stade de Reims)
- 1959-60 Real Madrid (runner-up Eintracht Frankfurt)

1960-61 adds SL Benfica (European Cup) and Fiorentina (Cup Winners' Cup).
All-time titles on the loaded database: Real Madrid 5, SL Benfica 1,
Fiorentina 1.

Documented aggregates used in tests:

- Real Madrid vs Stade de Reims: two finals, 4-3 (1956) and 2-0 (1959); 6-3 goals.
- Real Madrid vs FC Barcelona: 1959-60 SF 6-2 aggregate (two legs) plus 1960-61 first round 3-4; 4 matches, 9-6.
- Real Madrid vs Eintracht Frankfurt: 1959-60 Final 7-3 at Hampden (10 goals; counted once).
- Eintracht Frankfurt vs KuPS Kuopio: 1959-60 walkover; 0 matches, 0-0, labelled walkover (not 3-0).

## CLI

    python cli.py h2h real_madrid reims
    python cli.py goals real_madrid
    python cli.py goals --season 1959-60
    python cli.py leaderboard titles
    python cli.py leaderboard matches
    python cli.py leaderboard finals

British English in help text, docstrings and labels. Historical country codes
(FRG, GDR, TCH, YUG, SAA) are untouched.

## Tests

`tests/test_stats.py` rebuilds via `build(force=True, db_path=tempfile)`.
Covers H2H symmetry, Classic Era 1955-60 champions, the documented aggregates
above, walkover labelling, leaderboard totals vs SQL, and hat-trick notes only
when stored.

## Constraints held

1. Derived, not duplicated - no career-total tables.
2. Join on club_id; period names display-only.
3. seasons.py Classic Era rows not rewritten.
4. British English in new CLI copy.
5. UTF-8; FRG/GDR/TCH/YUG/SAA retained.


## Verification on Hawkeye (2026-09-03 ~23:20 BST)

- `python -m pytest tests -q`: **104 passed** in 4.17s (includes `tests/test_stats.py`).
- `python build_database.py --force`: zero errors.
  Row counts: lineage=2, club=91, club_name_history=9, edition=7, round=33,
  tie=148, match=297. All aggregates verified against RSSSF printed totals.
- CLI against the rebuilt DB (no errors):
  - `h2h benfica barcelona`: 1 match, Benfica 1-0 Barcelona, goals 3-2
    (1961-05-31 European Cup Final, Wankdorf). Reverse pair is the complement
    (Barcelona 0-1 Benfica, goals 2-3).
  - `h2h real_madrid reims`: 2 matches, Real Madrid 2-0, goals 6-3.
  - `h2h real_madrid barcelona`: 4 matches, 2-1-1, goals 9-6 (1959-60 SF 6-2
    plus 1960-61 first round 3-4).
  - `h2h eintracht kups`: 0 matches, 1 walkover, not scored 3-0.
  - `leaderboard titles`: Real Madrid 5, Fiorentina 1, SL Benfica 1.
  - `leaderboard finals`: Real Madrid 5 finals / 5 titles; Eintracht Frankfurt
    (FRG) 1 final / 0 titles / 1 runner-up (1959-60).
  - `goals --season 1959-60`: 218 goals; Final 10 (7-3 Hampden); no hat-trick
    notes stored.
  - `goals real_madrid`: 39 matches, 115-46, GD +69, finals goals 18-8.
- Classic Era 1955-60 title counts match the seeded golden data (Real Madrid
  five-in-a-row). Historical country codes (FRG, YUG, ...) unchanged.

Committed locally on `feat/stats-analyst`. Not pushed.
