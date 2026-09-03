# -*- coding: utf-8 -*-
"""Standings engine for group stages and Swiss league phases.

Tournament structure is data, not code: points-for-a-win and the ordered
tie-break list live on the edition, so 2-point 1990s groups and 3-point
Swiss league phases share one sorter. Rankings are always derived from
fixtures; they are never stored as a hard-coded table.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# Criteria names stored on edition.standings_tiebreak (comma-separated).
KNOWN_CRITERIA = (
    "points",
    "goal_difference",
    "goals_scored",
    "goals_against",  # lower is better
    "head_to_head",
    "away_goals_scored",
    "wins",
    "away_wins",
    "opponent_points",
    "opponent_goal_difference",
    "opponent_goals_scored",
)

DEFAULT_GROUP_TIEBREAK = "points,goal_difference,goals_scored,head_to_head"
DEFAULT_SWISS_TIEBREAK = (
    "points,goal_difference,goals_scored,away_goals_scored,"
    "wins,away_wins,opponent_points,opponent_goal_difference,opponent_goals_scored"
)


def parse_tiebreak(spec: Optional[str], default: str = DEFAULT_GROUP_TIEBREAK) -> List[str]:
    """Split a stored tie-break string into criterion names."""
    text = (spec or default).strip()
    keys = [k.strip() for k in text.split(",") if k.strip()]
    unknown = [k for k in keys if k not in KNOWN_CRITERIA]
    if unknown:
        raise ValueError("unknown standings criterion: %s" % ", ".join(unknown))
    return keys


def _empty_row(club: str) -> Dict[str, Any]:
    return {
        "club": club,
        "played": 0,
        "w": 0,
        "d": 0,
        "l": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0,
        "pts": 0,
        "away_gf": 0,
        "wins": 0,
        "away_wins": 0,
        "incomplete": 0,
        "awarded": 0,
    }


def _result_points(hs: int, aws: int, points_for_win: int) -> Tuple[int, int]:
    if hs > aws:
        return points_for_win, 0
    if aws > hs:
        return 0, points_for_win
    return 1, 1


def iter_played_matches(matches: Iterable[dict]) -> Iterable[dict]:
    """Yield matches that have both scores (including awarded walkovers)."""
    for m in matches:
        if m.get("hs") is None or m.get("as") is None:
            continue
        yield m


def accumulate(clubs: Sequence[str], matches: Iterable[dict], points_for_win: int,
               only_clubs: Optional[Sequence[str]] = None) -> Dict[str, dict]:
    """Build per-club counting rows from fixtures.

    Unplayed matches (missing scores) increment ``incomplete`` only.
    Awarded/walkover results count as played using the recorded scoreline.
    """
    allow = set(only_clubs) if only_clubs is not None else None
    rows = {c: _empty_row(c) for c in clubs}
    for m in matches:
        home, away = m["home"], m["away"]
        if allow is not None and (home not in allow or away not in allow):
            continue
        for club in (home, away):
            if club not in rows:
                rows[club] = _empty_row(club)
        hs, aws = m.get("hs"), m.get("as")
        if hs is None or aws is None:
            rows[home]["incomplete"] += 1
            rows[away]["incomplete"] += 1
            continue
        hs, aws = int(hs), int(aws)
        hp, ap = _result_points(hs, aws, points_for_win)
        for club, gf, ga, pts, is_away in (
            (home, hs, aws, hp, False),
            (away, aws, hs, ap, True),
        ):
            row = rows[club]
            row["played"] += 1
            row["gf"] += gf
            row["ga"] += ga
            row["pts"] += pts
            if gf > ga:
                row["w"] += 1
                row["wins"] += 1
                if is_away:
                    row["away_wins"] += 1
            elif gf == ga:
                row["d"] += 1
            else:
                row["l"] += 1
            if is_away:
                row["away_gf"] += gf
            if m.get("awarded") or m.get("walkover_winner"):
                row["awarded"] += 1
    for row in rows.values():
        row["gd"] = row["gf"] - row["ga"]
    return rows


def _opponent_strength(rows: Dict[str, dict], matches: Iterable[dict]) -> Dict[str, dict]:
    """Sum opponents' league-phase counting stats (Swiss-model strength of schedule)."""
    played = defaultdict(list)
    for m in iter_played_matches(matches):
        played[m["home"]].append(m["away"])
        played[m["away"]].append(m["home"])
    extra = {}
    for club, row in rows.items():
        opps = played.get(club, [])
        extra[club] = {
            "opponent_points": sum(rows[o]["pts"] for o in opps if o in rows),
            "opponent_goal_difference": sum(rows[o]["gd"] for o in opps if o in rows),
            "opponent_goals_scored": sum(rows[o]["gf"] for o in opps if o in rows),
        }
        row.update(extra[club])
    return extra


