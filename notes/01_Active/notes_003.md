### Read-Only Progress Audit

Date: 2026-09-04
Author: Mark

The project boasts a robust and thoroughly tested vertical slice, encompassing the Classic Era data model, a deterministic database build, multi-lineage support, a modernised desktop user interface, CI infrastructure, a statistics layer, and the implementation of an additional European Cup season, all of which are present within the repository. The primary risk has transitioned from foundational architecture to integration drift. Numerous completed features reside on unmerged branches or solely in the current index, while discrepancies exist among the roadmap, README, schema comments, agent catalogue, issue template, and audit-note numbering regarding what is deemed complete.

No files were modified during this audit.

### 1. Completed Features Currently on Main

The branches `main` and `origin/main` are at commit `c860008`, which incorporates PR #1 and PR #2.

- **Classic Knockout Foundation:**
  - The knockout schema, canonical clubs, aggregate verification, and the European Cup seasons from 1955-56 to 1959-60 are marked as complete in [ROADMAP.md (line 12)](C:\\EuroDatabase\\ROADMAP.md:12).
  - The original build and data milestones are outlined in [CHANGELOG.md (line 51)](C:\\EuroDatabase\\CHANGELOG.md:51) and [CHANGELOG.md (line 62)](C:\\EuroDatabase\\CHANGELOG.md:62).

- **Data-Layer Expansion:**
  - Features such as `club_name_history`, period names, lineages, the 1960-61 European Cup, the inaugural 1960-61 Cup Winners’ Cup, RSSSF importer, and CLI are included in the v1.2 work detailed at [CHANGELOG.md (line 39)](C:\\EuroDatabase\\CHANGELOG.md:39).
  - The database engineer's shipment records the same deliverables in [audits_000.txt (line 4)](C:\\EuroDatabase\\notes\\00_Audits\\audits_000.txt:4).

- **Quality Assurance Stabilisation:**
  - Eleven confirmed defects have been addressed, including issues with lost tie notes, missing attendance, layout overlaps, N+1 lookups, third-club verification, shootout persistence, and replay/coin-toss displays. Further details can be found in [audits_002.md (line 7)](C:\\EuroDatabase\\notes\\00_Audits\\audits_002.md:7) and in the defect table at [audits_002.md (line 11)](C:\\EuroDatabase\\notes\\00_Audits\\audits_002.md:11).
  - This pass reported a green build with 50 tests at the time, as noted in [audits_002.md (line 44)](C:\\EuroDatabase\\notes\\00_Audits\\audits_002.md:44).

- **Modular Desktop User Interface:**
  - `app.py` now serves as a shell over the `ui/` package, featuring fixtures and bracket views, club profiles, rich match cards, period-accurate names, dark/light mode, caching, and a missing-database screen. For more information, see [CHANGELOG.md (line 32)](C:\\EuroDatabase\\CHANGELOG.md:32) and [audits_001.md (line 6)](C:\\EuroDatabase\\notes\\00_Audits\\audits_001.md:6).
  - The bracket milestone has been confirmed at [ROADMAP.md (line 25)](C:\\EuroDatabase\\ROADMAP.md:25).
  - UI helper tests reported positive results in the latest UI-specific audit, with 40 tests passing as noted in [audits_010.md (line 37)](C:\\EuroDatabase\\notes\\00_Audits\\audits_010.md:37).

- **GitHub and CI Scaffolding:**
  - The verify workflow is established and executes the build along with the test suite, as indicated in [.github/workflows/verify_database.yml (line 1)](C:\\EuroDatabase.github\\workflows\\verify_database.yml:1).
  - The agent-task issue form is available at [.github/ISSUE_TEMPLATE/agent_task.yml (line 1)](C:\\EuroDatabase.github\\ISSUE_TEMPLATE\\agent_task.yml:1).
  - Their initial shipment and the then-current gates are documented in [audits_005.md (line 7)](C:\\EuroDatabase\\notes\\00_Audits\\audits_005.md:7).

