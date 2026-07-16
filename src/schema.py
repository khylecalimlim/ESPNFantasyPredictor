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
# (support.espn.com "Scoring Settings" / games.espn.com scoring master list) —
# these are ESPN's actual defaults, not a generic approximation. Still worth a
# final check against the user's real league (via espn_api, once league access
# is wired up) in case the commissioner customized anything.
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

# ESPN default kicker scoring. Confirmed 2026-07-13 against ESPN's own scoring
# master list. Not yet wired into WEEKLY_STATS_SCHEMA/data_loader.py (kicker
# stats are a different shape — FG makes by distance bucket, not yards/TDs) —
# add a dedicated kicker table when Step 3+ needs to project K scoring.
KICKER_SCORING = {
    "pat_made": 1.0,
    "pat_missed": -1.0,
    "fg_made_0_39": 3.0,
    "fg_made_40_49": 4.0,
    "fg_made_50_plus": 5.0,
    "fg_missed": -1.0,
}

# ESPN default team Defense/Special Teams scoring. Sources disagreed on the
# exact points-allowed tiers and whether all defensive TDs are a flat 6 or
# split by type (INT/fumble return vs. kick/punt return) — the values below
# are ESPN's own scoring master list (games.espn.com), the most authoritative
# source found, but this is the one scoring category most likely to have been
# customized by a commissioner, so confirm against the real league before
# relying on it. Also not yet wired into a schema — DST stats are team-level
# (sacks, turnovers forced, points/yards allowed), not player-level, so this
# needs its own table, not WEEKLY_STATS_SCHEMA.
DST_SCORING = {
    "sack": 1.0,
    "interception": 2.0,
    "fumble_recovery": 2.0,
    "safety": 2.0,
    "blocked_kick": 2.0,  # blocked punt, FG, or PAT
    "interception_return_td": 3.0,
    "fumble_return_td": 3.0,
    "kick_or_punt_return_td": 4.0,
    # Points allowed -> fantasy points.
    "points_allowed_tiers": {
        0: 10,
        (1, 6): 7,
        (7, 13): 4,
        (14, 17): 1,
        (18, 21): 0,
        (22, 27): -1,
        (28, 34): -4,
        (35, 45): -7,
        46: -10,  # 46+
    },
}

# League roster/bench settings — placeholder pending confirmation with the user
# (see ROADMAP.md Step 1). Roster shape (1 QB/2 RB/2 WR/1 TE/1 FLEX/1 K/1 DST,
# 6 bench) is ESPN's standard default; scoring is Full PPR (KICKER_SCORING and
# DST_SCORING aren't included here yet since neither has a data table to back it).
LEAGUE_SETTINGS = {
    "roster_slots": {
        "QB": 1,
        "RB": 2,
        "WR": 2,
        "TE": 1,
        "FLEX": 1,  # RB/WR/TE
        "K": 1,
        "DST": 1,
    },
    "bench_size": 6,
    "scoring": FULL_PPR_SCORING,
}
