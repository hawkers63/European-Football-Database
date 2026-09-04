### Overall Assessment

**Date:** 4th September 2026  
**Author:** Mark

The project currently boasts a robust working version 1.x vertical slice. Its architecture, reminiscent of the knockout era, along with the generated SQLite database, modular desktop user interface, statistical queries, command-line interface, RSSSF drafting tool, and automated tests, provides a solid foundation. 

However, it is not yet prepared for an extensive feature sprint or a tagged release. The primary bottleneck now lies in integration and release hygiene: completed statistics work, staged data for the 1961–62 season, and experimental work in modern formats are distributed across various branches and worktrees, while several correctness issues remain obscured by the otherwise successful test suite. 

In summary:  
The engineering foundation is sufficiently mature for the currently established Classic Era, yet the state of the repository requires consolidation, and historical data coverage is still in its infancy.

No files, branches, stashes, references, or databases were altered during this review.

**Progress Snapshot**

| Area                    | Current Position                                                                                       | Assessment             |
|-------------------------|-------------------------------------------------------------------------------------------------------|------------------------|
| Knockout Data Model     | Lineages, editions, rounds, ties, legs, period club names, aggregates, replays, walkovers, and coin tosses are represented | Strong Foundation       |
| Current Staged Dataset   | 2 seeded lineages, 8 editions, 99 clubs, 38 rounds, 176 ties, 352 matches                          | Internally Coherent     |
| European Cup Coverage   | 1955–56 through 1961–62                                                                             | Seven Complete Seasons  |
| Other Competitions      | Inaugural 1960–61 Cup Winners’ Cup                                                                   | Started, but Limited Breadth |
| Fairs Cup              | Lineage configured, no substantive season data yet                                                  | Pending                 |
| Desktop Application      | Fixtures, bracket view, search, dark/light modes, period names, champion/runner-up context, club profiles | Substantial v1 UI      |
| Statistics              | Club records, head-to-head, goals, highest-scoring ties, and leaderboards                           | Implemented on an Unmerged Branch |
| CLI                     | club, h2h, goals, leaderboard, season, and export                                                  | Mostly Functional; Export has a Serious Bug |
| Import Tooling          | Common RSSSF rows, aliases, aggregate checks, season-block output                                   | Useful, but Unsafe for Unattended Bulk Ingestion |
| Automated Verification   | 112 tests passing; 27 Python files compile; SQLite integrity and foreign keys clean                  | Good Baseline with Important Blind Spots |
| Group/Swiss Formats     | Experimental branch with schema/parser/ranking prototypes and sample data                            | Proof of Concept, Not Completed v2/v3 |
| Windows Packaging        | No package metadata, PyInstaller specification, artifact build, release workflow, or tags           | Not Started             |

The temporary database rebuild was successful, yielding:
- 2 lineages
- 99 clubs
- 11 generated period-name rows
- 8 editions
- 38 rounds
- 176 ties
- 352 matches

The SQLite integrity check returned successful results, with no violations found in the foreign key check, and additional read-only checks identified no negative scores, duplicate leg numbers, same-club fixtures, orphaned match clubs, invalid tie winners, broken edition-final winners, or broken round progression in the current data. 

**Metadata Coverage Remains Uneven:**
- Dates: 63 out of 352 matches
- Venues: 56 out of 352
- Attendance: 9 out of 352
- Referees: 9 out of 352
- Persisted Match Notes: 0 out of 352

All 55 matches in the newly staged 1961–62 European Cup possess dates, indicating that the newer seeding work is already more complete than the earlier seasons.

**Immediate Release Blockers**

1. **JSON Export Silently Truncates Tournaments**  
   This is the highest-priority functional defect. The nested export loops reuse a single lazy SQLite cursor in `*_export_edition()` (line 343). Each inner execute() resets its parent iteration. A read-only reproduction of the 1955–56 export yielded:
   - 1 round instead of 4
   - 1 tie instead of 15
   - 1 match instead of 29  
   This constitutes silent data loss in a user-facing command. The existing pipeline test only verifies CLI help and does not ascertain the validity of exported structure. The statistics pull request should not be merged until export tests confirm the full round/tie/match counts, particularly for multi-competition seasons such as 1960–61.