### 2. Implemented but Not Yet Integrated into Main

**Statistics, v1.4**

The branch `feat/stats-analyst` is at commit `449225c` and contains two commits not yet merged into main. It currently lacks a configured upstream in the existing branch listing. The delivered work includes:

- Shared head-to-head, goal, and leaderboard queries in `queries.py`.
- CLI commands in `cli.py`.
- Temporary-database regression tests in `tests/test_stats.py`.
- Documentation updates in `CHANGELOG.md`, `DATA_GUIDE.md`, and `notes/00_Audits/audits_008.md`.

The detailed scope can be found at [CHANGELOG.md (line 15)](C:/EuroDatabase/CHANGELOG.md:15), with the audit documenting 104 passing tests, successful builds, and CLI smoke tests at that historical checkpoint, as noted in [audits_008.md (line 107)](C:/EuroDatabase/notes/00_Audits/audits_008.md:107). This feature is functionally complete but remains unshipped until it is rebased onto the current main, retested, pushed, and merged.

**European Cup 1961-62, v1.5**

The current index contains a staged, uncommitted change set of 290 lines across nine files, which adds:

- European Cup 1961-62.
- Eight new clubs and period-name records.
- RSSSF aliases.
- Updates to data, display, import, and statistics tests.
- Revisions to the changelog, guide, and roadmap.

The staged roadmap already marks the 1961-62 season as complete at [ROADMAP.md (line 21)](C:/EuroDatabase/ROADMAP.md:21), with the staged release entry beginning at [CHANGELOG.md (line 3)](C:/EuroDatabase/CHANGELOG.md:3).

A read-only query of the current generated database has revealed:

- 2 lineages
- 99 clubs
- 11 period-name rows
- 8 editions
- 38 rounds
- 176 ties
- 352 matches

The current implementation is situated on the feat/stats-analyst branch, while the nominal feat/season-1961-62 branch still references commit 370fd2d, which lacks any season implementation. This mismatch between branches and tasks must be addressed prior to advancing any further feature development.

Additionally, there are four related stashes, including “pre-rebase” and mixed stats/seeder work in progress. These should only be compared once the staged work has been safely committed; redundant stashes should be retained until their contents have been verified as duplicates.

### Group/Swiss Foundations

The feat/modern-era-parser branch is at commit ddd27c0, is synced with origin/feat/modern-era-parser, and has not yet been merged. This branch introduces approximately 1,900 lines of code, which encompass the following:

- Additive standings/group/league schema.
- Metadata for points_for_win, standings-tiebreak, and phase-type.
- Group and Swiss parsers.
- A ranking engine.
- Classic-era golden tests.
- A fragment of the 1991-92 European Cup group stage/final.
- A miniature Swiss-format fixture.
- Competition-transfer modelling.

This significantly meets the parser brief outlined in [agents/modern_era_parser.md (line 32)](C:/EuroDatabase/agents/modern_era_parser.md:32). However, it remains a foundation and proof of concept, lacking complete v2/v3 coverage. A follow-up note, which is not tracked, explicitly indicates that the full 36-club ingestion and league-table UI remain unfinished.

### Confirmed Documentation and Task Drift

The README is notably outdated:

- [README.md (line 5)](C:\\EuroDatabase\\README.md:5) states that the current dataset concludes at 1959-60.
- [README.md (line 20)](C:\\EuroDatabase\\README.md:20) hard-codes 76 clubs, 112 ties, and 228 matches.
- [README.md (line 39)](C:\\EuroDatabase\\README.md:39) again asserts 112 verified ties.
- The current staged/generated dataset includes 99 clubs, 176 ties, and 352 matches, encompassing the European Cup through 1961-62, along with the 1960-61 CWC.
- [README.md (line 48)](C:\\EuroDatabase\\README.md:48) claims that period club names are only in notes and points to a planned display feature, despite the club_name_history and period-accurate UI labels already being implemented.

