"""Data schema definitions for the ESPN Fantasy Predictor pipeline.

Each table below is defined as a dict of column name -> pandas dtype string.
These are the contract that `data_loader.py` validates incoming data against,
regardless of whether it eventually comes from a manual CSV export, the
nflverse loader (`nflverse_loader.py`), or the `espn_api` package later.

`player_id` is a string (nflverse's GSIS ID, e.g. "00-0023459") rather than an
int, since that's the join key the real historical data source (nflverse) uses.
"""

# One row per player (season-independent identity/metadata).
PLAYERS_SCHEMA = {
    "player_id": "object",
    "name": "object",
    "position": "object",  # QB, RB, WR, TE, K, DST
    "team": "object",  # NFL team abbreviation
    "bye_week": "int64",
}

# One row per player per week per season.
WEEKLY_STATS_SCHEMA = {
    "player_id": "object",
    "season": "int64",
    "week": "int64",
    "pass_yds": "float64",
    "pass_td": "float64",
    "pass_int": "float64",
    "rush_yds": "float64",
    "rush_td": "float64",
    "receptions": "float64",
    "rec_yds": "float64",
    "rec_td": "float64",
    "special_teams_td": "float64",  # kick/punt return TD
    "fumbles_lost": "float64",
    "two_pt_conversions": "float64",
}

# One row per player per season (aggregated from weekly_stats).
SEASON_TOTALS_SCHEMA = {
    "player_id": "object",
    "season": "int64",
    "games_played": "int64",
    "total_fantasy_points": "float64",
}

# One row per player per season, average draft position from mock/real drafts.
DRAFT_ADP_SCHEMA = {
    "player_id": "object",
    "season": "int64",
    "adp": "float64",
    "adp_position_rank": "int64",
}

# Full PPR scoring weights, keyed to the stat columns in WEEKLY_STATS_SCHEMA.
# Confirmed (2026-07-13) against ESPN's own published default offensive scoring
# (support.espn.com "Scoring Settings" / games.espn.com scoring master list), and
# re-confirmed (2026-08-16) against the user's real league (id 2091358422, "Vicious
# Victories", 2025 season) via a live espn_api pull — every offensive value below
# matches the real league exactly, so this one was already correct as a default.
FULL_PPR_SCORING = {
    "pass_yds": 0.04,  # 1 pt per 25 yds
    "pass_td": 4.0,
    "pass_int": -2.0,
    "rush_yds": 0.1,  # 1 pt per 10 yds
    "rush_td": 6.0,
    "receptions": 1.0,  # the "PPR" in Full PPR
    "rec_yds": 0.1,  # 1 pt per 10 yds
    "rec_td": 6.0,
    "special_teams_td": 6.0,  # kick/punt return TD
    "fumbles_lost": -2.0,
    "two_pt_conversions": 2.0,
}

# Kicker scoring. Corrected 2026-08-16 against the user's real league (id
# 2091358422, "Vicious Victories", 2025 season) via a live espn_api pull — the
# generic "ESPN default" values from 2026-07-13 were wrong in two ways for this
# league: (1) 50+ yard FGs aren't one flat tier, the league splits 50-59 from
# 60+ with 60+ worth an extra point; (2) missed PATs cost nothing here (0, not
# -1 — espn_api only returns non-zero scoring entries, and no "PAT missed"
# entry was present). Not yet wired into WEEKLY_STATS_SCHEMA/data_loader.py
# (kicker stats are a different shape — FG makes by distance bucket, not
# yards/TDs) — add a dedicated kicker table when Step 3+ needs to project K
# scoring.
KICKER_SCORING = {
    "pat_made": 1.0,
    "pat_missed": 0.0,
    "fg_made_0_39": 3.0,
    "fg_made_40_49": 4.0,
    "fg_made_50_59": 5.0,
    "fg_made_60_plus": 6.0,
    "fg_missed": -1.0,
}

