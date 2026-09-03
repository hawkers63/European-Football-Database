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
