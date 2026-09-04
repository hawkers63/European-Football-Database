# European Football Database — Classic Era

A standalone desktop database of UEFA club competitions, built the way the old
*Yearbook of European Football* felt: one clean reference you can page through.
The current data covers the **unseeded two-legged knockout era**, with the
European Cup seeded from **1955-56 through 1961-62** and the inaugural European
Cup Winners' Cup **1960-61**.

Stack: Python + CustomTkinter (UI) · SQLite (data, bundleable into a `.exe`).

**Current baseline:** v1.5 · **Next development release:** v1.6, Classic
competitions expansion. See [`ROADMAP.md`](ROADMAP.md) for release scope and
acceptance gates.

Group-stage and league-phase prototypes exist on `feat/modern-era-parser`, but
they remain outside the baseline until the v2.0 integration gates are met.

## Current coverage

- 2 seeded trophy lineages and 8 complete editions
- 99 canonical clubs across 29 historical association codes
- 38 rounds, 176 ties and 351 matches
- Full match dates for the European Cup 1961-62; selected dates, venues,
  attendances and referees for earlier editions
- 112 passing automated tests at the v1.5 baseline

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | The database schema (DDL). Single source of truth for structure. |
| `clubs.py` | Canonical club registry — one keyed entry per real club. |
| `seasons.py` | Season fixtures, each tie tagged with RSSSF's printed aggregate. |
| `build_database.py` | Builds `european_football.db`; **verifies** every aggregate before committing. |
| `app.py` | The CustomTkinter viewer (fixtures list, tournament bracket, club profiles). |
| `ui/` | Modular widgets, yearbook palette, and batched data loaders. |
| `queries.py`, `cli.py` | Shared statistics plus club, head-to-head, goals, leaderboard, season and JSON commands. |
| `tools/import_rsssf.py` | Drafts season data from pasted RSSSF result lines and checks aggregates. |
| `european_football.db` | Generated database (99 clubs, 8 editions, 176 ties, 351 matches). |
| `ROADMAP.md`, `DATA_GUIDE.md`, `CHANGELOG.md` | Plan, how to add a season, history. |

## Running it

```bash
python -m pip install -r requirements.txt
python -m pip install customtkinter  # required only for the desktop viewer
python build_database.py --force # build (or rebuild) the .db
python app.py                    # launch the viewer
```

Pick a competition and season in the sidebar. Each round renders as paired
fixture cards or a tournament bracket, with the aggregate calculated from the
stored legs and the winner shown in green. Search filters the loaded edition;
club names open profile records, and play-offs, coin tosses and walkovers remain
explicit.

The same data is available from the command line:

```bash
python cli.py club benfica
python cli.py h2h benfica real_madrid
python cli.py goals --season 1961-62
python cli.py leaderboard titles
python cli.py export 1961-62 --format json
```

## What makes the data trustworthy

`build_database.py` recomputes every tie's aggregate from its individual legs and
checks it against RSSSF's own printed total. If a single leg is mistyped, the
build prints the offending tie and **writes nothing**. The current dataset builds
clean: all 176 ties pass validation, with zero foreign-key violations and zero
duplicate or unused canonical clubs. The full regression suite also checks
settlement types, period names, importer behaviour, statistics and UI helpers.

## Design decisions worth knowing

- **Structure is data, not code.** A round can hold one-leg ties, two-leg ties,
  play-offs, coin tosses, walkovers or byes with no schema change.
- **One trophy line, many names.** `lineage` is the continuous identity; each
  `edition` stores the period-correct name for that season.
- **One club, one row.** The registry is keyed by short IDs, so a club is defined
  once no matter how many seasons it plays. `club_name_history` supplies the name
  used in a particular edition without changing the canonical identity.
- **Ties own their legs.** Aggregates are computed, never stored, so they can't
  drift. `decided_by` records how each tie was settled.
- **Statistics are derived.** Head-to-head records, goal totals and leaderboards
  are calculated from verified match and edition rows, not maintained as separate
  career totals.

## Adding seasons

See `DATA_GUIDE.md`. In short: reuse or add club keys in `clubs.py`, append a
season dictionary to `seasons.py`, then run both release gates:

```bash
python build_database.py --force
python -m pytest -q
```

*Historical results transcribed from RSSSF (Rec.Sport.Soccer Statistics
Foundation), James M. Ross's European competition pages. Free to reproduce with
acknowledgement.*
