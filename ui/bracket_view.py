# -*- coding: utf-8 -*-
"""Knockout bracket canvas: columns by round_order, connectors, inspector."""

from __future__ import annotations

import tkinter as tk

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from ui.data import layout_bracket_positions, organise_bracket_columns
from ui.formatters import (
    DECISION_TAG,
    _field,
    format_attendance,
    format_score_header,
)
from ui.tie_card import club_label

_Base = ctk.CTkFrame if ctk is not None else object

COL_W = 210
NODE_W = 180
NODE_H = 58


class BracketView(_Base):
    """Multi-column knockout tree with a legs inspector under the canvas."""

    def __init__(self, master, colours, on_club=None, **kwargs):
        if ctk is None:
            raise RuntimeError("CustomTkinter is not installed.")
        super().__init__(master, **kwargs)
        self._colours = colours
        self._on_club = on_club
        self._clubs = {}
        self._columns = []
        self._payload = None
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        canvas_hold = ctk.CTkFrame(self, fg_color="transparent")
        canvas_hold.grid(row=0, column=0, sticky="nsew")
        canvas_hold.grid_rowconfigure(0, weight=1)
        canvas_hold.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_hold, highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar = ctk.CTkScrollbar(
            canvas_hold, orientation="vertical", command=self.canvas.yview)
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar = ctk.CTkScrollbar(
            canvas_hold, orientation="horizontal", command=self.canvas.xview)
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(
            yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", lambda _e: self._paint())

        self.inspector = ctk.CTkFrame(self, corner_radius=8)
        self.inspector.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.inspector_title = ctk.CTkLabel(
            self.inspector, text="Select a tie to inspect its legs.",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        self.inspector_title.pack(padx=12, pady=(8, 2), anchor="w")
        self.inspector_body = ctk.CTkLabel(
            self.inspector, text="", justify="left", anchor="w",
            wraplength=720, font=ctk.CTkFont(size=12))
        self.inspector_body.pack(padx=12, pady=(0, 10), anchor="w")

    def apply_palette(self, colours):
        self._colours = colours
        self._paint()

    def populate(self, payload, query=""):
        self._payload = payload
        self._clubs = (payload or {}).get("clubs") or {}
        rounds = list((payload or {}).get("rounds") or [])
        if query:
            filtered = []
            from ui.data import tie_matches_query
            for rnd in rounds:
                ties = [t for t in (rnd.get("ties") or [])
                        if tie_matches_query(t, self._clubs, query)]
                clone = dict(rnd)
                clone["ties"] = ties or list(rnd.get("ties") or [])
                filtered.append(clone)
            # Keep full tree when a search is active so connectors still
            # make sense; matching nodes are highlighted in _paint.
            self._query = query
            self._columns = organise_bracket_columns(rounds)
        else:
            self._query = ""
            self._columns = organise_bracket_columns(rounds)
        self._paint()
        self.inspector_title.configure(text="Select a tie to inspect its legs.")
        self.inspector_body.configure(text="")

    def _paint(self):
        c = self._colours
        self.canvas.delete("all")
        self.canvas.configure(bg=c["canvas"])
        columns = self._columns
        if not columns:
            self.canvas.create_text(
                24, 24, anchor="nw", fill=c["dim"],
                text="No knockout rounds to display.", font=("Segoe UI", 12))
            return

        ys = layout_bracket_positions(columns, slot_h=NODE_H + 14, top=40)
        self._hit = []  # (x0,y0,x1,y1,tie)
        query = (getattr(self, "_query", "") or "").casefold()

        for ci, col in enumerate(columns):
            x = 20 + ci * COL_W
            self.canvas.create_text(
                x + NODE_W / 2, 16, text=str(col.get("name") or "").upper(),
                fill=c["gold"], font=("Segoe UI", 10, "bold"))
            for si, slot in enumerate(col.get("slots") or []):
                y = ys[ci][si] if si < len(ys[ci]) else 40 + si * (NODE_H + 14)
                tie = slot.get("tie")
                self._draw_node(x, y, tie, query)
                feeders = slot.get("feeders") or []
                if ci > 0:
                    prev_ys = ys[ci - 1]
                    x0 = 20 + (ci - 1) * COL_W + NODE_W
                    x1 = x
                    mid = (x0 + x1) / 2
                    for fi in feeders:
                        if fi is None or fi >= len(prev_ys):
                            continue
                        y0 = prev_ys[fi] + NODE_H / 2
                        y1 = y + NODE_H / 2
                        self.canvas.create_line(
                            x0, y0, mid, y0, mid, y1, x1, y1,
                            fill=c["border"], width=2)

        max_x = 40 + len(columns) * COL_W
        max_y = 80
        for col_ys in ys:
            if col_ys:
                max_y = max(max_y, max(col_ys) + NODE_H + 40)
        self.canvas.configure(scrollregion=(0, 0, max_x, max_y))

    def _draw_node(self, x, y, tie, query):
        c = self._colours
        if tie is None:
            return
        a_name, a_cc = club_label(self._clubs, tie.get("club_a_id"))
        b_name, b_cc = club_label(self._clubs, tie.get("club_b_id"))
        legs = tie.get("matches") or []
        ga, gb = tie.get("aggregate") or (0, 0)
        score = format_score_header(ga, gb, tie.get("decided_by"), legs)
        blob = " ".join((a_name, b_name, a_cc, b_cc)).casefold()
        match = (not query) or (query in blob)
        fill = c["node"] if match else c["head"]
        outline = c["gold"] if match and query else c["border"]
        self.canvas.create_rectangle(
            x, y, x + NODE_W, y + NODE_H,
            fill=fill, outline=outline, width=2, tags=("node",))
        winner = tie.get("winner_club_id")
        a_fill = c["win"] if winner == tie.get("club_a_id") else c["text"]
        b_fill = c["win"] if winner == tie.get("club_b_id") else c["text"]
        a_txt = a_name if not a_cc else "%s  [%s]" % (a_name, a_cc)
        b_txt = b_name if not b_cc else "%s  [%s]" % (b_name, b_cc)
        self.canvas.create_text(
            x + 8, y + 12, anchor="w", fill=a_fill,
            text=_fit(a_txt, 26), font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(
            x + 8, y + 30, anchor="w", fill=b_fill,
            text=_fit(b_txt, 26), font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(
            x + NODE_W - 8, y + NODE_H / 2, anchor="e", fill=c["gold"],
            text=score, font=("Segoe UI", 10, "bold"))
        self._hit.append((x, y, x + NODE_W, y + NODE_H, tie))

    def _on_canvas_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for x0, y0, x1, y1, tie in reversed(getattr(self, "_hit", [])):
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._show_inspector(tie)
                a_id = tie.get("club_a_id")
                # Second click on the name half could open the club; keep
                # the inspector as the primary action for the node.
                return

    def _show_inspector(self, tie):
        clubs = self._clubs
        a_name, a_cc = club_label(clubs, tie.get("club_a_id"))
        b_name, b_cc = club_label(clubs, tie.get("club_b_id"))
        legs = tie.get("matches") or []
        ga, gb = tie.get("aggregate") or (0, 0)
        score = format_score_header(ga, gb, tie.get("decided_by"), legs)
        tag = DECISION_TAG.get(tie.get("decided_by") or "", "")
        title = "%s [%s]  %s  %s [%s]" % (
            a_name, a_cc or "\u2014", score, b_name, b_cc or "\u2014")
        if tag:
            title += "  \u00b7  %s" % tag
        lines = []
        if not legs:
            lines.append("No legs recorded (walkover or bye).")
        for m in legs:
            hn, _ = club_label(clubs, m.get("home_club_id"))
            an, _ = club_label(clubs, m.get("away_club_id"))
            bits = ["Leg %s  %s %s-%s %s" % (
                _field(m, "leg_number") or "?",
                hn, _field(m, "home_score"), _field(m, "away_score"), an)]
            if _field(m, "after_extra_time"):
                bits.append("aet")
            hp, ap = _field(m, "home_pens"), _field(m, "away_pens")
            if hp is not None and ap is not None:
                bits.append("pens %s-%s" % (hp, ap))
            extras = [x for x in (
                _field(m, "match_date"),
                _field(m, "venue"),
                format_attendance(_field(m, "attendance")),
                ("ref %s" % _field(m, "referee")) if _field(m, "referee") else None,
            ) if x]
            line = "  \u00b7  ".join(bits)
            if extras:
                line += "\n    " + "  \u00b7  ".join(extras)
            lines.append(line)
        notes = tie.get("notes") or ""
        if notes:
            lines.append("\u2139  %s" % notes)
        self.inspector_title.configure(text=title)
        self.inspector_body.configure(text="\n".join(lines) or "")
        self._inspected = tie


def _fit(text, n):
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "\u2026"
