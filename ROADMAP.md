# Roadmap

The database treats the **structure of a tournament as data, not code**. That is
what lets one schema carry a 1950s straight knockout, a 1990s double group stage
and today's Swiss league phase. The plan grows the data and the display logic in
that order, never rewriting the foundation.

## v1.x — The Classic Era (in progress)

Unseeded / seeded two-legged knockouts, from 1955 to the mid-1990s rebrands.

- [x] Schema for knockouts (ties own their legs; play-offs, coin tosses,
      walkovers, byes, single-leg finals all representable).
- [x] Canonical club registry keyed by short IDs (no duplicate clubs).
- [x] Build-time verification: every tie's legs must reproduce RSSSF's printed
      aggregate or the build fails.
- [x] CustomTkinter viewer: season browser, round-by-round paired fixtures,
      auto-aggregate, winner highlighting.
- [x] European Cup **1955-56 → 1959-60** seeded (the Real Madrid five-in-a-row).
- [x] European Cup **1960-61** seeded (Benfica's first title).
- [x] European Cup **1961-62** seeded (Benfica retained the trophy).
- [ ] Continue the European Cup season by season (1962-63 onward).
- [x] European Cup Winners' Cup inaugural **1960-61** seeded (Fiorentina).
- [ ] Continue Cup Winners' Cup and add Inter-Cities Fairs Cup → UEFA Cup.
- [x] Optional viewer polish: a proper bracket view for pure knockout rounds.

## v2.0 — The Group Stage Era

Once the knockout data is broad and solid, add group phases as an **additive**
feature — no change to existing tables.

- [ ] A `standings` phase type linked to a round.
- [ ] A per-competition flag for **2 points vs 3 points for a win** (the switch
      happened in the early 1990s; store it, don't hardcode a year).
- [ ] Group-table sorting: points, goal difference, head-to-head.
- [ ] Viewer: render league tables alongside the existing bracket/fixture views.

## v3.0 — The Modern Era

- [ ] The Swiss single-league phase (36 teams, eight opponents), sortable by the
      current UEFA tiebreakers.
- [ ] Mid-season movement between competitions (e.g. third-placed Champions
      League clubs dropping into the Europa League).
- [ ] Away-goals handling driven entirely by the per-season flag already in the
      schema (rule introduced 1965-66, abolished 2021).

## Known modelling notes (candidates for a future minor version)

- [x] **Period-accurate club names** via `club_name_history` / `CLUB_NAME_HISTORY`.
  Remaining polish: surface them throughout the CustomTkinter viewer.
- Legacy note: the club registry keeps one canonical row per
  real club, so a club that was renamed mid-era (MTK Budapest ↔ *Vörös Lobogó*;
  Slovan Bratislava ↔ *ČH Bratislava*) currently displays under one name across
  all seasons, with the period name recorded in its notes. A small
  `club_name_history` table — mirroring how competition lineage already preserves
  period-correct competition names — would let each season show the club's name
  of the day. Deferred deliberately; flag if you'd like it prioritised.
- **Match dates.** Only finals carry full dates so far; leg dates can be
  backfilled from RSSSF's detail pages at any time (the schema already holds them).

## Data source

Historical results are transcribed from **RSSSF** (the Rec.Sport.Soccer
Statistics Foundation), James M. Ross's European competition pages. RSSSF content
is free to reproduce with acknowledgement.
