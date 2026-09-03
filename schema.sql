-- =====================================================================
--  European Football Database — Schema v1.0  ("The Classic Era")
--  Scope: unseeded / seeded two-legged knockouts, 1955 to the mid-1990s
--  rebrands. Group stages and the Swiss league phase are DELIBERATELY
--  ADDITIVE in v2.0 / v3.0 (tables below); never a rewrite of this foundation.
--  never as a rewrite of this foundation.
--
--  Design principle: the STRUCTURE of a tournament is DATA, not code.
--  A round can hold one-leg ties, two-leg ties, replays, byes and
--  shootouts without any change to the tables below.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- lineage: the continuous identity of a trophy across every rename.
-- e.g. European Champion Clubs' Cup -> UEFA Champions League is ONE line.
-- The season-specific name lives on `edition`, so history stays queryable
-- as a single thread while each season still displays its period-correct
-- name. (This is why we do NOT keep a separate aliases table.)
-- ---------------------------------------------------------------------
CREATE TABLE lineage (
    lineage_id  INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,          -- working name of the trophy line
    notes       TEXT
);

-- ---------------------------------------------------------------------
-- club: the canonical registry. One row per club, referenced everywhere.
-- Period-specific club renames (e.g. Vörös Lobogó = MTK Budapest) are
-- noted here for now; a full club-name-history table is a later concern.
-- ---------------------------------------------------------------------
CREATE TABLE club (
    club_id     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,          -- canonical display name
    country     TEXT,                   -- association code, e.g. 'ESP','SCO'
    city        TEXT,
    notes       TEXT
);

-- ---------------------------------------------------------------------
-- edition: one season of one trophy line. Holds the name in use THAT
-- season and the per-season away-goals flag (rule varied by era; the
-- application applies it conditionally rather than hardcoding a year).
-- ---------------------------------------------------------------------
CREATE TABLE edition (
    edition_id        INTEGER PRIMARY KEY,
    lineage_id        INTEGER NOT NULL REFERENCES lineage(lineage_id),
    season_label      TEXT    NOT NULL,          -- '1955-56'
    start_year        INTEGER NOT NULL,          -- 1955
    competition_name  TEXT    NOT NULL,          -- 'European Cup' (period name)
    winner_club_id    INTEGER REFERENCES club(club_id),
    runner_up_club_id INTEGER REFERENCES club(club_id),
    away_goals_active INTEGER NOT NULL DEFAULT 0, -- 0/1 flag for this season
    notes             TEXT,
    points_for_win    INTEGER,   -- 2 or 3; NULL for knockout-only editions
    standings_tiebreak TEXT,     -- comma-separated criteria; NULL if unused
    UNIQUE (lineage_id, start_year)
);

-- ---------------------------------------------------------------------
-- round: a phase within an edition. round_order drives display sorting
-- (1 = earliest qualifier ... N = Final).
-- ---------------------------------------------------------------------
CREATE TABLE round (
    round_id    INTEGER PRIMARY KEY,
    edition_id  INTEGER NOT NULL REFERENCES edition(edition_id),
    name        TEXT    NOT NULL,        -- 'First Round','Quarter-Finals','Final'
    round_order INTEGER NOT NULL,
    phase_type  TEXT    NOT NULL DEFAULT 'knockout', -- knockout | group | league
    UNIQUE (edition_id, round_order)
);

-- ---------------------------------------------------------------------
-- tie: a confrontation between two clubs inside a round. A tie owns its
-- legs (0..n matches). club_a is, by convention, the first-named side /
-- first-leg host. decided_by records HOW it was settled so the UI never
-- has to guess:
--   'aggregate'    two legs, higher aggregate wins
--   'away_goals'   level on aggregate, decided on away goals
--   'replay'       settled by a third match on neutral ground
--   'penalties'    shootout (see *_pens on the deciding match)
--   'coin_toss'    drawing of lots (pre-shootout era)
--   'single_match' one match only (e.g. the Final)
--   'walkover' /   opponent withdrew / advanced without playing
--   'bye'
-- ---------------------------------------------------------------------
CREATE TABLE tie (
    tie_id         INTEGER PRIMARY KEY,
    round_id       INTEGER NOT NULL REFERENCES round(round_id),
    club_a_id      INTEGER NOT NULL REFERENCES club(club_id),
    club_b_id      INTEGER NOT NULL REFERENCES club(club_id),
    winner_club_id INTEGER REFERENCES club(club_id),   -- NULL if unplayed
    decided_by     TEXT,
    notes          TEXT
);

-- ---------------------------------------------------------------------
-- match: an individual leg. Covers legs, replays and one-off finals.
-- Scores are the result as recorded (incl. extra time); a shootout is
-- carried separately in *_pens so the 90'/aet scoreline stays truthful.
-- ---------------------------------------------------------------------
CREATE TABLE match (
    match_id         INTEGER PRIMARY KEY,
    tie_id           INTEGER NOT NULL REFERENCES tie(tie_id),
    leg_number       INTEGER NOT NULL DEFAULT 1,   -- 1, 2, 3(=replay)
    match_date       TEXT,                          -- ISO 'YYYY-MM-DD' or NULL
    home_club_id     INTEGER NOT NULL REFERENCES club(club_id),
    away_club_id     INTEGER NOT NULL REFERENCES club(club_id),
    home_score       INTEGER,
    away_score       INTEGER,
    home_pens        INTEGER,                        -- shootout, NULL if n/a
    away_pens        INTEGER,
    after_extra_time INTEGER NOT NULL DEFAULT 0,     -- 0/1
    venue            TEXT,                           -- ground / relocation note
    attendance       INTEGER,
    referee          TEXT,
    notes            TEXT
);

