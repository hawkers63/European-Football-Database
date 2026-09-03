#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py - European Football Database viewer (Classic Era)

A CustomTkinter desktop viewer over `european_football.db`. Pick a competition
and season; each round renders as paired-fixture cards with the two-legged
aggregate auto-calculated and the winner highlighted. A tournament bracket
view sits alongside the fixtures list.

Requirements:  pip install customtkinter
Run:           python app.py   (run build_database.py first if the .db is missing)
"""

from __future__ import annotations

import os
import sys

try:
    import customtkinter as ctk
except ImportError:
    ctk = None
    if __name__ == "__main__":
        sys.exit("CustomTkinter is not installed. Run:  pip install customtkinter")

from ui.formatters import (  # noqa: F401  - re-exported for tests/test_ui_helpers.py
    CARD,
    DECISION_TAG,
    DIM,
    HEAD,
    MATCH_SEP,
    NOTE,
    WIN,
    _decider_leg,
    _field,
    aggregate_from_matches,
    compose_tie_detail,
    connect,
    format_attendance,
    format_champion_banner,
    format_match_line,
    format_score_header,
    load_club_name_cache,
    match_extra_fragments,
    missing_database_message,
    tie_aggregate,
    wraplength_for_width,
)
from ui.theme import GOLD, palette
from ui.data import (
    fetch_club_profile,
    fetch_edition_payload,
    final_score_text,
    tie_matches_query,
)
from ui.header import BRACKET_LABEL, FIXTURES_LABEL, HeaderBar
from ui.sidebar import Sidebar
from ui.tie_card import render_tie_card
from ui.bracket_view import BracketView
from ui.club_dialog import ClubProfileDialog

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "european_football.db")


class App(ctk.CTk if ctk is not None else object):
    def __init__(self, db_path=None):
        if ctk is None:
            raise RuntimeError(
                "CustomTkinter is not installed. Run:  pip install customtkinter")
        super().__init__()
        self.title("European Football Database - Classic Era")
        self.geometry("1000x740")
        self.minsize(840, 560)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._db_path = db_path or DB_PATH
        self._colours = palette("dark")
        self._appearance = "dark"
        self._ignore_menu = 0
        self._payload = None
        self._club_names = {}
        self._view = FIXTURES_LABEL
        self._search = ""
        self.conn = None
        self.cur = None
        self.lineages = {}
        self.editions = {}

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if not os.path.exists(self._db_path):
            self._build_missing_db()
            return

        self.conn = connect(self._db_path)
        self.cur = self.conn.cursor()
        self._build_sidebar()
        self._build_main()
        self._load_competitions()

    def _on_close(self):
        try:
            if getattr(self, "cur", None) is not None:
                self.cur.close()
            if getattr(self, "conn", None) is not None:
                self.conn.close()
        finally:
            self.destroy()

    def _build_missing_db(self):
        """In-window setup message; do not sys.exit when the database is absent."""
        msg = missing_database_message(self._db_path)
        hold = ctk.CTkFrame(self, fg_color="transparent")
        hold.grid(row=0, column=0, columnspan=2, rowspan=2, sticky="nsew", padx=40, pady=40)
        ctk.CTkLabel(
            hold, text="Database not found",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            hold, text=msg, justify="left", wraplength=640,
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", pady=(12, 0))

    def _build_sidebar(self):
        self.sidebar = Sidebar(
            self, self._colours,
            on_competition=self._on_competition,
            on_season=self._on_season,
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsw")
        self.competition_menu = self.sidebar.competition_menu
        self.season_menu = self.sidebar.season_menu
        self.champ_label = self.sidebar.champ_label
        self.edition_notes_label = self.sidebar.edition_notes_label

    def _build_main(self):
        self.header = HeaderBar(
            self, self._colours,
            on_search=self._on_search,
            on_view=self._on_view,
            on_appearance=self._on_appearance,
        )
        self.header.grid(row=0, column=1, sticky="ew", padx=24, pady=(16, 8))
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scroll.grid(row=1, column=1, sticky="nsew", padx=16, pady=(0, 16))
        self.scroll.grid_columnconfigure(0, weight=1)
        self.bracket = BracketView(
            self, self._colours, on_club=self._open_club)

    def _load_competitions(self):
        self.lineages = {r["name"]: r["lineage_id"]
                         for r in self.cur.execute(
                             "SELECT lineage_id, name FROM lineage ORDER BY name")}
        names = list(self.lineages) or ["-"]
        self._ignore_menu += 1
        try:
            self.sidebar.set_competitions(names, names[0])
            self._fill_seasons(names[0])
            labels = list(self.editions) or ["-"]
            self.sidebar.set_seasons(labels, labels[-1])
        finally:
            self._ignore_menu -= 1
        self._on_season(labels[-1])

    def _fill_seasons(self, competition_name):
        lid = self.lineages.get(competition_name)
        self.editions = {}
        if lid is not None:
            for r in self.cur.execute(
                    "SELECT edition_id, season_label FROM edition "
                    "WHERE lineage_id=? ORDER BY start_year", (lid,)):
                self.editions[r["season_label"]] = r["edition_id"]

    def _on_competition(self, name):
        if self._ignore_menu:
            return
        self._fill_seasons(name)
        labels = list(self.editions) or ["-"]
        self._ignore_menu += 1
        try:
            self.sidebar.set_seasons(labels, labels[-1])
        finally:
            self._ignore_menu -= 1
        self._on_season(labels[-1])

    def _on_season(self, label):
        if self._ignore_menu:
            return
        eid = self.editions.get(label)
        if eid is not None:
            self._render_edition(eid)

    def _on_search(self, text):
        self._search = text or ""
        self._refresh_view()

    def _on_view(self, value):
        if self._ignore_menu:
            return
        self._view = value or FIXTURES_LABEL
        self._refresh_view()

    def _on_appearance(self, mode):
        self._appearance = "light" if str(mode).lower().startswith("light") else "dark"
        ctk.set_appearance_mode(self._appearance)
        self._colours = palette(self._appearance)
        if getattr(self, "sidebar", None) is not None:
            self.sidebar.apply_palette(self._colours)
        if getattr(self, "header", None) is not None:
            self.header.apply_palette(self._colours)
        if getattr(self, "bracket", None) is not None:
            self.bracket.apply_palette(self._colours)
        self._refresh_view()

    def _render_edition(self, edition_id):
        # Canonical names (test-pinned helper) plus the richer per-edition cache.
        self._club_names = load_club_name_cache(self.cur)
        self._payload = fetch_edition_payload(self.cur, edition_id)
        clubs = self._payload["clubs"]
        for cid, info in clubs.items():
            self._club_names[cid] = info.get("display_name") or info.get("name")

        ed = self._payload["edition"]
        winner_id = ed.get("winner_club_id")
        runner_id = ed.get("runner_up_club_id")
        winner = (clubs.get(winner_id) or {}).get("display_name") if winner_id else None
        runner = (clubs.get(runner_id) or {}).get("display_name") if runner_id else None
        self.sidebar.set_champions(winner, runner, final_score_text(self._payload))
        self.sidebar.set_notes(ed.get("notes") or "")
        self.sidebar.set_stats(
            self._payload["match_count"], self._payload["goal_count"])

        rounds = self._payload["rounds"]
        first_round = rounds[0]["name"] if rounds else ""
        last_round = rounds[-1]["name"] if rounds else ""
        round_span = first_round if first_round == last_round else (
            "%s \u2013 %s" % (first_round, last_round) if first_round else "")
        lineage_name = None
        for name, lid in self.lineages.items():
            if lid == ed.get("lineage_id"):
                lineage_name = name
                break
        self.header.set_breadcrumbs(
            lineage_name or ed.get("competition_name") or "",
            ed.get("season_label") or "",
            round_span,
        )
        self._refresh_view()

    def _refresh_view(self):
        if self._payload is None:
            return
        show_bracket = self._view == BRACKET_LABEL
        if show_bracket:
            self.scroll.grid_remove()
            self.bracket.grid(row=1, column=1, sticky="nsew", padx=16, pady=(0, 16))
            self.bracket.populate(self._payload, self._search)
        else:
            self.bracket.grid_remove()
            self.scroll.grid()
            self._render_fixtures()

    def _render_fixtures(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        payload = self._payload
        clubs = payload["clubs"]
        query = self._search
        r = 0
        for rnd in payload["rounds"]:
            ties = [t for t in (rnd.get("ties") or [])
                    if tie_matches_query(t, clubs, query)]
            if query and not ties:
                continue
            ctk.CTkLabel(
                self.scroll, text=str(rnd["name"]).upper(), anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=self._colours["head"], corner_radius=6, padx=12, pady=6,
            ).grid(row=r, column=0, sticky="ew", pady=(14, 6))
            r += 1
            for tie in ties:
                render_tie_card(
                    self.scroll, tie, clubs, self._colours,
                    on_club=self._open_club, row=r)
                r += 1

    def _open_club(self, club_id):
        if self.cur is None or club_id is None:
            return
        profile = fetch_club_profile(self.cur, club_id)
        ClubProfileDialog(self, profile, self._colours)


if __name__ == "__main__":
    if ctk is None:
        sys.exit("CustomTkinter is not installed. Run:  pip install customtkinter")
    App().mainloop()