def _criterion_value(row: dict, criterion: str) -> Tuple:
    """Sort tuple for one criterion (all higher-is-better except goals_against)."""
    if criterion == "points":
        return (row["pts"],)
    if criterion == "goal_difference":
        return (row["gd"],)
    if criterion == "goals_scored":
        return (row["gf"],)
    if criterion == "goals_against":
        return (-row["ga"],)
    if criterion == "away_goals_scored":
        return (row.get("away_gf", 0),)
    if criterion == "wins":
        return (row.get("wins", row["w"]),)
    if criterion == "away_wins":
        return (row.get("away_wins", 0),)
    if criterion == "opponent_points":
        return (row.get("opponent_points", 0),)
    if criterion == "opponent_goal_difference":
        return (row.get("opponent_goal_difference", 0),)
    if criterion == "opponent_goals_scored":
        return (row.get("opponent_goals_scored", 0),)
    raise ValueError("criterion %r is not a scalar sort key" % criterion)


def _split_equal(group: List[dict], keyfn) -> List[List[dict]]:
    if not group:
        return []
    ordered = sorted(group, key=keyfn, reverse=True)
    buckets: List[List[dict]] = []
    current = [ordered[0]]
    current_key = keyfn(ordered[0])
    for row in ordered[1:]:
        k = keyfn(row)
        if k == current_key:
            current.append(row)
        else:
            buckets.append(current)
            current = [row]
            current_key = k
    buckets.append(current)
    return buckets


def rank_table(clubs: Sequence[str], matches: Sequence[dict], points_for_win: int,
               tiebreak: Optional[str] = None,
               default_tiebreak: str = DEFAULT_GROUP_TIEBREAK) -> List[dict]:
    """Return ranked rows (1-based ``rank``) for a group or league phase.

    ``points_for_win`` must be supplied by the caller (edition flag). This
    function never infers 2 vs 3 from a calendar year.
    """
    if points_for_win not in (2, 3):
        raise ValueError("points_for_win must be 2 or 3, not %r" % (points_for_win,))
    criteria = parse_tiebreak(tiebreak, default_tiebreak)
    rows_map = accumulate(clubs, matches, points_for_win)
    if any(c.startswith("opponent_") for c in criteria):
        _opponent_strength(rows_map, matches)

    def resolve(group: List[dict], remaining: List[str], all_matches: Sequence[dict]) -> List[dict]:
        if len(group) <= 1 or not remaining:
            return sorted(group, key=lambda r: r["club"])
        crit = remaining[0]
        rest = remaining[1:]
        if crit == "head_to_head":
            subset = [r["club"] for r in group]
            mini = accumulate(subset, all_matches, points_for_win, only_clubs=subset)
            # Mini-league uses the remaining criteria (UEFA-style nested ranking).
            mini_rows = [mini[c] for c in subset]
            nested = resolve(mini_rows, rest if rest else ["goal_difference", "goals_scored"], all_matches)
            order = {row["club"]: i for i, row in enumerate(nested)}
            group_sorted = sorted(group, key=lambda r: order[r["club"]])
            # Re-bucket by mini rank so still-tied clubs continue.
            buckets: List[List[dict]] = []
            for row in group_sorted:
                if not buckets or order[row["club"]] != order[buckets[-1][0]["club"]]:
                    buckets.append([row])
                else:
                    buckets[-1].append(row)
            out: List[dict] = []
            for bucket in buckets:
                if len(bucket) == 1:
                    out.extend(bucket)
                else:
                    # Still tied after this H2H pass: fall through remaining
                    # criteria on the ORIGINAL counting rows (not mini).
                    out.extend(resolve(bucket, rest, all_matches))
            return out
        keyfn = lambda r, c=crit: _criterion_value(r, c)
        out = []
        for bucket in _split_equal(group, keyfn):
            if len(bucket) == 1:
                out.extend(bucket)
            else:
                out.extend(resolve(bucket, rest, all_matches))
        return out

    ordered = resolve(list(rows_map.values()), criteria, matches)
    ranked = []
    for i, row in enumerate(ordered, start=1):
        item = dict(row)
        item["rank"] = i
        ranked.append(item)
    return ranked


def tables_match(computed: Sequence[dict], printed: Sequence[dict],
                 fields: Sequence[str] = ("club", "played", "w", "d", "l", "gf", "ga", "pts")) -> List[str]:
    """Return problem strings if a computed table disagrees with a printed one."""
    problems = []
    if len(computed) != len(printed):
        problems.append("table length %d != printed %d" % (len(computed), len(printed)))
        return problems
    for got, exp in zip(computed, printed):
        for field in fields:
            if field not in exp:
                continue
            if got.get(field) != exp.get(field):
                problems.append(
                    "rank %s %s: computed %s=%r, printed %s=%r"
                    % (got.get("rank"), got.get("club"), field, got.get(field), field, exp.get(field))
                )
    return problems
