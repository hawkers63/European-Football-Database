**EuroDatabase Review (Read-Only)**  
**Date:** 4 September 2026  
**Author:** Grok  

This snapshot represents the v1.5 Classic Era data layer, encompassing the schema, canonical clubs, season dictionaries, builder, queries, CLI, and a lightweight app.py orchestrator operating on european_football.db. The integrity of the live file is confirmed as clean (PRAGMA integrity_check = ok, empty foreign_key_check). The counts align with the README: 2 lineages, 8 editions, 99 clubs, 38 rounds, 176 ties, and 352 matches. The verify() function against SEASONS currently indicates no aggregate mismatches.

Two critical scope facts should be noted prior to the findings:

The directories ui/, tests/, and tools/ are not present in this workspace. The app.py file imports ui.formatters, ui.theme, ui.data, ui.header, ui.sidebar, ui.tie_card, ui.bracket_view, and ui.club_dialog. Consequently, this structure cannot launch the viewer or execute the “112 tests” mentioned in README.md. The review herein regards app.py as a contract for a missing package rather than as a functional desktop application. Canonical club keys and the 1955–60 season dictionaries should remain unchanged. No recommendations are made regarding the rewriting of golden data.

**What is Already Sound**

- Each club corresponds to a single key and a single row. Referenced keys and CLUBS maintain a 1:1 relationship; there are no unused clubs or duplicate canonical names.
- Aggregates are computed rather than stored. The agg variable serves as a build-time witness for legs 1–2 only; play-off legs are appropriately excluded from this check.
- Settlement is consistent: aggregate/replay/single_match/coin_toss/walkover are applied uniformly. The CWC 1960-61 final is accurately represented as a two-legged aggregate, rather than a fictitious single match.
- Statistics in queries.py are derived from match/edition rows. Walkovers without scorelines are not erroneously treated as 3–0.
- The build(..., db_path=) function is already safe for testing.

These are the invariants to uphold.

**Findings (Ordered by Impact)**

1. **verify() Only Checks Two-Leg Aggregates**  
   The build_database.verify function recalculates legs 1–2 and checks the winner for aggregate/away_goals. However, it does not verify:  
   - The single_match winner against the only scoreline.  
   - The replay/coin_toss winner against the play-off (leg 3+).  
   - Walkover/bye instances that possess zero legs, a winner, and where aggregate is None.  
   - Instances where a two-legged aggregate tie has only one leg played.  

   The latter case pertains to live data: Vorwärts–Linfield, European Cup 1961-62 Preliminary, by="aggregate", agg=(3, 0), with only one leg played. Historically, Linfield withdrew after a 3–0 scoreline. While the printed aggregate aligns, the build remains green, the settlement type is incorrect, and any UI assuming two cards for aggregate will present an incomplete tie.

2. **club_name_history is Attached by season_label Across Lineages**  
   The build function:  
   ```python
   Pythonmatched = [(lin, lab, eid) for (lin, lab), eid in edition_ids.items() if lab == season_label]
   ```  
   This results in a 1960-61 history row for cwks_warsaw (Legia) and wismut being recorded for both the European Cup and Cup Winners’ Cup editions, despite neither club participating in the CWC that year. While the display is currently benign (as they do not appear on CWC cards), get_club_display_name(club_id, cwc_edition_id) is already incorrect, and v1.6 (with two lineages sharing more season labels) will exacerbate this issue.  
   Relatedly, the history rows for wismut and cca_buc repeat the canonical club.name, adding unnecessary noise without altering the display.

3. **Configured Lineages Are Not Inserted Unless a Season Exists**  
   LINEAGES includes the Inter-Cities Fairs Cup. The build function only inserts names appearing in SEASONS, leading to the live database reflecting only two lineages. Consequently, the UI competition menu and CLI cannot access a lineage that is already a v1.6 target. This represents a straightforward insert gap rather than a schema issue.

4. **match.notes Cannot Be Populated**  
   The schema.sql includes match.notes. However, queries._MATCH_SELECT and hat_trick_notes() read it, while MATCH_INSERT_SQL/match_insert_tuple()/L() extras do not write to it. Hat-trick and abandoned-leg details can only reside on tie.notes, which is why the stats layer currently reports “none stored”.

5. **Leaderboard Surface Area is Split**  
   The leaderboard_wins and leaderboard_goal_difference exist, and LEADERBOARD_SORT documents wins/gd. However, LEADERBOARD_KINDS and cli.py leaderboard only expose titles|matches|finals. DATA_GUIDE.md and ROADMAP.md already outline the additional types. This represents a wiring oversight rather than a need for new analytics.