2. **Current Checkout Mixes Two Features**  
   The active checkout is feat/stats-analyst at commit 449225c, with no upstream. Relative to the locally cached origin/main, it is two commits ahead and three behind. Its two commits pertain to the v1.4 statistics work; however, the index also contains nine staged files—290 insertions and seven deletions—for the separate v1.5 European Cup 1961–62 seed. This discrepancy is evident in the staged CHANGELOG.md (line 3) and the new season beginning in seasons.py (line 495). The nominal feat/season-1961-62 branch does not encompass that implementation. This branch/task mismatch should be resolved prior to any rebase, commit, or new work. There are also four stashes, two of which are identical safety copies of the current staged v1.5 tree and should remain intact until both feature branches have been reconstructed and verified.

3. **Forced Database Rebuilding is Not Atomic**  
   The `build(force=True)` function (line 83) deletes the existing database before loading, building, or verifying the replacement. Should the validation subsequently fail, the newly created database is also deleted. This means a failed --force operation eradicates the last known-good database, despite the module's assertion that a failed build writes nothing. The builder should create and validate a temporary sibling database, successfully closing it before employing an atomic replacement only after:
   - Source validation passes
   - Aggregate and settlement checks are successful
   - Foreign key checks pass
   - Integrity checks are successful
   - The transaction commits successfully  
   A failure-path regression should commence with a sentinel destination database, demonstrating that it remains untouched following invalid input.

4. **Match.notes Exists, But Data Pipeline Cannot Populate It**  
   The schema defines match.notes, and the statistics layer queries it; however, the canonical pipeline is incomplete. 
   - Leg extras do not document notes in seasons.py (line 14).
   - The insert statement and tuple builder omit notes in build_database.py (line 30).
   - JSON export does not include notes.
   - Fixture and bracket renderers do not display them.
   - The only test directly injects a note with SQL, bypassing the source and builder.  
   This should evolve into a proper source → builder → database → query → export/UI round-trip prior to expanding scorer or hat-trick annotations.

5. **Period-name History is Duplicated Across Competitions**  
   The history builder matches aliases solely by season, inserting one copy for each competition edition sharing that season at build_database.py (line 165). Since the 1960–61 season includes both the European Cup and Cup Winners’ Cup, this currently results in duplicate facts for:
   - CWKS Warsaw / Legia Warsaw
   - Wismut Karl-Marx-Stadt  
   This duplication is visible to users. The command `python cli.py club cwks_warsaw` outputs “Legia Warsaw” twice. The model should differentiate:
   - A season-wide historical name: one row with no specific edition; or
   - A competition-specific name: a source entry explicitly naming the lineage/edition.  
   A uniqueness rule and defensive presentation deduplication should accompany the fix.

6. **Validation Needs Strengthening Before Later Eras**  
   The current verifier checks club membership, printed aggregates, aggregate winners, and away-goal winners. However, it does not thoroughly validate:
   - Whether away_goals is permitted by the edition's away_goals_active flag
   - Replay winner against the deciding match
   - Single-match winner against the score
   - Penalty winner and paired penalty values
   - Coin-toss/replay prerequisites
   - Walkover and bye shape
   - Edition champion and runner-up against the final
   - Complete score and leg-number invariants  
   The current data passed separate read-only checks for these conditions, yet the canonical builder itself should enforce them before the project transitions to the away-goals era. Work on away-goals must be prioritised from the roadmap’s v3 section, as the historical rule begins to impact Classic Era data in 1965–66.

7. **RSSSF Importer Can Silently Omit Input**  
   The importer located at tools/import_rsssf.py (line 338) skips non-comment lines it cannot parse without reporting them. Consequently, during a bulk import, an entire fixture could potentially disappear without notice.

The system can also emit a level aggregate with the literal string "win": "None" and by: "aggregate" when a decider cannot be resolved. 

Before relying on it for ongoing seeding, the importer should:
- Report every ignored non-blank line along with its line number.
- Fail unless the omission is explicitly permitted.
- Differentiate headings, comments, malformed results, walkovers, and unresolved deciders.
- Emit a genuine None or an explicit unresolved/TODO state.
- Address away goals, penalties, ambiguous orientations, and round boundaries through testing.

**Repository and Documentation Status**  
The locally cached main/origin/main is at c860008, which includes the merged v1.3 modular UI baseline. However, the statistics and the work from 1961–62 have yet to be integrated.

