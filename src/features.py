"""Point-in-time feature engineering for the Step 3 projection model.

Every function here must only use information available *before* the week
being predicted - no target leakage. A projection for a given week can't see
that week's own stat line.
"""

import pandas as pd

TRAILING_WINDOWS = (3, 5)


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
