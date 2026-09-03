# Autonomous Agent Task Directory (`AGENTS.md`)

This repository contains three specialized agent task definitions located in the [`agents/`](file:///C:/EuroDatabase/agents/) directory. These task prompts are structured for immediate use by AI assistants (such as Grok Bots, Antigravity, or other LLM coding agents).

---

## Available Agent Task Prompts

1. **Bug Audit & QA Engineer**: [`agents/qa_auditor.md`](file:///C:/EuroDatabase/agents/qa_auditor.md)
   * **Mission**: Uncover and fix software bugs, edge-case scoring ambiguities, N+1 query bottlenecks, omitted data fields (attendance, tie notes), and layout geometry overlaps. Creates automated regression test suite (`tests/`).
   * **Recommended Execution**: Run first to stabilize the base.

2. **Database & Data Pipeline Engineer**: [`agents/database_engineer.md`](file:///C:/EuroDatabase/agents/database_engineer.md)
   * **Mission**: Schema expansion (`club_name_history` table for period-accurate club names), multi-competition lineage support (Cup Winners' Cup, UEFA Cup), RSSSF ingestion parser script, and stats query CLI.
   * **Recommended Execution**: Run second on top of the stabilized database.

3. **UI/UX Desktop Application Specialist**: [`agents/ui_ux_developer.md`](file:///C:/EuroDatabase/agents/ui_ux_developer.md)
   * **Mission**: Overhaul the CustomTkinter desktop interface (`app.py`), implement an interactive knockout tournament bracket view, rich match cards with metadata pills, and club profile inspector.
   * **Recommended Execution**: Run third to build the modern UI upon the bug-free, expanded data layer.

For detailed documentation and the recommended sequencing graph, see [`agents/README.md`](file:///C:/EuroDatabase/agents/README.md).