Hard-coded row counts will become outdated almost every season; they should either be generated during a release or labelled “as of version X”.

### ROADMAP Contradictions

The ROADMAP contains inconsistencies:

- [ROADMAP.md (line 49)](C:\\EuroDatabase\\ROADMAP.md:49) correctly indicates that period-accurate names are complete.
- [ROADMAP.md (line 50)](C:\\EuroDatabase\\ROADMAP.md:50) states that they still need to be integrated throughout the viewer, while [CHANGELOG.md (line 35)](C:\\EuroDatabase\\CHANGELOG.md:35) asserts that every club label already employs them.
- [ROADMAP.md (line 51)](C:\\EuroDatabase\\ROADMAP.md:51) redundantly suggests that a club_name_history table may be added in the future.
- [ROADMAP.md (line 29)](C:\\EuroDatabase\\ROADMAP.md:29) mentions that group support will require “no change to existing tables”, while the modern parser appropriately introduces nullable columns to edition and round. The intended assurance is “no breaking rewrite”, not literally “no table change”.
- The away-goals support is designated for v3 at [ROADMAP.md (line 44)](C:\\EuroDatabase\\ROADMAP.md:44), despite the same line indicating that the rule commences in 1965-66. This must be completed before Classic Era seeding reaches 1965-66.

While the away-goals flag exists, the build_database.verify() function currently validates decided_by == "away_goals" without considering the edition’s away_goals_active value. Consequently, the v3 checkbox remains legitimately open; the feature is stored but not fully flag-driven.

### Schema Comments Reflect an Outdated Schema

- [schema.sql (line 2)](C:\\EuroDatabase\\schema.sql:2) still refers to itself as “Schema v1.0”.
- [schema.sql (line 4)](C:\\EuroDatabase\\schema.sql:4) states that group and Swiss phases are absent.
- [schema.sql (line 29)](C:\\EuroDatabase\\schema.sql:29) asserts that club-name history is a future concern.
- The actual club_name_history table is present at [schema.sql (line 124)](C:\\EuroDatabase\\schema.sql:124).

The modern parser branch partially updates the header but retains duplicated prose and continues to refer to it as Schema v1.0.

### Agent Catalogue and Issue Form Exclude the Season Seeder

- AGENTS.md includes the season seeder at [AGENTS.md (line 37)](C:\\EuroDatabase\\AGENTS.md:37).
- The quick-reference table in [agents/README.md (line 9)](C:\\EuroDatabase\\agents\\README.md:9) concludes with the stats analyst and omits it.
- The execution graph at [agents/README.md (line 23)](C:\\EuroDatabase\\agents/README.md:23) outlines parser → stats → UI and lacks a seeding track, despite statistics being documented as parallelisable and seeding being an ongoing data track.
- The role dropdown at [.github/ISSUE_TEMPLATE/agent_task.yml (line 16)](C:\\EuroDatabase.github\\ISSUE_TEMPLATE\\agent_task.yml:16) does not include the season_seeder.

A more precise execution graph would branch after the data-layer foundation into three parallel tracks—season seeding, statistics, and modern-format parsing—before converging for UI integration and continuous integration.

### Several Agent Briefs Mischaracterise Completed Work as Upcoming Tasks

- [AGENTS.md (line 38)](C:\\EuroDatabase\\AGENTS.md:38) and [agents/season_seeder.md (line 14)](C:\\EuroDatabase\\agents\\season_seeder.md:14) still designate 1961-62 as the default next target.
- [agents/season_seeder.md (line 79)](C:\\EuroDatabase\\agents\\season_seeder.md:79) reiterates that default in its deliverables.
- The next target for the European Cup is now 1962-63, following the commitment of the staged work.
- [agents/ui_ux_developer.md (line 83)](C:\\EuroDatabase\\agents\\ui_ux_developer.md:83) hard-codes “all 5 seeded seasons”, which is already outdated.
- QA/database/UI/stats briefs retain unchecked acceptance lists, even where their audits confirm delivery. This practice is only acceptable if these files are explicitly labelled as reusable role contracts rather than live status trackers.