-- Helpful indexes for the viewer's typical drill-down path.
CREATE INDEX idx_round_edition ON round(edition_id);
CREATE INDEX idx_tie_round     ON tie(round_id);
CREATE INDEX idx_match_tie     ON match(tie_id);

-- ---------------------------------------------------------------------
-- club_name_history: period-accurate club names (e.g. Vörös Lobogó for
-- MTK Budapest in 1955-56). Canonical modern/recognisable names stay on
-- `club`; this table supplies the name of the day per edition/season.
-- ---------------------------------------------------------------------
CREATE TABLE club_name_history (
    history_id   INTEGER PRIMARY KEY,
    club_id      INTEGER NOT NULL REFERENCES club(club_id),
    edition_id   INTEGER REFERENCES edition(edition_id),
    season_label TEXT,
    name_used    TEXT NOT NULL,
    notes        TEXT
);
CREATE INDEX idx_club_name_edition ON club_name_history(club_id, edition_id);


-- ---------------------------------------------------------------------
-- v2.0 / v3.0 additive tables. Knockout tie/match rows are unchanged.
-- A standings phase is linked to a round (phase_type = 'group' or 'league').
-- Rankings are derived from standing_match; they are not stored as a table.
-- ---------------------------------------------------------------------

-- standing_group: one named group (Group A) or a single Swiss league phase.
CREATE TABLE standing_group (
    group_id     INTEGER PRIMARY KEY,
    round_id     INTEGER NOT NULL REFERENCES round(round_id),
    name         TEXT    NOT NULL,        -- 'Group A' / 'League phase'
    group_order  INTEGER NOT NULL,
    UNIQUE (round_id, group_order)
);

-- standing_member: clubs that belong to the group / league phase.
CREATE TABLE standing_member (
    member_id INTEGER PRIMARY KEY,
    group_id  INTEGER NOT NULL REFERENCES standing_group(group_id),
    club_id   INTEGER NOT NULL REFERENCES club(club_id),
    UNIQUE (group_id, club_id)
);

-- standing_match: group / league-phase fixtures. Not a knockout tie.
-- Unplayed matches keep NULL scores (incomplete groups). Awarded/walkover
-- results set awarded=1 and record the scoreline as published (often 3-0).
CREATE TABLE standing_match (
    match_id           INTEGER PRIMARY KEY,
    group_id           INTEGER NOT NULL REFERENCES standing_group(group_id),
    matchday           INTEGER,
    match_date         TEXT,
    home_club_id       INTEGER NOT NULL REFERENCES club(club_id),
    away_club_id       INTEGER NOT NULL REFERENCES club(club_id),
    home_score         INTEGER,
    away_score         INTEGER,
    awarded            INTEGER NOT NULL DEFAULT 0,  -- 0/1 walkover or awarded
    walkover_winner_id INTEGER REFERENCES club(club_id),
    venue              TEXT,
    attendance         INTEGER,
    referee            TEXT,
    notes              TEXT
);

-- competition_transfer: mid-season movement between trophy lines
-- (e.g. a third-placed group club dropping into the UEFA Cup / Europa League).
-- Stored as data so the application never special-cases a calendar year.
CREATE TABLE competition_transfer (
    transfer_id     INTEGER PRIMARY KEY,
    club_id         INTEGER NOT NULL REFERENCES club(club_id),
    from_edition_id INTEGER NOT NULL REFERENCES edition(edition_id),
    from_round_id   INTEGER REFERENCES round(round_id),
    from_rank       INTEGER,
    to_edition_id   INTEGER NOT NULL REFERENCES edition(edition_id),
    to_round_id     INTEGER REFERENCES round(round_id),
    reason          TEXT NOT NULL,        -- e.g. 'group_third', 'league_phase_drop'
    notes           TEXT
);

CREATE INDEX idx_standing_group_round ON standing_group(round_id);
CREATE INDEX idx_standing_member_group ON standing_member(group_id);
CREATE INDEX idx_standing_match_group ON standing_match(group_id);
CREATE INDEX idx_transfer_from ON competition_transfer(from_edition_id);
CREATE INDEX idx_transfer_to ON competition_transfer(to_edition_id);

-- Derived counting view (points still need edition.points_for_win in the app).
-- This is not a ranking: sort order is applied in tools/standings.py.
CREATE VIEW v_standing_results AS
SELECT
    sm.group_id,
    sm.match_id,
    sm.matchday,
    sm.home_club_id,
    sm.away_club_id,
    sm.home_score,
    sm.away_score,
    sm.awarded,
    sm.walkover_winner_id
FROM standing_match sm;
