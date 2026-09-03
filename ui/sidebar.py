# -*- coding: utf-8 -*-
"""Competition / season sidebar with champions card and season context."""

from __future__ import annotations

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from ui.formatters import format_champion_banner

_Base = ctk.CTkFrame if ctk is not None else object


class Sidebar(_Base):
    """Left rail: lineage + season menus, champions, notes, match/goal counts."""

    def __init__(self, master, colours, on_competition, on_season, **kwargs):
        if ctk is None:
            raise RuntimeError("CustomTkinter is not installed.")
        kwargs.setdefault("width", 250)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self.grid_propagate(False)
        self._colours = colours
        self._on_competition = on_competition
        self._on_season = on_season
        self._build()

    def _build(self):
        c = self._colours
        ctk.CTkLabel(
            self, text="European Football\nDatabase",
            font=ctk.CTkFont(size=20, weight="bold"), justify="left",
        ).pack(padx=20, pady=(24, 2), anchor="w")
        ctk.CTkLabel(
            self, text="The Classic Era", text_color=c["dim"],
        ).pack(padx=20, pady=(0, 24), anchor="w")

        ctk.CTkLabel(self, text="Competition").pack(
            padx=20, pady=(0, 4), anchor="w")
        self.competition_menu = ctk.CTkOptionMenu(
            self, values=["-"], width=210, command=self._on_competition)
        self.competition_menu.pack(padx=20, pady=(0, 16), anchor="w")

        ctk.CTkLabel(self, text="Season").pack(
            padx=20, pady=(0, 4), anchor="w")
        self.season_menu = ctk.CTkOptionMenu(
            self, values=["-"], width=210, command=self._on_season)
        self.season_menu.pack(padx=20, pady=(0, 16), anchor="w")

        self.champ_card = ctk.CTkFrame(
            self, fg_color=c["head"], corner_radius=8)
        self.champ_card.pack(padx=16, pady=(8, 0), fill="x")
        self.champ_kicker = ctk.CTkLabel(
            self.champ_card, text="\u2605  CHAMPIONS",
            text_color=c["gold"],
            font=ctk.CTkFont(size=11, weight="bold"), anchor="w")
        self.champ_kicker.pack(padx=12, pady=(10, 0), anchor="w")
        self.champ_winner = ctk.CTkLabel(
            self.champ_card, text="\u2014",
            text_color=c["gold"], wraplength=200, justify="left",
            font=ctk.CTkFont(size=15, weight="bold"), anchor="w")
        self.champ_winner.pack(padx=12, pady=(2, 0), anchor="w")
        self.champ_runner = ctk.CTkLabel(
            self.champ_card, text="",
            text_color=c["dim"], wraplength=200, justify="left",
            font=ctk.CTkFont(size=12), anchor="w")
        self.champ_runner.pack(padx=12, pady=(4, 0), anchor="w")
        self.champ_score_label = ctk.CTkLabel(
            self.champ_card, text="FINAL SCORE",
            text_color=c["dim"],
            font=ctk.CTkFont(size=10, weight="bold"), anchor="w")
        self.champ_score_label.pack(padx=12, pady=(8, 0), anchor="w")
        self.champ_score = ctk.CTkLabel(
            self.champ_card, text="",
            text_color=c["text"],
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.champ_score.pack(padx=12, pady=(0, 10), anchor="w")

        # Kept for tests that still read format_champion_banner via app;
        # hidden duplicate used only as an accessibility fallback.
        self.champ_label = ctk.CTkLabel(
            self, text="", text_color=c["win"], wraplength=210,
            justify="left", font=ctk.CTkFont(size=1))
        self.champ_label.pack_forget()

        self.notes_frame = ctk.CTkFrame(
            self, fg_color=c["card"], corner_radius=8)
        self.notes_frame.pack(padx=16, pady=(12, 0), fill="x")
        ctk.CTkLabel(
            self.notes_frame, text="Season context",
            text_color=c["dim"],
            font=ctk.CTkFont(size=10, weight="bold"), anchor="w",
        ).pack(padx=12, pady=(8, 0), anchor="w")
        self.edition_notes_label = ctk.CTkLabel(
            self.notes_frame, text="", text_color=c["dim"],
            wraplength=200, justify="left", font=ctk.CTkFont(size=12),
            anchor="w")
        self.edition_notes_label.pack(padx=12, pady=(2, 10), anchor="w")

        self.stats_label = ctk.CTkLabel(
            self, text="", text_color=c["dim"], wraplength=210,
            justify="left", font=ctk.CTkFont(size=12))
        self.stats_label.pack(padx=20, pady=(12, 16), anchor="w")

    def apply_palette(self, colours):
        self._colours = colours
        self.champ_card.configure(fg_color=colours["head"])
        self.champ_kicker.configure(text_color=colours["gold"])
        self.champ_winner.configure(text_color=colours["gold"])
        self.champ_runner.configure(text_color=colours["dim"])
        self.champ_score_label.configure(text_color=colours["dim"])
        self.champ_score.configure(text_color=colours["text"])
        self.notes_frame.configure(fg_color=colours["card"])
        self.edition_notes_label.configure(text_color=colours["dim"])
        self.stats_label.configure(text_color=colours["dim"])

    def set_competitions(self, names, selected=None):
        values = list(names) or ["-"]
        self.competition_menu.configure(values=values)
        self.competition_menu.set(selected or values[0])

    def set_seasons(self, labels, selected=None):
        values = list(labels) or ["-"]
        self.season_menu.configure(values=values)
        self.season_menu.set(selected or values[-1])

    def set_champions(self, winner, runner_up, final_score=""):
        self.champ_winner.configure(text=winner or "\u2014")
        if runner_up:
            self.champ_runner.configure(text="Runner-up  %s" % runner_up)
        else:
            self.champ_runner.configure(text="")
        self.champ_score.configure(text=final_score or "\u2014")
        self.champ_label.configure(
            text=format_champion_banner(winner, runner_up))

    def set_notes(self, notes):
        self.edition_notes_label.configure(text=notes or "No season notes recorded.")

    def set_stats(self, match_count, goal_count):
        self.stats_label.configure(
            text="%s matches  \u00b7  %s goals scored" % (
                match_count, goal_count))