Additionally, there are two distinct untracked files named audits_009.md in separate worktrees, as well as an untracked audits_010.md in the current checkout. These files contain different content, necessitating the reconciliation of audit numbering prior to any commits or the removal of worktrees.

The pushed feat/modern-era-parser branch is one commit ahead and seven behind the cached origin/main. While it contains a significant proof of concept, merging it as-is is inadvisable due to:
- Conflicting audit-note numbering.
- A reused v1.3 changelog version.
- Control-character corruption within its changelog.
- Overlaps with the UI, statistics, season, schema, importer, and roadmap work.
- Only partial data for the 1991–92 season and miniature Swiss samples.
- Absence of a league-table UI.

Given that this branch has already been shared remotely, merging the updated main into it is a safer option than rewriting its history, unless all collaborators explicitly consent to a rebase.

**Documentation is Significantly Behind Implementation**  
- The [README.md (line 5)](C:/EuroDatabase/README.md:5) still indicates that coverage ends in 1959–60 and reports outdated totals of 76 clubs, 112 ties, and 228 matches.
- The [ROADMAP.md (line 49)](C:/EuroDatabase/ROADMAP.md:49) lists period names as complete, only to describe them as deferred immediately afterwards.
- The [schema.sql (line 2)](C:/EuroDatabase/schema.sql:2) still refers to itself as schema v1.0 and mentions that club-name history is a future concern, despite defining that table subsequently.
- Both [agents/README.md (line 9)](C:/EuroDatabase/agents/README.md:9) and the [agent issue form (line 16)](C:/EuroDatabase/.github/ISSUE_TEMPLATE/agent_task.yml:16) omit the role of the season-seeder.
- The season-seeder brief continues to identify the now-completed 1961–62 season as its default next target.
- Completed reports remain in notes/01_Active, which inflates the appearance of the active backlog.

The CI workflow serves as a useful baseline; however, its installation command at [verify_database.yml (line 11)](C:/EuroDatabase/.github/workflows/verify_database.yml:11) may obscure a problematic requirements installation. Since requirements.txt includes only pytest, a successful installation does not install CustomTkinter. Currently, CI tests only on Ubuntu/Python 3.11 and does not cover the Windows desktop runtime.

**Recommended Next Steps**  
1. Preserve and untangle the existing Git work.  
   Prior to rebasing or changing branches:
   - Avoid deleting stashes, branches, worktrees, conducting git gc, or pruning.
   - Allocate unique names for the two different audits_009.md files and the current audits_010.md.
   - Capture one additional recoverable snapshot, including the staged v1.5 files and untracked audit note.
   - Ensure the snapshot can reproduce the current green state of 99 clubs and 352 matches.
   - Restore feat/stats-analyst to a stats-only worktree.

A fresh remote fetch should be conducted prior to integration, but only after current work has been safely preserved. This review intentionally utilised existing local references without altering them.

2. Complete and integrate v1.4 statistics.  
   On the statistics branch:
   - Rectify the JSON export truncation.
   - Add comprehensive export regressions for 1955–56 and multi-lineage 1960–61.
   - Resolve smaller future-facing statistics issues:
     - Season-scoped club records should not incorporate hat-trick notes from other seasons.
     - Tie-level notes should not be repeated for each leg.
   - Preserve a backup reference.
   - Update the branch to align with the current main.
   - Rebuild the temporary database, execute all tests, and conduct a smoke test of the CLI.
   - Push with a correctly configured upstream and merge through a focused pull request.

3. Integrate v1.5 for the European Cup 1961–62.

Following the completion of the statistics phase:

1. Recreate or expedite the features for the 1961–62 season based on the updated core.
2. Initially apply the preserved staged season work without destructive alterations.
3. Execute the database build and comprehensive test suite.
4. Confirm the following:
   - Benfica as the champion
   - Real Madrid as the runner-up
   - Aggregate results for Benfica and Tottenham
   - Play-off results for Juventus and Real Madrid
   - Withdrawal of Linfield
   - Period names for Feyenoord and Haka
   - Absence of unused clubs
   - Integrity of classic 1955–60 golden data
5. Commit and merge these changes as a distinct pull request for version 1.5.
6. Complete a milestone focused on pipeline hardening.