6. **club_record(..., season_label=) Does Not Scope Hat-Tricks**  
   Match records, titles, and highest-scoring ties respect season_label, while hat_trick_notes(db, club_id=club_id) does not. A season-filtered cli.py goals CLUB --season YYYY-YY can display all-time notes under a season heading.

7. **Byes Are Documented, Not Modeled**  
   The 1961-62 notes indicate that Benfica, Fenerbahçe, and Haka received First Round byes, yet there are no bye ties recorded. Consequently, participant lists for the Preliminary Round are incomplete if derived solely from tie rows. It is advisable not to create bye rows without an RSSSF participant list; this should be documented as a known modeling gap for v1.6.

8. **Snapshot Incompleteness vs Documentation**  
   README.md continues to reference ui/, tools/import_rsssf.py, and 112 tests. In this structure, these paths are missing. This represents a packaging/synchronisation issue (the GitHub-parity agent brief exists for a reason). One should not attempt to “fix” this by integrating the UI back into app.py.

9. **Schema Comment Drift (Non-Blocking)**  
   The schema.sql still states that period names are “noted [on club] for now; a full club-name-history table is a later concern” just above the table that already exists. Stale comments can lead to future seeders placing aliases solely in club.notes.  

None of the aforementioned issues compromise the integrity of the 1955–60 golden scorelines.

### Targeted Fixes
Incremental and modular adjustments without a complete architectural overhaul.

#### Fix A — Extend `verify()` for Settlement Types
**Location:** `build_database.py`  
**Task:** Replace the body of the `verify()` function after the existing two-leg aggregate loop, ensuring that the current aggregate arithmetic is maintained while appending the additional checks.

```python
PythonALLOWED_BY = {
    "aggregate", "away_goals", "replay", "penalties",
    "coin_toss", "single_match", "walkover", "bye",
}

def verify(cur, club_id, seasons=None):
    """Recompute aggregates and verify settlement consistency against SEASONS."""
    problems = []
    for s in (SEASONS if seasons is None else seasons):
        for rnd in s["rounds"]:
            for tie in rnd["ties"]:
                a, b = tie["t1"], tie["t2"]
                ga = gb = 0
                tag = f'{s["season_label"]} {rnd["name"]}: {a} v {b}'
                by = tie.get("by")
                win = tie.get("win")
                legs = tie.get("legs") or []

                if by not in ALLOWED_BY:
                    problems.append(f"!! BY   {tag}: unknown decided_by={by!r}")

                if win and win not in (a, b):
                    problems.append(f"!! WIN  {tag}: winner {win} is not {a} or {b}")

                for idx, leg in enumerate(legs):
                    h, aw, hs, as_, _ = leg_fields(leg)
                    if h not in (a, b) or aw not in (a, b):
                        problems.append(
                            f"!! CLUB {tag} leg {idx + 1}: {h} v {aw} is not among ({a}, {b})")
                        continue
                    if idx >= 2:
                        continue
                    if h == a:
                        ga += hs
                    if aw == a:
                        ga += as_
                    if h == b:
                        gb += hs
                    if aw == b:
                        gb += as_

                if tie["agg"] is not None and (ga, gb) != tuple(tie["agg"]):
                    problems.append(
                        f"!! AGG  {tag}: legs give {ga}-{gb}, "
                        f"RSSSF states {tie['agg'][0]}-{tie['agg'][1]}")

                if by == "aggregate":
                    if len(legs) == 1:
                        problems.append(
                            f"!! LEGS {tag}: decided_by=aggregate but only 1 leg "
                            f"(withdrawal should be recorded as walkover, or note a missing 2nd leg)")
                    winner = a if ga > gb else (b if gb > ga else None)
                    if winner != win:
                        problems.append(
                            f"!! WIN  {tag}: higher aggregate is {winner}, data indicates {win}")

                if by == "away_goals":
                    if ga != gb:
                        problems.append(
                            f"!! AG   {tag}: decided_by=away_goals but aggregate is {ga}-{gb}")
                    else:
                        aa = ab = 0
                        for idx, leg in enumerate(legs):
                            if idx >= 2:
                                continue
                            h, aw, hs, as_, _ = leg_fields(leg)
                            if aw == a:
                                aa += as_
                            if aw == b:
                                ab += as_
                        winner = a if aa > ab else (b if ab > aa else None)
                        if winner != win:
                            problems.append(
                                f"!! AG   {tag}: away goals {aa}-{ab} imply {winner}, data indicates {win}")

                if by == "single_match":
                    if len(legs) != 1:
                        problems.append(
                            f"!! LEGS {tag}: single_match expects 1 leg, has {len(legs)}")
                    elif win:
                        h, aw, hs, as_, _ = leg_fields(legs[0])
                        scored_home = a if h == a else b
                        actual = scored_home if hs > as_ else (
                            (b if scored_home == a else a) if as_ > hs else None)
                        if actual and actual != win:
                            problems.append(
                                f"!! WIN  {tag}: single-match score implies {actual}, data indicates {win}")

                if by in ("replay", "coin_toss"):
                    if len(legs) < 3:
                        problems.append(
                            f"!! LEGS {tag}: {by} requires a play-off leg, has {len(legs)}")
                    elif by == "replay" and win:
                        h, aw, hs, as_, _ = leg_fields(legs[2])
                        if hs != as_:
                            po_home = a if h == a else b
                            actual = po_home if hs > as_ else (b if po_home == a else a)
                            if actual != win:
                                problems.append(
                                    f"!! WIN  {tag}: play-off score implies {actual}, data indicates {win}")

                if by in ("walkover", "bye"):
                    if legs:
                        problems.append(
                            f"!! LEGS {tag}: {by} should have 0 legs, has {len(legs)}")
                    if tie["agg"] is not None:
                        problems.append(f"!! AGG  {tag}: {by} should have agg=None")
                    if not win:
                        problems.append(f"!! WIN  {tag}: {by} has no declared winner")
    return problems
```

