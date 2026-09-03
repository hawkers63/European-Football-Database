# Autonomous Agent Task Directory (`AGENTS.md`)

This repository contains specialised agent task definitions located in the [`agents/`](agents/) directory. These task prompts are structured for immediate use by AI assistants (such as Grok Bots, Antigravity, or other LLM coding agents).

---

## Available Agent Task Prompts

1. **Bug Audit & QA Engineer**: [`agents/qa_auditor.md`](agents/qa_auditor.md)
   * **Mission**: Uncover and fix software bugs, edge-case scoring ambiguities, N+1 query bottlenecks, omitted data fields (attendance, tie notes), and layout geometry overlaps. Creates automated regression test suite (`tests/`).
   * **Recommended Execution**: Run first to stabilise the base.

2. **Database & Data Pipeline Engineer**: [`agents/database_engineer.md`](agents/database_engineer.md)
   * **Mission**: Schema expansion (`club_name_history` table for period-accurate club names), multi-competition lineage support (Cup Winners' Cup, UEFA Cup), RSSSF ingestion parser script, and stats query CLI.
   * **Recommended Execution**: Run second on top of the stabilised database.

3. **UI/UX Desktop Application Specialist**: [`agents/ui_ux_developer.md`](agents/ui_ux_developer.md)
   * **Mission**: Overhaul the CustomTkinter desktop interface (`app.py`), implement an interactive knockout tournament bracket view, rich match cards with metadata pills, and club profile inspector.
   * **Recommended Execution**: Run third to build the modern UI upon the bug-free, expanded data layer.

4. **GitHub Sync & Cloud Agent Orchestrator**: [`agents/github_sync_manager.md`](agents/github_sync_manager.md)
   * **Mission**: Verify parity between local workspace (`C:\EuroDatabase`) and remote GitHub repository (`origin`). Directs Cloud Agents operating in GitHub environments to author and manage new agent specifications, GitHub Actions workflows, and issue templates directly at GitHub.
   * **Recommended Execution**: Run before/after work and continuously to verify branch synchronisation.

5. **Modern Era Parser**: [`agents/modern_era_parser.md`](agents/modern_era_parser.md)
   * **Mission**: Parse 1990s Champions League group stages and the modern 36-team Swiss-model league phase as additive data. Must not corrupt Classic Era golden data (European Cup 1955-60). Parsers and tests may be added under `tools/` and `tests/`.
   * **Recommended Execution**: Phase 2b, after the database engineer, with golden-data regressions green.

6. **CI/CD Guardian**: [`agents/ci_cd_guardian.md`](agents/ci_cd_guardian.md)
   * **Mission**: Own GitHub Actions and pull-request verification. Gates are `python build_database.py --force` and `pytest tests/`. Never force-push to `main`; never skip hooks.
   * **Recommended Execution**: Continuous / DevOps, alongside the GitHub sync manager.

7. **Stats Analyst**: [`agents/stats_analyst.md`](agents/stats_analyst.md)
   * **Mission**: Head-to-head records, goal statistics, and all-time club leaderboards over `european_football.db`, with automated tests. Figures are derived from verified match rows, never hand-edited totals.
   * **Recommended Execution**: Phase 2c, after the database engineer; may run in parallel with the modern era parser.

8. **Classic Era Season Seeder**: [`agents/season_seeder.md`](agents/season_seeder.md)
   * **Mission**: Continue seeding verified knockout seasons from RSSSF: European Cup 1961-62 onward, Cup Winners' Cup after 1960-61, and Inter-Cities Fairs Cup → UEFA Cup as a new lineage. Must not touch Classic Era golden data (1955-60) and must not implement group/Swiss phases (that is `modern_era_parser.md`).
   * **Recommended Execution**: After the database engineer; default first target is European Cup 1961-62.

---

## Cloud / GitHub Mandate

When Cloud Agents are available on GitHub (or when this work is provisioned locally and pushed to `origin`), they must:

1. **Author briefs** in [`agents/`](agents/) for every specialised role, including the three modern-era / CI / stats briefs above.
2. **Author workflows** under [`.github/workflows/`](.github/workflows/), especially [`verify_database.yml`](.github/workflows/verify_database.yml) (`build_database.py --force` + `pytest tests/` on every push and pull request).
3. **Author issue templates** under [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/), especially [`agent_task.yml`](.github/ISSUE_TEMPLATE/agent_task.yml), so tasks can be filed against a role, summary, acceptance criteria, and branch.
4. **Keep bi-directional `agents/` sync**: briefs authored on GitHub are fetched down to `C:\EuroDatabase\agents/`; locally authored briefs are pushed up to `origin`. Never force-push to `main`.

For detailed documentation and the recommended sequencing graph, see [`agents/README.md`](agents/README.md).
