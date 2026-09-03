# -*- coding: utf-8 -*-
"""Top navigation: breadcrumbs, search, view switcher, appearance toggle."""

from __future__ import annotations

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

_Base = ctk.CTkFrame if ctk is not None else object

FIXTURES_LABEL = "Fixtures List"
BRACKET_LABEL = "Tournament Bracket"
VIEW_CHOICES = (FIXTURES_LABEL, BRACKET_LABEL)


class HeaderBar(_Base):
    """Breadcrumbs, search, Fixtures/Bracket switch, Dark/Light toggle."""

    def __init__(self, master, colours, on_search, on_view, on_appearance, **kwargs):
        if ctk is None:
            raise RuntimeError("CustomTkinter is not installed.")
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self._colours = colours
        self._on_search = on_search
        self._on_view = on_view
        self._on_appearance = on_appearance
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        c = self._colours
        self.crumbs = ctk.CTkLabel(
            self, text="", anchor="w",
            font=ctk.CTkFont(size=18, weight="bold"))
        self.crumbs.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        tools = ctk.CTkFrame(self, fg_color="transparent")
        tools.grid(row=0, column=1, sticky="e")

        self.search_var = ctk.StringVar(value="")
        self.search = ctk.CTkEntry(
            tools, width=200, placeholder_text="Search clubs or ties\u2026",
            textvariable=self.search_var)
        self.search.pack(side="left", padx=(0, 8))
        self.search.bind("<KeyRelease>", self._search_event)

        self.view_switch = ctk.CTkSegmentedButton(
            tools, values=list(VIEW_CHOICES),
            font=ctk.CTkFont(size=12))
        self.view_switch.set(FIXTURES_LABEL)
        self.view_switch.configure(command=self._on_view)
        self.view_switch.pack(side="left", padx=(0, 8))

        self.mode_switch = ctk.CTkSwitch(
            tools, text="Light mode", command=self._toggle_appearance,
            font=ctk.CTkFont(size=12))
        self.mode_switch.pack(side="left")

        # Row 1: quieter breadcrumb trail (Lineage > Season > Round).
        self.trail = ctk.CTkLabel(
            self, text="", anchor="w", text_color=c["dim"],
            font=ctk.CTkFont(size=12))
        self.trail.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

    def _search_event(self, _event=None):
        if self._on_search is not None:
            self._on_search(self.search_var.get())

    def _toggle_appearance(self):
        mode = "light" if self.mode_switch.get() else "dark"
        if self._on_appearance is not None:
            self._on_appearance(mode)

    def apply_palette(self, colours):
        self._colours = colours
        self.trail.configure(text_color=colours["dim"])

    def set_breadcrumbs(self, lineage, season, round_name=""):
        title = "  ".join(p for p in (lineage, season) if p)
        self.crumbs.configure(text=title)
        bits = [p for p in (lineage, season, round_name) if p]
        self.trail.configure(text="  \u203a  ".join(bits))

    def current_view(self) -> str:
        try:
            return self.view_switch.get() or FIXTURES_LABEL
        except Exception:
            return FIXTURES_LABEL

    def search_text(self) -> str:
        return self.search_var.get()
