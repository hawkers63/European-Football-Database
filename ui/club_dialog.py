# -*- coding: utf-8 -*-
"""Club profile modal: canonical name, aliases, record, match history."""

from __future__ import annotations

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from ui.formatters import _field, format_attendance

_Base = ctk.CTkToplevel if ctk is not None else object


class ClubProfileDialog(_Base):
    """Modal inspector for a single club, fed by ui.data.fetch_club_profile."""

    def __init__(self, master, profile, colours, **kwargs):
        if ctk is None:
            raise RuntimeError("CustomTkinter is not installed.")
        super().__init__(master, **kwargs)
        self._colours = colours
        club = profile["club"]
        title_name = club.get("name") or "Club"
        self.title("%s \u2014 club profile" % title_name)
        self.geometry("720x560")
        self.minsize(560, 400)
        try:
            self.transient(master)
        except Exception:
            pass
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._build(profile)
        try:
            self.grab_set()
        except Exception:
            pass
        self.focus()

    def _build(self, profile):
        c = self._colours
        club = profile["club"]
        canonical = club.get("name") or "?"
        country = club.get("country") or "\u2014"
        city = club.get("city") or "\u2014"

        header = ctk.CTkFrame(self, fg_color=c["head"], corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            header, text=canonical,
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(padx=20, pady=(16, 0), anchor="w")
        ctk.CTkLabel(
            header, text="%s  \u00b7  %s" % (country, city),
            text_color=c["dim"], font=ctk.CTkFont(size=13), anchor="w",
        ).pack(padx=20, pady=(0, 12), anchor="w")

        aliases = profile.get("aliases") or []
        if aliases:
            seen = []
            for a in aliases:
                used = a.get("name_used")
                if used and used not in seen and used != canonical:
                    seen.append(used)
            if seen:
                alias_fr = ctk.CTkFrame(self, fg_color="transparent")
                alias_fr.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 0))
                ctk.CTkLabel(
                    alias_fr, text="Also known as",
                    text_color=c["dim"],
                    font=ctk.CTkFont(size=11, weight="bold"),
                ).pack(anchor="w")
                bits = []
                for a in aliases:
                    used = a.get("name_used")
                    if not used:
                        continue
                    season = a.get("season_label") or ""
                    bits.append("%s (%s)" % (used, season) if season else used)
                ctk.CTkLabel(
                    alias_fr, text="  \u00b7  ".join(bits),
                    wraplength=660, justify="left", anchor="w",
                    font=ctk.CTkFont(size=13),
                ).pack(anchor="w")

        rec = ctk.CTkFrame(self, fg_color=c["card"], corner_radius=8)
        rec.grid(row=2, column=0, sticky="ew", padx=20, pady=12)
        stats = (
            ("Ties played", profile.get("ties_played") or 0),
            ("Wins", profile.get("wins") or 0),
            ("Losses", profile.get("losses") or 0),
            ("Titles", profile.get("titles") or 0),
            ("Runner-up", profile.get("runner_up_finishes") or 0),
        )
        for i, (label, value) in enumerate(stats):
            rec.grid_columnconfigure(i, weight=1)
            cell = ctk.CTkFrame(rec, fg_color="transparent")
            cell.grid(row=0, column=i, padx=8, pady=10, sticky="ew")
            ctk.CTkLabel(
                cell, text=str(value),
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=c["gold"] if label in ("Titles", "Wins") else None,
            ).pack()
            ctk.CTkLabel(
                cell, text=label, text_color=c["dim"],
                font=ctk.CTkFont(size=11),
            ).pack()

        history = ctk.CTkScrollableFrame(self, corner_radius=8)
        history.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 16))
        history.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            history, text="Match history",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(4, 6))

        matches = profile.get("matches") or []
        if not matches:
            ctk.CTkLabel(
                history, text="No matches recorded in the loaded database.",
                text_color=c["dim"],
            ).grid(row=1, column=0, sticky="w")
            return
        for i, m in enumerate(matches, start=1):
            self._match_row(history, m, i)

    def _match_row(self, parent, m, row):
        c = self._colours
        fr = ctk.CTkFrame(parent, fg_color=c["card"], corner_radius=6)
        fr.grid(row=row, column=0, sticky="ew", pady=3)
        home = m.get("home_display") or m.get("home_canonical") or "?"
        away = m.get("away_display") or m.get("away_canonical") or "?"
        score = "%s-%s" % (_field(m, "home_score"), _field(m, "away_score"))
        meta = "  \u00b7  ".join(x for x in (
            m.get("competition_name"),
            m.get("season_label"),
            m.get("round_name"),
            _field(m, "match_date"),
            _field(m, "venue"),
            format_attendance(_field(m, "attendance")),
        ) if x)
        ctk.CTkLabel(
            fr, text="%s  %s  %s" % (home, score, away),
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).pack(padx=10, pady=(6, 0), anchor="w")
        if meta:
            ctk.CTkLabel(
                fr, text=meta, text_color=c["dim"],
                font=ctk.CTkFont(size=11), anchor="w", wraplength=640,
            ).pack(padx=10, pady=(0, 6), anchor="w")
