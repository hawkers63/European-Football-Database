# Adding a season

Adding a season is dropping one dict into `seasons.py` (and any brand-new clubs
into `clubs.py`). The build verifies your entries against RSSSF's own aggregates,
so a slip fails the build instead of shipping a wrong scoreline.

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


## 7. Group stages and Swiss league phases

Group and Swiss (league-phase) fixtures are **additive**. Knockout `tie` /
`match` rows stay as they are. Rankings are **always derived** from fixtures via
`tools/standings.py` — never stored as a ranking table.

### Edition flags (data, not calendar years)

| field | meaning |
|-------|---------|
| `points_for_win` | `2` or `3`. NULL on knockout-only editions. **Never** infer from the season label. |
| `standings_tiebreak` | Comma-separated criteria (e.g. `points,goal_difference,goals_scored,head_to_head`). |

### Round shape

```python
{"name": "Group Stage", "phase_type": "group", "ties": [], "groups": [
  {"name": "Group A", "clubs": ["sampdoria", "red_star", "..."],
   "matches": [
     {"home": "sampdoria", "away": "red_star", "hs": 2, "as": 0},
   ],
   "table": [  # optional printed RSSSF table for build-time verify
     {"club": "sampdoria", "played": 6, "w": 3, "d": 2, "l": 1,
      "gf": 10, "ga": 5, "pts": 8},
   ]},
]},
```

Use `"phase_type": "league"` for a Swiss / single-table league phase (one
`standing_group`, often named `"League phase"`).

### Mid-season movement

Cross-competition drops (e.g. group third → UEFA Cup / Europa League) are rows
in `competition_transfer`, seeded from a season's optional `transfers` list:

```python
"transfers": [
  {"club": "benfica", "from_rank": 3, "from_round": "Group Stage",
   "to_lineage": "UEFA Cup", "to_season_label": "1991-92",
   "to_round": "First Round", "reason": "group_third"},
],
```

The destination edition must already be seeded or the build skips with a warning.

### Parser tools (do not write the database)

```bash
python tools/parse_group_stage.py tools/fixtures/cl_1991_92_groups.rsssf \
    --season 1991-92 --points-for-win 2 --dry-run

python tools/parse_swiss_phase.py tools/fixtures/swiss_miniature.rsssf \
    --season 2024-25 --points-for-win 3 --dry-run
```

Paste the printed fragment into `seasons.py`, register any new club keys, then:

```bash
python build_database.py --force
```

Representative fixture: `tools/fixtures/cl_1991_92_groups.rsssf` (1991-92 first
Champions League groups, 2 points for a win). Miniature Swiss sample:
`tools/fixtures/swiss_miniature.rsssf`.