Prior to initiating the 1962–63 season, implement a targeted hardening release that encompasses:
- Atomic verification for database replacement
- Comprehensive validation specific to settlements
- Alignment of edition winners and finals
- Proper persistence and export/display of match notes
- Correct cardinality for historical names
- Temporary database fixtures for all tests reliant on the database
- Loud failure reporting for RSSSF parsing
- Integrity checks for SQLite within the build gate

Seventeen current tests depend on the pre-existing european_football.db, which can be bypassed on a fresh checkout rather than validating database behaviour. The more robust methodology currently employed by the statistics tests—creating a temporary database—should be adopted as the standard practice.

7. Reconcile documentation and continuous integration.
A small, separate pull request should:
- Rectify the README to accurately reflect coverage and capabilities.
- Remove or dynamically generate volatile row counts instead of hard-coding them indefinitely.
- Reconcile completed and pending roadmap items.
- Update outdated schema comments.
- Incorporate the season_seeder into the agent index, execution graph, and issue form.
- Adjust the seeder’s default target for the European Cup to the 1962–63 season.
- Move completed notes from notes/01_Active.
- Replace CI’s dependency fallback with deterministic runtime and development dependencies.
- Introduce a Windows import/smoke job.
- Ensure that unexpected test skips result in CI failures.
- Verify the actual status of GitHub Actions, required checks, and branch protection settings online.

A tagged release should only proceed once the branch contents, changelog version, and documentation consistently describe the same commit.

8. Resume seeding for the Classic Era.
Once the hardening gate is implemented, the subsequent data sequence should include:
1. European Cup 1962–63
2. Cup Winners’ Cup 1961–62
3. Inter-Cities Fairs Cup 1955–58, ensuring accommodation for its multi-year edition label
4. Progress each competition through small, independently reviewable season pull requests
5. Implement edition-driven away-goals enforcement prior to 1965–66

Each season pull request should encompass:
- A specific source reference
- Validation of champion and runner-up
- At least one representative aggregate test
- Tests for oddities, withdrawals, and replays as applicable
- Temporary database build
- Regression tests for the golden 1955–60 data
- Absence of unused clubs or importer warnings
- Updated generated counts

Given that seasons.py currently stands at 648 lines for eight editions, it is advisable to maintain the public SEASONS contract while beginning to segment future data into competition/year modules before the file expands excessively.

9. Integrate modern formats only once the baseline is stable.
Subsequently, repair and integrate the modern-parser branch by:
- Resolving overlaps with the new core.
- Renaming its audit note and changelog version.
- Removing control characters.
- Maintaining "schema capability," "representative sample," "complete historical edition," and "viewer support" as distinct roadmap milestones.
- Completing a full 1991–92 edition instead of retaining only a fragment.
- Constructing the standings UI using shared ranking/query code rather than relying solely on UI-specific SQL.
- Validating a complete 36-team league phase only after the group-era model has stabilised.

10. Ensure robust validation for desktop applications and packaging.
Although the helper-level UI tests are beneficial, no tests currently instantiate a real Application, bracket, sidebar, dialog, or rendered card. Prior to designating the desktop application as releasable:
- Conduct a manual smoke test across every loaded edition in a headed environment.
- Test for resizing and DPI scaling.
- Validate both appearance modes.
- Assess long notes, irregular brackets, period names, attendance, and club dialogues.
- Introduce a minimal automated window construction, switching, and closure smoke test where a virtual display is available.
- Define Windows packaging and produce a PyInstaller artifact.
- Only after these steps should release tags and a Windows artifact workflow be added.

Recommended immediate milestone:
I propose naming the next milestone “v1.5 Consolidation and Pipeline Hardening.” Its definition of completion should include:
- Statistics and the 1961–62 data on separate, appropriately named branches, merged in sequence.
- JSON export yielding exactly 4 rounds, 15 ties, and 29 matches for the 1955–56 season.
- A deliberately failed forced build that preserves the legacy database.
- Round-trip match notes from source to database and output.
- Historical-name queries devoid of duplicate entries.
- All database-dependent tests constructed from a temporary fixture.
- Full tests remaining successful with no unexpected skips.
- Agreement among the README, roadmap, changelog, agent catalogue, and issue form with the merged state.
- A clean working tree and supporting worktrees, with accurate upstream mappings.

Following the completion of this milestone, the next appropriate feature task will be the European Cup for the 1962–63 season.