### Active Notes Are Not Active

- [notes_000.md (line 1)](C:\\EuroDatabase\\notes\\01_Active\\notes_000.md:1) is the original project proposal, using pre-implementation table names and both “current 32-team group stage” at line 6 and “now 36-team” at line 50.
- [notes_001.md (line 13)](C:\\EuroDatabase\\notes\\01_Active\\notes_001.md:13) is a completed QA report with all eleven findings marked as fixed.
- Retaining these in notes/01_Active diminishes the project’s perceived completeness. The proposal should be relocated to a vision/archive section, while the completed QA report should be stored with the audit history.

### Audit-Note Numbering Collisions Across Branches/Worktrees

- The current stats work contains notes/00_Audits/audits_008.md.
- Commit ddd27c0 on the parser branch also adds a different audits_008.md.
- Both the main/database worktree and parser worktree house differing untracked audits_009.md files.
- The parser’s untracked audits_009.md indicates that 008 is reserved for stats, yet the parser commit has already recorded its own 008.

These issues will lead to merge conflicts and compromise the intended sequential audit trail unless renamed prior to integration.

The documentation for the modern-parser branch requires attention prior to merging. 

- The CHANGELOG.md erroneously reuses version v1.3, which corresponds to the modular UI release; the current development has progressed to v1.4, with v1.5 on the horizon.
- The parser modifications logically align with the roadmap’s v2 foundation, such as v2.0-alpha, rather than being classified under another v1.3 release.
- The committed parser changelog includes control characters where Markdown backticks were anticipated: ESC at line 4, vertical tabs, and tabs surrounding identifiers on lines 7-15.
- The schema header features repeated phrasing of “never as a rewrite.”
- The roadmap indicates that transfer modelling is complete, yet it acknowledges that full multi-lineage population remains incomplete. The schema capability and populated historical data should be represented as separate checkboxes.
- The parser brief conflates the 36-team league phase with the older third-place-to-Europa transfer mechanism at [agents/modern_era_parser.md (line 47)](C:\\EuroDatabase\\agents\\modern_era_parser.md:47). These are distinct historical formatting issues and should be documented separately.

Remaining product gaps have already been identified by the project:

- Continuation of the European Cup from 1962-63: [ROADMAP.md (line 22)](C:\\EuroDatabase\\ROADMAP.md:22).
- Continuation of the Cup Winners’ Cup and seeding for the Inter-Cities Fairs Cup/UEFA Cup: [ROADMAP.md (line 24)](C:\\EuroDatabase\\ROADMAP.md:24).
- Addition of league-table rendering to the viewer: [ROADMAP.md (line 36)](C:\\EuroDatabase\\ROADMAP.md:36).
- Full ingestion of the 36-club Swiss league remains incomplete; the parser branch currently contains only a small sample.
- Completion of data-driven away-goals enforcement prior to 1965-66.
- Backfilling of non-final match dates: [ROADMAP.md (line 58)](C:\\EuroDatabase\\ROADMAP.md:58).
- Implementation of a genuine penalty shootout row; while current rendering and persistence has been unit-tested, the loaded data does not contain any: [audits_001.md (line 58)](C:\\EuroDatabase\\notes\\00_Audits\\audits_001.md:58).
- Integration of new statistics helpers into the viewer; the club profile continues to utilise separate batched SQL: [audits_008.md (line 126)](C:\\EuroDatabase\\notes\\00_Audits\\audits_008.md:126).
- A scorer/goal-event model is essential before reliable scorer or hat-trick leaderboards can be developed: [audits_008.md (line 128)](C:\\EuroDatabase\\notes\\00_Audits\\audits_008.md:128).
- Conduct a comprehensive GUI smoke test following branch integration. While automated UI helpers are functioning correctly, manual validation is still required for resizing, light/dark rendering, navigation across all loaded editions, and handling of irregular brackets.

