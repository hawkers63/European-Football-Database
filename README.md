# European Football Database — Classic Era

A standalone desktop database of UEFA club competitions, built the way the old
*Yearbook of European Football* felt: one clean reference you can page through.
The current data covers the **unseeded two-legged knockout era**, seeded with the
complete European Cup **1955-56 → 1959-60** — Real Madrid's five-in-a-row.

Stack: Python + CustomTkinter (UI) · SQLite (data, bundleable into a `.exe`).

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | The database schema (DDL). Single source of truth for structure. |
| `clubs.py` | Canonical club registry — one keyed entry per real club. |
| `seasons.py` | Season fixtures, each tie tagged with RSSSF's printed aggregate. |
| `build_database.py` | Builds `european_football.db`; **verifies** every aggregate before committing. |
| `app.py` | The CustomTkinter viewer. |
| `european_football.db` | Generated database (76 clubs, 112 ties, 228 matches). |
| `ROADMAP.md`, `DATA_GUIDE.md`, `CHANGELOG.md` | Plan, how to add a season, history. |

## Running it

```bash
pip install customtkinter        # one-off
python build_database.py --force # build (or rebuild) the .db
python app.py                    # launch the viewer
```

Pick a competition and season in the sidebar; each round renders as
paired-fixture cards with the two-legged aggregate auto-calculated and the winner
in green. Play-offs, coin tosses and walkovers are shown for what they are.

## What makes the data trustworthy

`build_database.py` recomputes every tie's aggregate from its individual legs and
checks it against RSSSF's own printed total. If a single leg is mistyped, the
build prints the offending tie and **writes nothing**. The current dataset builds
clean: all 112 ties verified, zero foreign-key violations, zero duplicate clubs.

## Design decisions worth knowing

- **Structure is data, not code.** A round can hold one-leg ties, two-leg ties,
  play-offs, coin tosses, walkovers or byes with no schema change.
- **One trophy line, many names.** `lineage` is the continuous identity; each
  `edition` stores the period-correct name for that season.
- **One club, one row.** The registry is keyed by short IDs, so a club is defined
  once no matter how many seasons it plays. Clubs renamed mid-era carry the period
  name in their notes (see ROADMAP.md for the planned period-accurate display).
- **Ties own their legs.** Aggregates are computed, never stored, so they can't
  drift. `decided_by` records how each tie was settled.

## Adding seasons

See `DATA_GUIDE.md`. In short: reuse or add club keys in `clubs.py`, append a
season dict to `seasons.py`, run `python build_database.py --force`.

*Historical results transcribed from RSSSF (Rec.Sport.Soccer Statistics
Foundation), James M. Ross's European competition pages. Free to reproduce with
acknowledgement.*