# Team Defense/Special Teams scoring. Corrected 2026-08-16 against the user's
# real league (id 2091358422, "Vicious Victories", 2025 season) via a live
# espn_api pull — this was the scoring category most likely to be customized
# (per the original 2026-07-13 note), and it was: the real league scores every
# defensive TD type (INT return, fumble return, kick/punt return, blocked-kick
# return) as a flat 6, not the split 3/3/4 values guessed from a generic ESPN
# scoring master list. The points-allowed tiers also use different (smaller)
# magnitudes than the old defaults, and the real league scores a *second*,
# separate tier ladder on total yards allowed that wasn't tracked here at all.
# Two categories the live pull returned that aren't modeled below because
# their exact mechanic is unclear from the API alone (not guessed/fabricated):
# "1PSF" (1pt Safety, 1.0) alongside the flat "safety" (2.0) — possibly a
# distinct bonus condition; "FTD" (Fumble Recovered for TD, 6.0) alongside
# "fumble_return_td" (6.0) — possibly a distinct recovery-vs-return case. Both
# worth asking the commissioner about, or re-deriving once real DST box scores
# are available to see which field actually fires. Still not wired into a data
# table — DST stats are team-level (sacks, turnovers forced, points/yards
# allowed), not player-level, so this needs its own table, not
# WEEKLY_STATS_SCHEMA.
DST_SCORING = {
    "sack": 1.0,
    "interception": 2.0,
    "fumble_recovery": 2.0,
    "safety": 2.0,
    "blocked_kick": 2.0,  # blocked punt, FG, or PAT
    "interception_return_td": 6.0,
    "fumble_return_td": 6.0,
    "kickoff_return_td": 6.0,
    "punt_return_td": 6.0,
    "blocked_kick_return_td": 6.0,
    "two_pt_return": 2.0,  # defensive/ST return of an opponent's failed 2pt try
    # Points allowed -> fantasy points. Gaps (18-21, 22-27) are real: this
    # league scores those tiers at 0, same convention as the yards-allowed
    # ladder below.
    "points_allowed_tiers": {
        0: 5,
        (1, 6): 4,
        (7, 13): 3,
        (14, 17): 1,
        (18, 21): 0,
        (22, 27): 0,
        (28, 34): -1,
        (35, 45): -3,
        46: -5,  # 46+
    },
    # Total yards allowed -> fantasy points. Not present in the old generic
    # defaults at all; this league scores it as its own ladder alongside
    # points allowed. The 300-349 gap is real (unlisted by the API => 0).
    "total_yards_allowed_tiers": {
        (0, 99): 5,
        (100, 199): 3,
        (200, 299): 2,
        (300, 349): 0,
        (350, 399): -1,
        (400, 449): -3,
        (450, 499): -5,
        (500, 549): -6,
        550: -7,  # 550+
    },
}

# League roster/bench settings. Confirmed 2026-08-16 against the user's real
# league (id 2091358422, "Vicious Victories", 2025 season) via a live espn_api
# pull — the roster slot shape (1 QB/2 RB/2 WR/1 TE/1 FLEX/1 K/1 DST) matched
# the prior placeholder, but bench size was wrong (7, not 6) and an IR slot
# exists that wasn't modeled at all. 12 teams, 14-week regular season, 8-team
# playoff bracket (not part of roster/scoring, but relevant to Step 4's draft
# simulator and Step 5's backtest scorer later). Scoring is Full PPR
# (KICKER_SCORING and DST_SCORING aren't included here yet since neither has a
# data table to back it).
LEAGUE_SETTINGS = {
    "roster_slots": {
        "QB": 1,
        "RB": 2,
        "WR": 2,
        "TE": 1,
        "FLEX": 1,  # RB/WR/TE
        "K": 1,
        "DST": 1,
        "IR": 1,
    },
    "bench_size": 7,
    "team_count": 12,
    "reg_season_weeks": 14,
    "playoff_team_count": 8,
    "scoring": FULL_PPR_SCORING,
}