Following the implementation of this change, please revise the Linfield entry in `seasons.py` for the 1961-62 Preliminary round, rather than diluting the new rule:

```python
Python{"t1": "vorwarts", "t2": "linfield", "win": "vorwarts", "by": "walkover", "agg": None,
 "legs": [],
 "note": "Linfield withdrew after a 3-0 first leg (30 Aug 1961). "
         "Vorwärts were denied UK visas; Linfield could not travel to an alternative venue. "
         "RSSSF records the played 3-0; it is not stored as a completed two-leg aggregate."},
```

If you wish to maintain the played 3–0 as a match row for improved goal statistics, this requires a separate, minor settlement value. This can be achieved by setting `by="aggregate"` and including the one-leg exception only when the note indicates “withdrew.” I would refrain from introducing a new `by` token until version 1.6 has recorded two or three withdrawals after the first leg.

**Fix B** — Scope the name history to the editions that a club has actually contested.  
Location: `build_database.py`, within the `CLUB_NAME_HISTORY` loop.

```python
def _editions_contested_by(club_key, seasons, edition_ids):
    """Return (lineage, season_label, edition_id) for the editions in which the club actually appears."""
    labels = set()
    for season in seasons:
        if club_key in (season.get("winner"), season.get("runner_up")):
            labels.add((season["lineage"], season["season_label"]))
            continue
        for round in season["rounds"]:
            for tie in round["ties"]:
                if club_key in (tie["t1"], tie["t2"], tie.get("win")):
                    labels.add((season["lineage"], season["season_label"]))
                    break
    return [(lin, lab, edition_ids[(lin, lab)])
            for (lin, lab) in labels if (lin, lab) in edition_ids]
```

Within the `build()` function, replace the "matched = [...] if lab == season_label" block with the following:

```python
contested = _editions_contested_by(key, SEASONS, edition_ids)
matched = [(lin, lab, eid) for (lin, lab, eid) in contested if lab == season_label]
```

The same table will be used without any schema changes. The CWC 1960-61 will cease to inherit names from the Legia/Wismut period.

**Fix C** — Insert every configured lineage and persist optional match notes.  
Location: `build_database.py` lineage loop, along with `leg_fields` extras.

```python
# Replace:
for name in dict.fromkeys(s["lineage"] for s in SEASONS):
for name in list(LINEAGES) + [s["lineage"] for s in SEASONS if s["lineage"] not in LINEAGES]:
    if name in lineage_id:
        continue
    note = LINEAGES.get(name, "")
    if name not in LINEAGES:
        print("WARNING: lineage %r has no LINEAGES entry; inserting with empty notes." % name)
    cur.execute("INSERT INTO lineage (name, notes) VALUES (?,?)", (name, note))
    lineage_id[name] = cur.lastrowid
```

The empty Fairs Cup lineage will then be queryable. Ensure the UI/CLI displays “no editions yet” instead of hiding the trophy line.

