# Changelog

## v1.1 — Classic Era, five-in-a-row
- Restructured seeding around a canonical club registry (`clubs.py`) keyed by
  short IDs, with fixtures in `seasons.py`. Adding a season is now one dict.
- Build-time verification: every tie's legs must reproduce RSSSF's printed
  aggregate, or the build aborts and writes nothing.
- Added European Cup **1956-57, 1957-58, 1958-59, 1959-60** (with 1955-56, the
  complete Real Madrid five-in-a-row): 76 clubs, 112 ties, 228 matches.
- Viewer: two-leg aggregate now excludes play-offs; play-offs, coin tosses and
  walkovers render distinctly.
- Docs: ROADMAP.md, DATA_GUIDE.md, CHANGELOG.md.

## v1.0 — Classic Era foundation
- SQLite schema for the unseeded two-legged knockout era.
- CustomTkinter season viewer with auto-aggregate and winner highlighting.
- Seeded the inaugural 1955-56 European Cup as a validation dataset.
