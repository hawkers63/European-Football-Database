# -*- coding: utf-8 -*-
"""Rich fixture / tie cards with country pills, score pill and notes callout."""

from __future__ import annotations

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from ui.formatters import (
    DECISION_TAG,
    _field,
    compose_tie_detail,
    format_attendance,
    format_match_line,
    format_score_header,
    wraplength_for_width,
)


def club_label(clubs, club_id) -> tuple[str, str]:
    """Return (display_name, country_code) for a club_id."""
    info = (clubs or {}).get(club_id) or {}
    name = info.get("display_name") or info.get("name") or "?"
    country = info.get("country") or ""
    return name, country


def attach_dynamic_wrap(card, *labels, padding=28):
    """Write-gated wraplength updates on <Configure> (avoids layout thrash)."""

    def _on_configure(event, widget=card, lbls=labels, pad=padding):
        if event.widget is not widget:
            return
        wrap = wraplength_for_width(event.width, padding=pad)
        for lbl in lbls:
            try:
                current = int(lbl.cget("wraplength") or 0)
            except Exception:
                current = 0
            if current != wrap:
                lbl.configure(wraplength=wrap)

    card.bind("<Configure>", _on_configure)


def _bind_club_click(widget, club_id, on_club):
    if on_club is None or club_id is None:
        return
    widget.configure(cursor="hand2")
    widget.bind("<Button-1>", lambda _e, cid=club_id: on_club(cid))


def _pill(parent, text, fg, text_color, font_size=11):
    if ctk is None:
        return None
    frame = ctk.CTkFrame(parent, fg_color=fg, corner_radius=8)
    ctk.CTkLabel(
        frame, text=text, text_color=text_color,
        font=ctk.CTkFont(size=font_size, weight="bold"),
        padx=6, pady=1,
    ).pack()
    return frame