Recommended next steps include the following sequence:

1. Temporarily halt new feature development to safeguard the current staged season.
   - Execute a full build and test suite against the staged state of 1961-62.
   - Commit this to a correctly named season branch, ensuring the current index is preserved and inspecting the four WIP stashes before any deletions.
   - Ensure the season implementation is not recorded on feat/stats-analyst while feat/season-1961-62 remains unpopulated.

2. Prioritise the integration of statistics.
   - Rebase or cherry-pick commits bc666e4 and 449225c onto the current main branch.
   - Conduct build, full tests, and CLI smoke tests.
   - Push a suitable upstream and merge a focused statistics pull request.

3. Integrate the European Cup 1961-62 as the second priority.
   - Rebase the season commit onto the newly integrated stats/main state to address statistics regressions, which are documented as v1.5.
   - Validate the accurate historical data from 1955-60, including the new champion, runner-up, representative aggregate, aliases, and unused-club tests.
   - Merge through its own pull request.

4. Repair and rebase the modern parser prior to merging.
   - Rebase its single feature commit onto the updated main branch.
   - Resolve overlaps in CHANGELOG.md, DATA_GUIDE.md, build_database.py, queries.py, clubs.py, seasons.py, tools/import_rsssf.py, and tests.
   - Rename its audit note to a unique number.
   - Eliminate changelog control bytes, amend the schema header, and assign a non-conflicting release label.
   - Maintain the already merged UI/bracket and 1961-62 roadmap state while incorporating the parser roadmap updates.
   - Execute a full build and tests, along with both parser dry-runs before opening the pull request.

5. Reconcile documentation within the same integration cycle.
   - Update the README to reflect scope and capabilities, removing or generating volatile row counts.
   - Eliminate outdated period-name references from the README, ROADMAP, and schema comments.
   - Categorise roadmap items into “schema/parser,” “representative data,” “full data,” and “viewer” to avoid confusion between proof-of-concept foundations and full product completion.
   - Include season_seeder in agents/README.md and the issue template.
   - Replace the hard-coded “5 seeded seasons” acceptance language with “all loaded editions.”
   - Move completed material out of notes/01_Active.
   - Incorporate explicit status and last-verified metadata into agent briefs if they are intended to convey current progress.

6. Resume coverage of the Classic Era in parallel, with one verified unit per pull request.
   - European Cup 1962-63.
   - Cup Winners’ Cup 1961-62.
   - Initial coverage of the Inter-Cities Fairs Cup, taking into account its multi-year edition label.
   - Ensure each track is additive, supported by RSSSF, and safeguarded by golden-data regressions.
   - The existing Fairs Cup worktree is clean at the old base, indicating that this track has not substantively commenced.

7. Advance the enforcement of the away-goals rule before reaching 1965-66.
   - Implement verification to reject decided_by="away_goals" when the edition flag is false.
   - Include positive and negative tests against the flag, rather than merely storing it.
   - Ensure the rule is edition-driven so that the eventual abolition in 2021 requires no hard-coded year logic.

8. Finalise the v2 user experience following the establishment of the parser foundation.
   - Display group standings alongside fixture and bracket views.
   - Reuse the shared standings and statistics helpers instead of introducing UI-only SQL.
   - Complete the full 1991-92 edition rather than leaving only a group/final fragment.
   - Add manual headed tests for navigation, resize behaviour, light/dark mode, period names, notes, attendance, and irregular rounds.

9. Only at this point should modern coverage be expanded.
   - Ingest a complete 36-team league phase.
   - Validate edition-specific UEFA tiebreak rules against published tables.
   - Distinguish historical cross-competition transfers from modern league-phase behaviour.
   - Add release packaging for the anticipated Windows standalone application once schema, data, and UI integration have stabilised.

In summary, while the foundations are significantly more advanced than the primary README suggests, the next milestone should focus on a clean, verified integration release rather than pursuing another independent feature branch.