```python
MATCH_INSERT_SQL = """INSERT INTO match
   (tie_id, leg_number, match_date, home_club_id, away_club_id,
    home_score, away_score, home_pens, away_pens, after_extra_time,
    venue, attendance, referee, notes)
   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""

def match_insert_tuple(tie_id, leg_number, club_id, leg):
    h, a, hs, as_, x = leg_fields(leg)
    return (
        tie_id, leg_number, x.get("date"), club_id[h], club_id[a], hs, as_,
        x.get("home_pens"), x.get("away_pens"),
        1 if x.get("aet") else 0, x.get("venue"), x.get("att"), x.get("ref"),
        x.get("notes"),
    )
```

The `L()` function already accepts `**extras`, allowing a seeder to write `L(..., notes="abandoned after 88 minutes; result stood")` without requiring a new helper.

**Fix D** — Connect the existing wins and goal difference leaderboards.  
Location: `queries.py` (one tuple) and `cli.py` for the `cmd_leaderboard` titles dictionary.

```python
# queries.py
LEADERBOARD_KINDS = ("titles", "matches", "wins", "gd", "finals")

# cli.py cmd_leaderboard titles / print branches
titles = {
    "titles": "All-time leaderboard: titles won",
    "matches": "All-time leaderboard: matches played / wins / goal difference",
    "wins": "All-time leaderboard: matches won",
    "gd": "All-time leaderboard: goal difference",
    "finals": "All-time leaderboard: finals reached (champion + runner-up)",
}
```

Utilise the existing matches print layout for wins and goal difference; refrain from adding a third table format.

**Fix E** — Acknowledge the `season_label` in the club record hat-trick notes.  
Location: `queries.py`, within `club_record()`.

```python
edition_id = None
if season_label:
    rows = editions_for_season(db, season_label)
    # The notes helper is per edition; collect across lineages in that label
    notes = []
    for edition in rows:
        notes.extend(hat_trick_notes(db, club_id=club_id, edition_id=edition["edition_id"]))
    rec["hat_trick_notes"] = notes
else:
    rec["hat_trick_notes"] = hat_trick_notes(db, club_id=club_id)
```

### Three Lightweight Features

All three features prioritise query and CLI functionality. The viewer can utilise the same helper functions subsequently; none necessitate the creation of a new table or a UI rewrite.

**Feature 1 — Club Campaign Path**  
Track a club's progress through a single edition, detailing the rounds reached, opponents, settlements, and scorelines. This is the yearbook page that stakeholders are particularly interested in when selecting a club.  
Insert: New functions at the end of `queries.py`. Wire: `cli.py` subparser path.

```python
def club_campaign(db: CursorLike, club_id: int, season_label: str) -> list:
    """Retrieves details for a club's participation in ``season_label``, ordered by the earliest round.

    Includes walkovers. Scorelines are sourced solely from stored match rows.
    """
    get_club(db, club_id)
    cur = _cursor(db)
    rows = cur.execute(
        """SELECT t.tie_id, t.club_a_id, t.club_b_id, t.winner_club_id,
                  t.decided_by, t.notes,
                  r.name AS round_name, r.round_order,
                  e.edition_id, e.season_label, e.competition_name,
                  l.name AS lineage_name
             FROM tie t
             JOIN round r ON r.round_id = t.round_id
             JOIN edition e ON e.edition_id = r.edition_id
             JOIN lineage l ON l.lineage_id = e.lineage_id
            WHERE e.season_label = ?
              AND (t.club_a_id = ? OR t.club_b_id = ?)
            ORDER BY e.competition_name, r.round_order, t.tie_id""",
        (season_label, club_id, club_id),
    ).fetchall()
    
    out = []
    for t in rows:
        opp_id = t["club_b_id"] if t["club_a_id"] == club_id else t["club_a_id"]
        matches = list(cur.execute(
            """SELECT home_club_id, away_club_id, home_score, away_score,
                      after_extra_time, venue, match_date, leg_number
                 FROM match WHERE tie_id = ? ORDER BY leg_number""",
            (t["tie_id"],),
        ))
        out.append({
            "edition_id": t["edition_id"],
            "competition_name": t["competition_name"],
            "lineage_name": t["lineage_name"],
            "season_label": t["season_label"],
            "round_name": t["round_name"],
            "round_order": t["round_order"],
            "opponent_id": opp_id,
            "opponent": get_club_display_name(cur, opp_id, t["edition_id"]),
            "won": t["winner_club_id"] == club_id,
            "decided_by": t["decided_by"],
            "notes": t["notes"],
            "legs": [
                {
                    "leg_number": m["leg_number"],
                    "date": m["match_date"],
                    "home": get_club_display_name(cur, m["home_club_id"], t["edition_id"]),
                    "away": get_club_display_name(cur, m["away_club_id"], t["edition_id"]),
                    "home_score": m["home_score"],
                    "away_score": m["away_score"],
                    "after_extra_time": bool(m["after_extra_time"]),
                    "venue": m["venue"],
                }
                for m in matches
            ],
        })
    return out
```

