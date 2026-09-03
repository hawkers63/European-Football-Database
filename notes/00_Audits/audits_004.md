# audits_004.md — UI/UX pre-overhaul survey

Date: 2026-09-03 (Europe/London)
Branch inspected: `feat/database-engineer` (after Polly’s `84cbb1f` schema work)
Role: `agents/ui_ux_developer.md`

Read-only survey of `C:\EuroDatabase` on Hawkeye before the CustomTkinter overhaul was wired into `app.py`. Nothing in this note is a claim that the new viewer is already running.

## Snapshot at survey

| Item | Status |
|---|---|
| Layout | Monolith `app.py` (14,883 bytes, 373 lines, UTF-8). No `ui/` package at survey time. |
| DB | `european_football.db` present. Path is sibling of `app.py`. |
| CTk | 5.2.2 on Python 3.11 |
| Tests | `tests/test_ui_helpers.py` pins helpers and layout. `tests/test_integrity.py` is data/build. |
| Related notes | `notes/01_Active/notes_001.md` (earlier QA of the viewer). Sequential audits live in this folder. |

Polly’s completed database work (use this, do not ignore it):

- `club_name_history` + `queries.get_club_display_name(club_id, edition_id)` (MTK 1955-56 → Vörös Lobogó)
- Extra lineages / 1960-61 seasons, RSSSF importer, `cli.py`

## Gap analysis versus the UI/UX brief

### Modular layout (`ui/sidebar.py`, `header.py`, `tie_card.py`, `bracket_view.py`, `club_dialog.py`)
Missing at survey. Everything lived in one `App` class. Pure helpers were already extracted and unit-tested — keep them and re-export from `app` so `tests/test_ui_helpers.py` still `import app`.

### Top nav (breadcrumbs Lineage > Season > Round, search, Fixtures/Bracket switcher, dark/light toggle)
Missing except a single header label `{competition_name} {season_label}`. Appearance hardcoded `ctk.set_appearance_mode("dark")` / `set_default_color_theme("blue")`.

### Sidebar (competition/season, champions card, edition.notes, match/goal counts)
Partial. Competition + season menus, champion/runner-up banner, dim `edition.notes`. No trophy badge, no final score on the card, no match/goal counts.

### Knockout bracket + inspector
Missing. ROADMAP still had an unchecked “proper bracket view”. Linear fixtures list only. Bracket columns must use `round_order`, not round name (Preliminary / Qualifying / First Round vary by season).

### Rich fixture/tie cards
Partial, text not pills. Winner green / loser dim, aggregate header, match lines with venue/date/ref/attendance, italic amber notes callout, dynamic wraplength. Missing: country pills, aet/pens as badges, metadata badges, info-icon callout. `home_pens`/`away_pens` were not rendered (`format_match_line` only appended `(aet)`).

### Club profile modal
Missing. Club names were labels, not clickable. After Polly: aliases belong in `club_name_history`; on-screen labels must use `queries.get_club_display_name`.

### Polish checklist

| Item | At survey |
|---|---|
| `<Configure>` wraplength | Done (`wraplength_for_width` + write-gated bind) |
| Yearbook gold `#d4af37` / green `#2ea043` | Not used. Then: `WIN="#3ba55d"`, `NOTE="#d4b45a"` |
| British English | Neutral UI copy (“play-off”, “Champions”). Keep CTk APIs as `fg_color`. |
| `WM_DELETE_WINDOW` | Done — close cursor, then conn, then `destroy()` |
| Missing `.db` | Console `sys.exit` only — needs an in-window setup message |

## Data-access notes (avoid N+1)

Keep: `connect()` + one long-lived conn; `load_club_name_cache`; edition JOIN for winner/runner-up; helper formatters (tests pin them).

Extend the club cache to `{club_id: row}` (country, city, notes, period display name) so pills and the profile do not N+1.

Prefetch all matches for the edition (`WHERE round.edition_id=?`) and aggregate in Python. `_render_tie` previously selected matches per tie, and `tie_aggregate` queried legs 1–2 again.

Search should filter in-memory over the loaded edition.

Country codes are period RSSSF (FRG/GDR/TCH/SAA/YUG), not modern ISO — pills should show those.

## Layout pins tests must keep

- Header `row=0`, scroll `row=1`, sidebar `rowspan=2`
- `WM_DELETE_WINDOW`
- `load_club_name_cache` (or an equivalent cache still imported from `app`)

## Gotchas

1. UTF-8 source and DB (Vörös Lobogó, București, Saarbrücken, Atlético).
2. `CTkOptionMenu` `command=` fires on `.set()` — do not double-render.
3. `CTkFont(slant="italic")` may silently fall back; do not rely on italic for notes.
4. Variable round graphs (4 vs 5 rounds), byes/walkovers with empty legs (`w/o`).
5. Missing CustomTkinter at import sets `ctk=None` so helper tests run without a display.

## Follow-up

Implementation modules were drafted under `/workspace/eurodb-ui` and a shipment log was written as `audits_001.md` **ahead of a complete Hawkeye landing**. At the time this survey note was filed:

- Hawkeye `app.py` was still the 373-line monolith
- `ui/` on Hawkeye was partial (missing `bracket_view.py` and `data.py`)
- `tests/test_ui_overhaul.py` was not yet on Hawkeye

Do not treat `audits_001.md` as proof the new viewer is live until `app.py` is the modular shell and pytest is green on Hawkeye.
