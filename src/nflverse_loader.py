"""Load real historical NFL data from nflverse (via the `nflreadpy` package)
into the shapes defined in `schema.py`.

This is a free, no-auth data source — distinct from the ESPN league API
(`espn_api`, still pending the user's league ID/cookies) that will eventually
supply the user's actual league settings and draft history. nflverse is the
stats backbone: player weekly/season stats, rosters, schedules, going back to
1999. See PROJECTS.md for the fuller source comparison.
"""

import pandas as pd
import polars as pl

from schema import PLAYERS_SCHEMA, WEEKLY_STATS_SCHEMA

FANTASY_POSITIONS = ["QB", "RB", "WR", "TE", "K"]

FUMBLE_COLUMNS = ["sack_fumbles_lost", "rushing_fumbles_lost", "receiving_fumbles_lost"]
TWO_PT_COLUMNS = ["passing_2pt_conversions", "rushing_2pt_conversions", "receiving_2pt_conversions"]

STAT_RENAMES = {
    "passing_yards": "pass_yds",
    "passing_tds": "pass_td",
    "passing_interceptions": "pass_int",
    "rushing_yards": "rush_yds",
    "rushing_tds": "rush_td",
    "receiving_yards": "rec_yds",
    "receiving_tds": "rec_td",
    "special_teams_tds": "special_teams_td",
}


def _derive_bye_weeks(schedules: pl.DataFrame) -> pl.DataFrame:
    """One row per team/season for the week number they didn't play.

    Restricted to regular season games: playoff week numbers overlap with
    (but don't line up against) regular season week numbers, and not every
    team makes the playoffs, so including them produces multiple false byes.
    """
    schedules = schedules.filter(pl.col("game_type") == "REG")
    long = pl.concat(
        [
            schedules.select("season", "week", pl.col("home_team").alias("team")),
            schedules.select("season", "week", pl.col("away_team").alias("team")),
        ]
    )
    all_weeks = long.select("season", "week").unique()
    teams = long.select("season", "team").unique()
    every_team_week = teams.join(all_weeks, on="season", how="inner")
    bye = every_team_week.join(long, on=["season", "team", "week"], how="anti")
    return bye.rename({"week": "bye_week"})


def load_players(seasons: list[int]) -> pd.DataFrame:
    """PLAYERS_SCHEMA rows for every rostered player in the given seasons.

    Deliberately not filtered to FANTASY_POSITIONS here (unlike
    `load_weekly_stats`): a roster's listed position (e.g. "LB") can differ
    from the position on a given week's stat line for hybrid/gadget players
    (a linebacker who also gets occasional RB carries shows up with
    position="RB" in player_stats but position="LB" on the roster) — filtering
    this table by position risks orphaning those weekly_stats rows in
    `normalize_player_week`'s merge. This table is the identity lookup; the
    stats table decides fantasy relevance.
    """
    import nflreadpy as nfl

    rosters = nfl.load_rosters(seasons)
    bye_weeks = _derive_bye_weeks(nfl.load_schedules(seasons))

    players = (
        rosters.select(
            pl.col("gsis_id").alias("player_id"),
            pl.col("full_name").alias("name"),
            "position",
            "team",
            "season",
        )
        .unique(subset=["player_id", "season"], keep="first")
        .join(bye_weeks, on=["season", "team"], how="left")
        .drop("season")
        .drop_nulls("player_id")
    )
    return players.to_pandas().astype(PLAYERS_SCHEMA)


def load_weekly_stats(seasons: list[int]) -> pd.DataFrame:
    """WEEKLY_STATS_SCHEMA rows for fantasy-relevant positions in the given seasons."""
    import nflreadpy as nfl

    stats = nfl.load_player_stats(seasons, summary_level="week")
    weekly = (
        stats.filter(pl.col("position").is_in(FANTASY_POSITIONS))
        .with_columns(
            pl.sum_horizontal(FUMBLE_COLUMNS).alias("fumbles_lost"),
            pl.sum_horizontal(TWO_PT_COLUMNS).alias("two_pt_conversions"),
        )
        .rename(STAT_RENAMES)
        .select(list(WEEKLY_STATS_SCHEMA))
    )
    return weekly.to_pandas().astype(WEEKLY_STATS_SCHEMA)
