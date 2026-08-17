"""Point-in-time feature engineering for the Step 3 projection model.

Every function here must only use information available *before* the week
being predicted - no target leakage. A projection for a given week can't see
that week's own stat line.
"""

import pandas as pd

TRAILING_WINDOWS = (3, 5)
CATEGORICAL_FEATURES = ["position", "team"]

FEATURE_COLUMNS = [
    "trailing_3g_avg",
    "trailing_5g_avg",
    "season_to_date_avg",
    "prior_season_total_points",
    "prior_season_games_played",
    "prior_season_avg_points",
    *CATEGORICAL_FEATURES,
]


def add_trailing_form_features(player_week: pd.DataFrame) -> pd.DataFrame:
    """Adds trailing N-game rolling averages of fantasy_points per player.

    Rolling windows carry across season boundaries rather than resetting to
    NaN at the start of every season - a player's last 3 games are still the
    most relevant signal of current form whether they were in December or
    September. Shifted by one game so week W's features never include week
    W's own result; a player's very first tracked game has no prior games at
    all and stays NaN (LightGBM handles missing values natively, so this is
    left as-is rather than imputed here).
    """
    df = player_week.sort_values(["player_id", "season", "week"]).copy()
    grouped = df.groupby("player_id")["fantasy_points"]
    for window in TRAILING_WINDOWS:
        df[f"trailing_{window}g_avg"] = grouped.transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        )
    return df


def add_season_to_date_features(player_week: pd.DataFrame) -> pd.DataFrame:
    """Adds each player's average fantasy_points so far *this season only*.

    Unlike trailing form, this deliberately resets each season - it answers
    "how is this player doing this year," a different question than "what
    have their last few games looked like." Shifted by one game, same as
    trailing form. NaN for a player's first game of a season (nothing to
    average yet); `add_prior_season_features` below covers that gap.
    """
    df = player_week.sort_values(["player_id", "season", "week"]).copy()
    grouped = df.groupby(["player_id", "season"])["fantasy_points"]
    df["season_to_date_avg"] = grouped.transform(lambda s: s.shift(1).expanding().mean())
    return df


def add_prior_season_features(player_week: pd.DataFrame) -> pd.DataFrame:
    """Adds each player's prior-season total/games/average fantasy_points.

    Covers the cold-start gap `add_season_to_date_features` leaves early in
    a season: a returning veteran's most recent full season is a much better
    prior than nothing for Week 1-3 projections. True rookies (no prior
    season in this dataset at all) still end up NaN here - left for LightGBM
    to handle natively rather than imputed, same convention as the other
    feature functions.
    """
    totals = (
        player_week.groupby(["player_id", "season"])["fantasy_points"]
        .agg(prior_season_total_points="sum", prior_season_games_played="count")
        .reset_index()
    )
    totals["prior_season_avg_points"] = (
        totals["prior_season_total_points"] / totals["prior_season_games_played"]
    )
    totals["season"] += 1  # shift forward one year so a join on `season` lines up as "prior"

    return player_week.merge(totals, on=["player_id", "season"], how="left")


def add_categorical_features(player_week: pd.DataFrame) -> pd.DataFrame:
    """Casts position/team to pandas `category` dtype for LightGBM's native
    categorical handling - no one-hot encoding needed.

    A "bye-week flag" was in the original piece-5 plan but is dropped here:
    every row in this dataset already represents a game the player actually
    played (byes produce no stat line at all, so they're absent by
    construction), so a boolean "is bye week" feature could never be True on
    any real row - it wouldn't add information.
    """
    df = player_week.copy()
    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].astype("category")
    return df


def build_features(player_week: pd.DataFrame) -> pd.DataFrame:
    """Runs the full feature pipeline: trailing form, season-to-date,
    prior-season, and categorical features, in that order."""
    df = add_trailing_form_features(player_week)
    df = add_season_to_date_features(df)
    df = add_prior_season_features(df)
    df = add_categorical_features(df)
    return df
