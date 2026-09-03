# audits_005.md — GitHub agent briefs, issue template, and CI workflow

Date: 2026-09-03 (Europe/London)
Branch: `feat/database-engineer` @ `e2d0854`
Executed: remainder of `agents/github_sync_manager.md` (Cloud Agents unavailable on plan; landed locally and pushed)

## Shipped to origin

`e2d0854` — Add GitHub agent briefs, issue template, and database verify workflow.
Pushed `b09d0e8..e2d0854` to `origin/feat/database-engineer`. Not force. Not main.

### Created
- `agents/modern_era_parser.md`
- `agents/ci_cd_guardian.md`
- `agents/stats_analyst.md`
- `.github/ISSUE_TEMPLATE/agent_task.yml`
- `.github/workflows/verify_database.yml`
- `requirements.txt` (`pytest`)

### Updated
- `AGENTS.md` — catalogue + Cloud/GitHub mandate; repo-relative links
- `agents/README.md` — same

## Gates
- `python -m pytest tests -q` — 69 passed
- Database rebuild PASS: lineage=2, club=91, club_name_history=9, edition=7, round=33, tie=148, match=297

## Not done
- Pull request into `main`: `gh` is not authenticated on Hawkeye.
- Cursor Cloud Agents: not available on the current plan.
- Left untracked: `notes/00_Audits/audits_001.md`–`audits_004.md` (and this file), `tests/test_ui_overhaul.py`, `ui/` (real UI work, not part of this commit).

## Sync checker
`feat/database-engineer` `[SYNCED]` with origin. Working tree `[DIRTY]` only because of those untracked notes/UI files.