def render_tie_card(parent, tie, clubs, colours, on_club=None, row=0):
    """Build a rich fixture card. Returns the card frame."""
    if ctk is None:
        raise RuntimeError("CustomTkinter is not installed.")

    card = ctk.CTkFrame(parent, fg_color=colours["card"], corner_radius=8)
    card.grid(row=row, column=0, sticky="ew", pady=4)
    card.grid_columnconfigure(0, weight=1)

    a_id, b_id = tie["club_a_id"], tie["club_b_id"]
    a_name, a_cc = club_label(clubs, a_id)
    b_name, b_cc = club_label(clubs, b_id)
    winner = tie.get("winner_club_id")
    a_col = colours["win"] if winner == a_id else colours["text"]
    b_col = colours["win"] if winner == b_id else colours["text"]

    legs = list(tie.get("matches") or [])
    ga, gb = tie.get("aggregate") if tie.get("aggregate") is not None else (0, 0)
    score = format_score_header(ga, gb, tie.get("decided_by"), legs)
    tag = DECISION_TAG.get(tie.get("decided_by") or "", "")

    header = ctk.CTkFrame(card, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
    header.grid_columnconfigure(0, weight=1)
    header.grid_columnconfigure(2, weight=1)

    left = ctk.CTkFrame(header, fg_color="transparent")
    left.grid(row=0, column=0, sticky="e")
    a_lbl = ctk.CTkLabel(
        left, text=a_name, anchor="e", text_color=a_col,
        font=ctk.CTkFont(size=15, weight="bold"))
    a_lbl.pack(side="left")
    _bind_club_click(a_lbl, a_id, on_club)
    if a_cc:
        _pill(left, a_cc, colours["pill"], colours["dim"]).pack(
            side="left", padx=(8, 0))

    score_wrap = ctk.CTkFrame(
        header, fg_color=colours["score_pill"], corner_radius=8)
    score_wrap.grid(row=0, column=1, padx=10)
    ctk.CTkLabel(
        score_wrap, text=score,
        font=ctk.CTkFont(size=15, weight="bold"),
        padx=10, pady=4,
    ).pack()
    if tag:
        ctk.CTkLabel(
            score_wrap, text=tag.upper(),
            text_color=colours["gold"],
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(pady=(0, 4))

    right = ctk.CTkFrame(header, fg_color="transparent")
    right.grid(row=0, column=2, sticky="w")
    if b_cc:
        _pill(right, b_cc, colours["pill"], colours["dim"]).pack(
            side="left", padx=(0, 8))
    b_lbl = ctk.CTkLabel(
        right, text=b_name, anchor="w", text_color=b_col,
        font=ctk.CTkFont(size=15, weight="bold"))
    b_lbl.pack(side="left")
    _bind_club_click(b_lbl, b_id, on_club)

    wrap_labels = []
    body_row = 1
    for m in legs:
        body_row = _render_leg(card, m, clubs, colours, on_club, body_row)

    parts = []
    for m in legs:
        hn, _ = club_label(clubs, m.get("home_club_id"))
        an, _ = club_label(clubs, m.get("away_club_id"))
        parts.append(format_match_line(hn, an, m))
    _match_detail, notes_callout = compose_tie_detail(parts, tie.get("notes"))

    if notes_callout:
        callout = ctk.CTkFrame(
            card, fg_color=colours["callout_bg"], corner_radius=6)
        callout.grid(row=body_row, column=0, sticky="ew", padx=12, pady=(4, 10))
        # Info icon rather than italic fonts (CTk italic silently fails).
        note_lbl = ctk.CTkLabel(
            callout, text="\u2139  %s" % notes_callout,
            text_color=colours["note"], justify="left", anchor="w",
            font=ctk.CTkFont(size=12), wraplength=680)
        note_lbl.pack(padx=10, pady=8, anchor="w", fill="x")
        wrap_labels.append(note_lbl)
        body_row += 1
    else:
        spacer = ctk.CTkFrame(card, fg_color="transparent", height=6)
        spacer.grid(row=body_row, column=0, sticky="ew")

    if wrap_labels:
        attach_dynamic_wrap(card, *wrap_labels)
    return card


def _render_leg(card, m, clubs, colours, on_club, row):
    row_fr = ctk.CTkFrame(card, fg_color="transparent")
    row_fr.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 4))

    hn, _ = club_label(clubs, m.get("home_club_id"))
    an, _ = club_label(clubs, m.get("away_club_id"))
    hs = _field(m, "home_score")
    aws = _field(m, "away_score")
    ln = _field(m, "leg_number")
    prefix = "Leg %s" % ln if ln is not None else "Match"

    line = ctk.CTkFrame(row_fr, fg_color="transparent")
    line.pack(anchor="w", fill="x")
    ctk.CTkLabel(
        line, text=prefix, text_color=colours["dim"],
        font=ctk.CTkFont(size=11, weight="bold"), width=52, anchor="w",
    ).pack(side="left")

    home_lbl = ctk.CTkLabel(
        line, text=hn, font=ctk.CTkFont(size=12), anchor="w")
    home_lbl.pack(side="left", padx=(4, 4))
    _bind_club_click(home_lbl, m.get("home_club_id"), on_club)

    ctk.CTkLabel(
        line, text="%s-%s" % (hs, aws),
        font=ctk.CTkFont(size=12, weight="bold"),
    ).pack(side="left", padx=4)

    away_lbl = ctk.CTkLabel(
        line, text=an, font=ctk.CTkFont(size=12), anchor="w")
    away_lbl.pack(side="left", padx=(4, 8))
    _bind_club_click(away_lbl, m.get("away_club_id"), on_club)

    if _field(m, "after_extra_time"):
        _pill(line, "aet", colours["pill"], colours["text"], 10).pack(
            side="left", padx=3)
    hp = _field(m, "home_pens")
    ap = _field(m, "away_pens")
    if hp is not None and ap is not None:
        _pill(line, "pens %s-%s" % (hp, ap), colours["pill"],
              colours["gold"], 10).pack(side="left", padx=3)

    badges = []
    date = _field(m, "match_date")
    if date:
        badges.append(date)
    venue = _field(m, "venue")
    if venue:
        badges.append(venue)
    att = format_attendance(_field(m, "attendance"))
    if att:
        badges.append(att)
    referee = _field(m, "referee")
    if referee:
        badges.append("ref %s" % referee)
    if badges:
        meta = ctk.CTkLabel(
            row_fr, text="   \u00b7   ".join(badges),
            text_color=colours["dim"], font=ctk.CTkFont(size=11),
            anchor="w", wraplength=640)
        meta.pack(anchor="w", padx=(56, 0))
        attach_dynamic_wrap(card, meta, padding=80)
    return row + 1
