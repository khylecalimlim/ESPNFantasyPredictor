"""Data schema definitions for the ESPN Fantasy Predictor pipeline.

Each table below is defined as a dict of column name -> pandas dtype string.
These are the contract that `data_loader.py` validates incoming data against,
regardless of whether it eventually comes from a manual CSV export or the
`espn_api` package.
"""

# One row per player (season-independent identity/metadata).
PLAYERS_SCHEMA = {
    "player_id": "int64",
    "name": "object",
    "position": "object",  # QB, RB, WR, TE, K, DST
    "team": "object",  # NFL team abbreviation
    "bye_week": "int64",
}

# One row per player per week per season.
WEEKLY_STATS_SCHEMA = {
    "player_id": "int64",
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
    "fumbles_lost": "float64",
    "two_pt_conversions": "float64",
}

# One row per player per season (aggregated from weekly_stats).
SEASON_TOTALS_SCHEMA = {
    "player_id": "int64",
    "season": "int64",
    "games_played": "int64",
    "total_fantasy_points": "float64",
}

# One row per player per season, average draft position from mock/real drafts.
DRAFT_ADP_SCHEMA = {
    "player_id": "int64",
    "season": "int64",
    "adp": "float64",
    "adp_position_rank": "int64",
}

# Full PPR scoring weights, keyed to the stat columns in WEEKLY_STATS_SCHEMA.
# NOTE: these are standard Full PPR defaults, not yet confirmed against the
# user's actual league settings (see ROADMAP.md Step 1).
FULL_PPR_SCORING = {
    "pass_yds": 0.04,  # 1 pt per 25 yds
    "pass_td": 4.0,
    "pass_int": -2.0,
    "rush_yds": 0.1,  # 1 pt per 10 yds
    "rush_td": 6.0,
    "receptions": 1.0,  # the "PPR" in Full PPR
    "rec_yds": 0.1,  # 1 pt per 10 yds
    "rec_td": 6.0,
    "fumbles_lost": -2.0,
    "two_pt_conversions": 2.0,
}

# League roster/bench settings — placeholder pending confirmation with the user.
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