**CLI Shape:**  
```bash
python cli.py path benfica 1961-62
```
This will return results such as: Preliminary bye (if modelled) / First Round Austria / QF Nürnberg / SF Tottenham / Final Real Madrid. Once the `ui/` is reinstated, `ClubProfileDialog` can invoke the same helper for the loaded season, eliminating the need for a second query stack.

---

**Feature 2 — Edition Chronology (Dated Matches Only)**  
The 1961-62 season already has 55/55 dates; earlier finals are also dated. A chronology is immediately beneficial and remains transparent regarding missing dates, omitting undated rows rather than fabricating them.  
Insert: `queries.py`. Wire: `cli.py chronology`.

```python
def edition_chronology(db: CursorLike, season_label: str) -> list:
    """Retrieves matches in ``season_label`` that possess an ISO date, ordered from oldest to newest."""
    cur = _cursor(db)
    editions = editions_for_season(db, season_label)
    if not editions:
        raise KeyError("unknown season %s" % season_label)
    
    rows = cur.execute(
        _MATCH_SELECT + """
         WHERE e.season_label = ?
           AND m.match_date IS NOT NULL
         ORDER BY m.match_date, r.round_order, m.leg_number, m.match_id""",
        (season_label,),
    ).fetchall()
    
    return [{
        "date": m["match_date"],
        "competition_name": m["competition_name"],
        "round_name": m["round_name"],
        "leg_number": m["leg_number"],
        "home": get_club_display_name(cur, m["home_club_id"], m["edition_id"]),
        "away": get_club_display_name(cur, m["away_club_id"], m["edition_id"]),
        "home_score": m["home_score"],
        "away_score": m["away_score"],
        "after_extra_time": bool(m["after_extra_time"]),
        "venue": m["venue"],
    } for m in rows]
```
This is also an opportune moment to display a one-line coverage footer (dated/total) to ensure that the v1.6 date backfill has a measurable threshold without necessitating a new dashboard.

---

**Feature 3 — Winner-Path Overlay Helper (UI-Ready, No New Widgets)**  
The fixtures list and bracket already render every tie. Highlighting the champion’s route can be achieved through a filter over existing data, rather than creating a new view.  
Insert: `queries.py` (operates from a payload or from SQL). If `ui.data.fetch_edition_payload` is reinstated, invoke this from `App._render_fixtures` / `BracketView.populate` and pass `highlight=True` into `render_tie_card`.

```python
def winner_path_club_ids(db: CursorLike, edition_id: int) -> set:
    """Retrieves club IDs along the champion's route, including the champion.

    Traverses ties where the winner is the edition champion. Safe when the
    champion field is NULL (returns an empty set).
    """
    cur = _cursor(db)
    ed = cur.execute(
        "SELECT winner_club_id FROM edition WHERE edition_id = ?",
        (edition_id,),
    ).fetchone()
    if not ed or not ed["winner_club_id"]:
        return set()
    
    champ = ed["winner_club_id"]
    rows = cur.execute(
        """SELECT t.club_a_id, t.club_b_id, t.winner_club_id
             FROM tie t
             JOIN round r ON r.round_id = t.round_id
            WHERE r.edition_id = ? AND t.winner_club_id = ?""",
        (edition_id, champ),
    ).fetchall()
    
    ids = {champ}
    for t in rows:
        ids.add(t["club_a_id"])
        ids.add(t["club_b_id"])
    
    return ids
```
In the fixtures loop, a simple one-line membership test suffices:
```python
path_ids = winner_path_club_ids(self.cur, payload["edition"]["edition_id"])
# when rendering a tie:
on_path = tie["club_a_id"] in path_ids and tie["club_b_id"] in path_ids
```
There is no need for a new widget class; the existing victory-green token in the yearbook palette is already designated for this purpose.

---

**Suggested Application Order:**  
1. Fix A + Linfield settlement (prevents a green build from obscuring a one-leg “aggregate”).
2. Fix B + C (name-history scoping, empty Fairs lineage, utilisation of the match notes column).
3. Fix D + E (CLI/docs already indicate this behaviour).

Implement Feature 1, followed by Feature 2, and then Feature 3 — each is independently deployable and testable with a temporary `build(..., db_path=)`.

Please refrain from integrating group-stage or Swiss-phase work into any of the aforementioned features. That will remain reserved for v2.0 / `modern_era_parser`, and the 1955–60 dictionaries will remain untouched.

---