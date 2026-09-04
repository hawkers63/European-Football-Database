# audits_009 — Polly v1.2 data-layer confirm

Date: 2026-09-03 (Europe/London)
Agent: Polly
Worktree: C:\EuroDatabase-dbeng
Branch/SHA: feat/database-engineer @ 5ac574406fb974c541c5526b309b4a77eb5d7768

## Scope checked (v1.2 data slice)
- club_name_history table + index in schema.sql — present
- lineages.py LINEAGES (European Cup, Cup Winners' Cup, Inter-Cities Fairs Cup) — present
- EC 1960-61 + CWC 1960-61 in seasons.py — present
- tools/import_rsssf.py — present
- cli.py — present
- queries.get_club_display_name — present

## Verification
- pytest: 69 passed
- build_database.py --force: clean; lineage=2, club=91, club_name_history=9, edition=7
- MTK 1955-56 → Vörös Lobogó; MTK 1959-60 → MTK Budapest

## Known hole (do not duplicate)
- Inter-Cities Fairs Cup is in LINEAGES but unseeded in seasons.py — Jenny/season seeder territory

## Out of scope
- Did not touch ui/ or force-push main
