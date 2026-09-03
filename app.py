#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py - European Football Database viewer (Classic Era)

A CustomTkinter desktop viewer over `european_football.db`. Pick a competition
and season; each round renders as paired-fixture cards with the two-legged
aggregate auto-calculated and the winner highlighted. Play-offs, coin tosses,
walkovers and one-off finals are shown for what they are.

Requirements:  pip install customtkinter
Run:           python app.py   (run build_database.py first if the .db is missing)
"""

import os
import sqlite3
import sys

try:
    import customtkinter as ctk
except ImportError:
    ctk = None
    if __name__ == "__main__":
        sys.exit("CustomTkinter is not installed. Run:  pip install customtkinter")

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "european_football.db")

WIN = "#3ba55d"     # winner accent
DIM = "#8a8f98"     # secondary text / losing side
CARD = "#2b2d31"
HEAD = "#1e1f22"
NOTE = "#d4b45a"    # historical-note callout

# How each decision type is labelled in the UI.
DECISION_TAG = {
    "replay": "play-off", "coin_toss": "coin toss",
    "walkover": "walkover", "bye": "bye",
}

MATCH_SEP = "     \u00b7     "


def connect(path=None):
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _field(row, key, default=None):
    """Read a key from a mapping or sqlite3.Row, returning default if absent/NULL."""
    try:
        keys = row.keys() if hasattr(row, "keys") else None
        if keys is not None and key not in keys:
            return default
        val = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if val is None else val


def load_club_name_cache(cur):
    """Pre-load club_id -> name so tie rendering does not N+1 query the registry."""
    return {row["club_id"]: row["name"] for row in cur.execute(
        "SELECT club_id, name FROM club")}


def tie_aggregate(cur, tie):
    """Aggregate over the two legs only (a play-off is a separate decider)."""
    a, b = tie["club_a_id"], tie["club_b_id"]
    ga = gb = 0
    for m in cur.execute(
        "SELECT home_club_id, away_club_id, home_score, away_score "
        "FROM match WHERE tie_id=? AND leg_number IN (1,2)", (tie["tie_id"],)
    ):
        if m["home_score"] is None:
            continue
        if m["home_club_id"] == a: ga += m["home_score"]
        if m["away_club_id"] == a: ga += m["away_score"]
        if m["home_club_id"] == b: gb += m["home_score"]
        if m["away_club_id"] == b: gb += m["away_score"]
    return ga, gb


def format_attendance(attendance):
    """Return e.g. '135,000 spectators', or None when attendance is missing."""
    if attendance in (None, ""):
        return None
    try:
        n = int(attendance)
    except (TypeError, ValueError):
        return None
    return f"{n:,} spectators"


def match_extra_fragments(m):
    """Venue, date, referee and attendance fragments; empty values are omitted."""
    referee = _field(m, "referee")
    return [x for x in (
        _field(m, "venue"),
        _field(m, "match_date"),
        f"ref {referee}" if referee else None,
        format_attendance(_field(m, "attendance")),
    ) if x]


def format_match_line(home_name, away_name, m):
    seg = f"{home_name} {_field(m, 'home_score')}-{_field(m, 'away_score')} {away_name}"
    if _field(m, "after_extra_time"):
        seg += " (aet)"
    extras = match_extra_fragments(m)
    if extras:
        seg += "  (" + "; ".join(extras) + ")"
    return seg


def compose_tie_detail(parts, notes, separator=None):
    """
    Split match scores and historical notes.

    Notes are never discarded merely because match lines exist; the caller
    renders `notes_callout` in a distinct sub-label when it is non-empty.
    """
    if separator is None:
        separator = MATCH_SEP
    match_detail = separator.join(parts) if parts else ""
    notes_callout = notes or ""
    return match_detail, notes_callout


def _decider_leg(legs):
    """Third (or later) leg is the play-off / replay."""
    for m in legs:
        ln = _field(m, "leg_number")
        if ln is not None and int(ln) >= 3:
            return m
    if len(legs) >= 3:
        return legs[2]
    return None


def format_score_header(ga, gb, decided_by, legs):
    """
    Card header scoreline. Two-legged ties settled by replay or coin toss keep
    the aggregate visible but name the decider, so 5-5 is not mistaken for a
    scoring error.
    """
    if not legs:
        return "w/o"
    if decided_by == "single_match":
        return f"{ga} - {gb}"
    score = f"{ga}-{gb}"
    if decided_by == "replay":
        replay = _decider_leg(legs)
        if replay is not None and _field(replay, "home_score") is not None:
            hs = _field(replay, "home_score")
            aws = _field(replay, "away_score")
            score += f" (Replay: {hs}-{aws})"
    elif decided_by == "coin_toss":
        score += " (Coin Toss)"
    return score


def wraplength_for_width(width, padding=28, minimum=200):
    try:
        w = int(width)
    except (TypeError, ValueError):
        return minimum
    return max(minimum, w - padding)


def format_champion_banner(winner, runner_up):
    bits = []
    if winner:
        bits.append("\u2605 Champions\n%s" % winner)
    if runner_up:
        bits.append("Runner-up\n%s" % runner_up)
    return "\n\n".join(bits)


class App(ctk.CTk if ctk is not None else object):
    def __init__(self):
        if ctk is None:
            raise RuntimeError("CustomTkinter is not installed. Run:  pip install customtkinter")
        super().__init__()
        self.title("European Football Database - Classic Era")
        self.geometry("1000x740")
        self.minsize(840, 560)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.conn = connect()
        self.cur = self.conn.cursor()
        self._club_names = {}

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self._build_sidebar()
        self._build_main()
        self._load_competitions()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        try:
            if getattr(self, "cur", None) is not None:
                self.cur.close()
            if getattr(self, "conn", None) is not None:
                self.conn.close()
        finally:
            self.destroy()

    def _build_sidebar(self):
        bar = ctk.CTkFrame(self, width=250, corner_radius=0)
        bar.grid(row=0, column=0, rowspan=2, sticky="nsw")
        bar.grid_propagate(False)
        ctk.CTkLabel(bar, text="European Football\nDatabase",
                     font=ctk.CTkFont(size=20, weight="bold"), justify="left"
                     ).pack(padx=20, pady=(24, 2), anchor="w")
        ctk.CTkLabel(bar, text="The Classic Era", text_color=DIM
                     ).pack(padx=20, pady=(0, 24), anchor="w")

        ctk.CTkLabel(bar, text="Competition").pack(padx=20, pady=(0, 4), anchor="w")
        self.competition_menu = ctk.CTkOptionMenu(bar, values=["-"], width=210,
                                                  command=self._on_competition)
        self.competition_menu.pack(padx=20, pady=(0, 16), anchor="w")
        ctk.CTkLabel(bar, text="Season").pack(padx=20, pady=(0, 4), anchor="w")
        self.season_menu = ctk.CTkOptionMenu(bar, values=["-"], width=210,
                                            command=self._on_season)
        self.season_menu.pack(padx=20, pady=(0, 16), anchor="w")
        self.champ_label = ctk.CTkLabel(bar, text="", text_color=WIN, wraplength=210,
                                        justify="left", font=ctk.CTkFont(size=13, weight="bold"))
        self.champ_label.pack(padx=20, pady=(24, 0), anchor="w")
        self.edition_notes_label = ctk.CTkLabel(
            bar, text="", text_color=DIM, wraplength=210, justify="left",
            font=ctk.CTkFont(size=12))
        self.edition_notes_label.pack(padx=20, pady=(12, 16), anchor="w")

    def _build_main(self):
        self.header = ctk.CTkLabel(self, text="", anchor="w",
                                   font=ctk.CTkFont(size=22, weight="bold"))
        self.header.grid(row=0, column=1, sticky="ew", padx=24, pady=(16, 8))
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scroll.grid(row=1, column=1, sticky="nsew", padx=16, pady=(0, 16))
        self.scroll.grid_columnconfigure(0, weight=1)

    def _load_competitions(self):
        self.lineages = {r["name"]: r["lineage_id"]
                         for r in self.cur.execute("SELECT lineage_id, name FROM lineage ORDER BY name")}
        names = list(self.lineages) or ["-"]
        self.competition_menu.configure(values=names)
        self.competition_menu.set(names[0]); self._on_competition(names[0])

    def _on_competition(self, name):
        lid = self.lineages.get(name)
        self.editions = {}
        if lid is not None:
            for r in self.cur.execute(
                "SELECT edition_id, season_label FROM edition WHERE lineage_id=? ORDER BY start_year", (lid,)):
                self.editions[r["season_label"]] = r["edition_id"]
        labels = list(self.editions) or ["-"]
        self.season_menu.configure(values=labels)
        self.season_menu.set(labels[-1]); self._on_season(labels[-1])

    def _on_season(self, label):
        eid = self.editions.get(label)
        if eid is not None:
            self._render_edition(eid)

    def _render_edition(self, edition_id):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._club_names = load_club_name_cache(self.cur)
        ed = self.cur.execute(
            "SELECT e.*, w.name AS winner, ru.name AS runner_up FROM edition e "
            "LEFT JOIN club w ON w.club_id=e.winner_club_id "
            "LEFT JOIN club ru ON ru.club_id=e.runner_up_club_id "
            "WHERE e.edition_id=?",
            (edition_id,)).fetchone()
        self.header.configure(text=f"{ed['competition_name']}  {ed['season_label']}")
        self.champ_label.configure(text=format_champion_banner(ed["winner"], ed["runner_up"]))
        self.edition_notes_label.configure(text=ed["notes"] or "")

        r = 0
        for rnd in self.cur.execute(
            "SELECT * FROM round WHERE edition_id=? ORDER BY round_order", (edition_id,)):
            ctk.CTkLabel(self.scroll, text=rnd["name"].upper(), anchor="w",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         fg_color=HEAD, corner_radius=6, padx=12, pady=6
                         ).grid(row=r, column=0, sticky="ew", pady=(14, 6)); r += 1
            for tie in self.cur.execute(
                "SELECT * FROM tie WHERE round_id=? ORDER BY tie_id", (rnd["round_id"],)):
                self._render_tie(tie, r); r += 1

    def _club_name(self, club_id):
        name = self._club_names.get(club_id)
        if name is None:
            row = self.cur.execute("SELECT name FROM club WHERE club_id=?", (club_id,)).fetchone()
            name = row[0] if row else "?"
            self._club_names[club_id] = name
        return name

    def _attach_dynamic_wrap(self, card, *labels, padding=28):
        def _on_configure(event, widget=card, lbls=labels, pad=padding):
            if event.widget is not widget:
                return
            wrap = wraplength_for_width(event.width, padding=pad)
            for lbl in lbls:
                if int(lbl.cget("wraplength") or 0) != wrap:
                    lbl.configure(wraplength=wrap)
        card.bind("<Configure>", _on_configure)

    def _render_tie(self, tie, row):
        card = ctk.CTkFrame(self.scroll, fg_color=CARD, corner_radius=8)
        card.grid(row=row, column=0, sticky="ew", pady=4)
        for col, wt in ((0, 1), (1, 0), (2, 1)):
            card.grid_columnconfigure(col, weight=wt)
        a_name, b_name = self._club_name(tie["club_a_id"]), self._club_name(tie["club_b_id"])
        winner = tie["winner_club_id"]
        a_col = WIN if winner == tie["club_a_id"] else DIM
        b_col = WIN if winner == tie["club_b_id"] else DIM

        legs = self.cur.execute(
            "SELECT * FROM match WHERE tie_id=? ORDER BY leg_number", (tie["tie_id"],)).fetchall()
        if legs:
            ga, gb = tie_aggregate(self.cur, tie)
            score = format_score_header(ga, gb, tie["decided_by"], legs)
        else:
            score = format_score_header(0, 0, tie["decided_by"], [])

        ctk.CTkLabel(card, text=a_name, anchor="e", text_color=a_col,
                     font=ctk.CTkFont(size=15, weight="bold")
                     ).grid(row=0, column=0, sticky="e", padx=(14, 8), pady=(10, 0))
        ctk.CTkLabel(card, text=score, font=ctk.CTkFont(size=15, weight="bold")
                     ).grid(row=0, column=1, padx=6, pady=(10, 0))
        ctk.CTkLabel(card, text=b_name, anchor="w", text_color=b_col,
                     font=ctk.CTkFont(size=15, weight="bold")
                     ).grid(row=0, column=2, sticky="w", padx=(8, 14), pady=(10, 0))

        parts = []
        for m in legs:
            hn, an = self._club_name(m["home_club_id"]), self._club_name(m["away_club_id"])
            parts.append(format_match_line(hn, an, m))
        match_detail, notes_callout = compose_tie_detail(parts, tie["notes"])
        tag = DECISION_TAG.get(tie["decided_by"], "")
        prefix = f"[{tag}]  " if tag else ""
        detail_text = prefix + match_detail
        wrap_labels = []
        detail_pady = (2, 4) if notes_callout else (2, 10)
        if detail_text.strip():
            detail_lbl = ctk.CTkLabel(card, text=detail_text, text_color=DIM,
                                      font=ctk.CTkFont(size=12), anchor="center", wraplength=680)
            detail_lbl.grid(row=1, column=0, columnspan=3, sticky="ew", padx=14, pady=detail_pady)
            wrap_labels.append(detail_lbl)
        if notes_callout:
            note_lbl = ctk.CTkLabel(card, text=notes_callout, text_color=NOTE,
                                    font=ctk.CTkFont(size=12, slant="italic"),
                                    anchor="center", wraplength=680)
            note_lbl.grid(row=2, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 10))
            wrap_labels.append(note_lbl)
        if wrap_labels:
            self._attach_dynamic_wrap(card, *wrap_labels)


if __name__ == "__main__":
    if ctk is None:
        sys.exit("CustomTkinter is not installed. Run:  pip install customtkinter")
    if not os.path.exists(DB_PATH):
        sys.exit("european_football.db not found. Run:  python build_database.py")
    App().mainloop()
