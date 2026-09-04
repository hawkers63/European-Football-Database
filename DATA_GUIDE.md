# Adding a season

Adding a season is dropping one dict into `seasons.py` (and any brand-new clubs
into `clubs.py`). The build verifies your entries against RSSSF's own aggregates,
so a slip fails the build instead of shipping a wrong scoreline.

European Cup is seeded through **1961-62** (Benfica retained the trophy against
Real Madrid). Cup Winners' Cup remains at the inaugural **1960-61**.
This is the **v1.5 baseline**. The v1.6 queue is European Cup **1962-63**, Cup
Winners' Cup **1961-62**, and Inter-Cities Fairs Cup **1955-58**.

## 1. New clubs → `clubs.py`

For any club not already in the registry, add a keyed entry:

```python
"club_key": {"name": "Display Name", "country": "ESP", "city": "City",
             "notes": "optional — e.g. period alias or later name"},
```

Reuse the existing key for a club that already appears (Real Madrid is
`real_madrid` in every season). One real club = one key = one row.

## 2. New season → `seasons.py`

Append a season dict. The two rules that keep it honest:

- **`t1` is the first-named side / first-leg host** (as printed by RSSSF).
- **`agg` is RSSSF's printed aggregate for legs 1 & 2**, in `(t1, t2)` order.
  For a play-off tie this is the level score; the play-off is a third leg.

```python
{
  "lineage": "European Cup", "season_label": "1960-61", "start_year": 1960,
  "competition_name": "European Cup",
  "winner": "benfica", "runner_up": "barcelona", "away_goals_active": False,
  "notes": "…",
  "rounds": [
    {"name": "First Round", "ties": [
      {"t1": "real_madrid", "t2": "barcelona", "win": "barcelona",
       "by": "aggregate", "agg": (2, 2),
       "legs": [L("real_madrid", "barcelona", 2, 2),
                L("barcelona", "real_madrid", 2, 1)]},
    ]},
    # … Quarter-Finals, Semi-Finals, Final …
  ],
}
```

### The `by` field (how a tie was settled)

| value          | meaning                                   | legs                          |
|----------------|-------------------------------------------|-------------------------------|
| `aggregate`    | two legs, higher aggregate wins           | 2                             |
| `away_goals`   | level on aggregate, more away goals wins  | 2                             |
| `penalties`    | settled on a shootout (`home_pens`/…)     | 2 (+ pens on deciding leg)    |
| `replay`       | level, settled by a play-off              | 3 (3rd = play-off)            |
| `coin_toss`    | level after play-off, decided on the toss | 3                             |
| `single_match` | one match (e.g. the Final)                | 1                             |
| `walkover`/`bye` | advanced without playing                | 0 (set `agg` to `None`)       |

### Leg extras

`L(home, away, hs, as, venue="…", date="YYYY-MM-DD", att=12345, ref="…", aet=True)`
— all optional. Relocated legs and neutral finals go in `venue`.

## 3. Build and verify

```bash
python build_database.py --force
```

A clean run prints the row counts and *"All aggregates verified against RSSSF
printed totals."* If a leg is mistyped you'll get a line like:

```
!! AGG  1960-61 First Round: real_madrid v barcelona: legs give 4-2, RSSSF says 2-2
```

Fix the leg and rebuild. Nothing is written while a problem remains.


## 4. Period club names  → `CLUB_NAME_HISTORY` in `clubs.py`

Canonical modern names stay on `CLUBS`. When a club competed under a different
name in a given season, add a structured history entry (do **not** rely on
free-text notes alone):

```python
{
  "club": "mtk",
  "season_label": "1955-56",
  "name_used": "Vörös Lobogó",
  "notes": "Official name during the inaugural European Cup.",
},
```

`build_database.py` writes these into `club_name_history`. Query with
`queries.get_club_display_name(conn, club_id, edition_id)`.

## 5. Lineages  → `lineages.py`

New trophy threads need a `LINEAGES` note before you seed their first season:

```python
"European Cup Winners' Cup": "UEFA Cup Winners' Cup (1960-61 to 1998-99).",
```

## 6. CLI & RSSSF import

```bash
python cli.py club benfica
python cli.py h2h benfica barcelona
python cli.py season 1960-61
python cli.py export 1960-61 --format json

python tools/import_rsssf.py pasted_lines.txt --season 1961-62 --lineage "European Cup"
```

The importer fuzzy-matches club names, emits `L()` blocks, and refuses to print
a season skeleton if leg totals disagree with the RSSSF aggregate.


## 7. Head-to-head, goals and leaderboards

Figures are derived from verified `match` / `tie` / `edition` rows in
`european_football.db`. Rebuild before publishing numbers:

```bash
python build_database.py --force
```

```bash
python cli.py h2h benfica barcelona
python cli.py h2h real_madrid reims
python cli.py goals real_madrid
python cli.py goals --season 1959-60
python cli.py leaderboard titles
python cli.py leaderboard matches
python cli.py leaderboard finals --limit 10
```

- **Head-to-head** uses `club_id` joins. Period names (e.g. *Vörös Lobogó*)
  appear on individual matches via `get_club_display_name`; the summary uses
  canonical `club.name`. Walkovers are labelled and are not scored 3-0 unless
  a match row holds that scoreline. Two-legged ties count as two matches;
  play-offs, replays and single-leg finals each count as a match.
- **Goals** respect extra-time scores already stored on the match row and do
  not double-count replay legs. Hat-trick notes are printed only when present
  in `match.notes` or `tie.notes`.
- **Leaderboards** rank the loaded database (not a hard-coded UEFA list).
  Sort order is printed by the command and defined in
  `queries.LEADERBOARD_SORT` / `notes/00_Audits/audits_008.md`:
  - `titles` - titles won (desc), canonical name (A-Z)
  - `matches` - matches played, then wins, then goal difference, then name
  - `finals` - finals reached (champion + runner-up), then titles, then name

Helpers live in `queries.py` so the CustomTkinter viewer can consume the same
numbers later. Golden Classic Era fixtures in `seasons.py` are not rewritten
to chase a statistic; if a figure disagrees with RSSSF, fix the query.
