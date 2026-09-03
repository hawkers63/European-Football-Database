# European Football Database — v1.0 (The Classic Era)

A standalone desktop database of UEFA club competitions, built the way the old
*Yearbook of European Football* felt: one clean reference you can page through.
Version 1.0 covers the **unseeded two-legged knockout era** and ships with the
complete, verified **1955–56 European Cup** as a validation dataset.

Stack: Python + CustomTkinter (UI) · SQLite (data, bundleable into a `.exe`).

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | The v1.0 database schema (DDL). The single source of truth for structure. |
| `build_database.py` | Creates `european_football.db` from the schema and seeds 1955–56. |
| `app.py` | The CustomTkinter viewer — browse a season round-by-round. |
| `european_football.db` | Pre-built database (16 clubs, 15 ties, 29 matches). |

## Running it

```bash
pip install customtkinter        # one-off
python build_database.py --force # (optional) rebuild the .db from scratch
python app.py                    # launch the viewer
```

Pick a competition and season in the sidebar; each round renders as
paired-fixture cards with the aggregate auto-calculated and the winner in green.

## Design decisions worth knowing

- **Structure is data, not code.** A round can hold one-leg ties, two-leg ties,
  replays, byes or shootouts with no schema change. This is what lets the same
  tables carry a 1979 straight knockout and, later, a 1999 group labyrinth.
- **One trophy line, many names.** `lineage` is the continuous identity
  (European Cup → Champions League); each `edition` stores the period-correct
  name for that season. No separate aliases table needed.
- **Ties own their legs.** Aggregates are computed from `match` rows, never
  stored, so they can't drift out of sync. `tie.decided_by` records *how* a tie
  was settled (`aggregate`, `away_goals`, `replay`, `penalties`, `coin_toss`,
  `single_match`, `walkover`, `bye`) so the UI never has to guess.
- **Edge cases already have a home:** penalty shootouts (`home_pens`/`away_pens`
  keep the 90'/aet scoreline truthful), replays (`leg_number` 3), relocated legs
  and neutral-venue finals (`venue`), and per-season away-goals via a flag.

Every one of the 14 two-legged ties in the seed was cross-checked: the computed
aggregate matches the recorded winner in all cases, with zero foreign-key
violations.

## Roadmap

- **v1.0 — Classic Era (this):** knockout formats 1955–1991. Add more European
  Cup / Fairs–UEFA Cup / Cup Winners' Cup seasons from RSSSF.
- **v2.0 — Group Stage Era:** introduce a `standings` phase type; 2-vs-3-points
  flag; group sorting and head-to-head.
- **v3.0 — Modern Era:** Swiss league phase; mid-season drops between competitions.

*Historical results sourced from RSSSF (Rec.Sport.Soccer Statistics Foundation).*
# European-Football-Database
