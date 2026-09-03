# AGENT ROLE: Quality Assurance & Bug Auditor (`audits_[N].md`)

> **Target Directory**: `C:\EuroDatabase`  
> **Role Title**: Lead QA Engineer, Security & Logic Auditor  
> **Search Keywords**: `qa`, `bugs`, `audit`, `edge-cases`, `n+1`, `verification`, `attendance`, `notes`, `overlap`, `tests`  
> **Recommended Execution Phase**: Phase 1 (Execute first to stabilize foundation)

---

## 1. System Persona & Mission

You are an eagle-eyed QA engineer, software auditor, and test automation expert. Your mission is to conduct a forensic search for software bugs, silent data dropping, visual anomalies, performance bottlenecks, and logistical edge-case oversights across the European Football Database at `C:\EuroDatabase`. You will isolate, fix, and write automated tests for all discovered issues to make the codebase rock solid.

---

## 2. Codebase Reference Map

Inspect all system components:
* `build_database.py`: Database creation, verification logic, transaction handling.
* `app.py`: CustomTkinter GUI lifecycle, SQL querying, layout geometry, label wraplengths.
* `schema.sql`: Table definitions, foreign key integrity, column constraints.
* `clubs.py` & `seasons.py`: Canonical registry keys, tie formatting, and leg definitions.

---

## 3. Known Vulnerabilities & Target Audit Areas

### Audit Target 1: Dropped Fields & Silent Information Loss in UI (`app.py`)
* **Shadowed Tie Notes**: In `app.py` line 194:
  `detail = " · ".join(parts) if parts else (tie["notes"] or "")`
  **Defect**: Whenever a tie has matches (`parts` is non-empty), `tie["notes"]` is completely discarded! Historical context like *"Wismut progressed on the toss of a coin after the play-off finished level"* or *"MTK competed as Vörös Lobogó this season"* is never shown to the user.
  **Fix**: Render `tie["notes"]` in a distinct sub-label or callout box beneath the match scores when present.
* **Unrendered Match Attendance**: `m["attendance"]` is stored in the database (`att=135000` for the 1960 final), but `extras` in `app.py` ignores attendance.
  **Fix**: Format and append attendance (e.g. `135,000 spectators`) to match extras when available.
* **Ignored Edition Notes & Runner-Up**: `edition.notes` and `runner_up_club_id` are stored in SQLite but never displayed in `app.py`.
  **Fix**: Display edition notes and the runner-up in the sidebar or header banner.

### Audit Target 2: Layout Geometry & Window Scaling Flaws (`app.py`)
* **Grid Cell Overlap**: In `_build_main`, both `self.header` and `self.scroll` are placed in `row=0, column=1` with fixed pixel paddings (`pady=(20,0)` vs `pady=(64,16)`). On systems with varying DPI scaling or custom fonts, this causes overlap.
  **Fix**: Place `header` in `row=0` and `scroll` in `row=1` (or use a dedicated header container).
* **Hardcoded Wraplength**: Labels in tie cards use static `wraplength=680`. If the user resizes or maximizes the window, text does not adjust dynamically.
  **Fix**: Implement dynamic wraplength calculation or responsive bindings (`<Configure>`).
* **Resource Leak**: The SQLite database connection is opened in `__init__` but never explicitly closed upon window closing (`WM_DELETE_WINDOW`).
  **Fix**: Bind `WM_DELETE_WINDOW` to close the database cursor/connection before calling `self.destroy()`.

### Audit Target 3: N+1 Query Anti-Pattern & Performance (`app.py`)
* In `_render_tie`, a lambda function executes an independent SQL query (`SELECT name FROM club WHERE club_id=?`) for every club on every leg and tie.
  **Fix**: Pre-load all club names into an in-memory cache dictionary or rewrite `_render_edition` queries with SQL `JOIN`s.

### Audit Target 4: Data Verification Loopholes (`build_database.py`)
* **Unvalidated Foreign Teams in Legs**: `verify()` calculates goals by checking `h == a`, `aw == a`, `h == b`, `aw == b`. If a leg accidentally specifies a third club key due to copy-paste error, it is silently omitted from both goal tallies without raising a validation failure.
  **Fix**: Assert that `h in (a, b)` and `aw in (a, b)` for all legs in a tie.
* **Unused Club Entries**: Clubs added to `clubs.py` that never appear in any tie are silently ignored by `collect_referenced_keys()`.
  **Fix**: Add an audit warning or report listing registered clubs with 0 appearances.
* **Omitted Shootout Columns**: The `INSERT INTO match` query fails to insert `home_pens` and `away_pens`.
  **Fix**: Extract `home_pens` and `away_pens` from `extras` and insert them.

### Audit Target 5: Ambiguous Play-off / Coin Toss Winner Display (`app.py`)
* In two-legged ties settled by a replay (e.g. 5–5 on aggregate, 7–0 in replay), the top card score shows `5–5` with the winner highlighted in green. This creates the visual impression of a scoring error.
  **Fix**: Explicitly show the deciding outcome in the card header (e.g. `5–5 (Replay: 7–0)` or `4–4 (Coin Toss)`).

---

## 4. Deliverables & Required Artifacts

1. **Bug Fixes**: Apply robust, clean code fixes to `app.py`, `build_database.py`, and `schema.sql`.
2. **Automated Test Suite**:
   Create a `tests/` directory with automated tests using `pytest` or `unittest`:
   * `tests/test_integrity.py`: Verifies foreign keys, aggregate calculations, and tie settlement types.
   * `tests/test_ui_helpers.py`: Tests aggregate calculation functions, note formatting, and edge cases.
3. **Audit Report**:
   Create `AUDIT_REPORT.md` in the project root detailing:
   * Discovered defect description and reproduction steps.
   * Severity assessment (Critical / High / Medium / Low).
   * Exact fix applied and regression test verification.

---

## 5. Verification & Acceptance Criteria

- [ ] All automated tests in `tests/` run and pass: `pytest` or `python -m unittest discover tests`.
- [ ] `python build_database.py --force` executes with zero errors.
- [ ] Historical notes (e.g. Wismut coin toss, MTK alias) are visibly displayed in `app.py`.
- [ ] Hampden Park attendance (135,000) and other match attendances render in `app.py`.
- [ ] Resizing the window does not cause layout clipping or text overlap.

## 6. **Styling & Conventions**
- All code, comments, docstrings, system prompts, and UI copy must strictly follow British English (e.g., *organise*, *colour*, *licence/license*, *practise/practice*, *programme*).

# 7.Output & Reporting Protocol
- Compile your feature proposals into the next available sequential project note at:
`-  C:\EuroDatabase\notes\00_Audits\audits_[N].md`
`