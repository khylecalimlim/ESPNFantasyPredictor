"""Train/eval scaffolding for the Step 3 fantasy points projection model."""

import lightgbm as lgb
import pandas as pd

from features import FEATURE_COLUMNS

# Kickers have no real fantasy_points signal yet - WEEKLY_STATS_SCHEMA doesn't
# carry FG/PAT stats (see schema.py's KICKER_SCORING note), so every K row's
# fantasy_points is a data gap masquerading as a true zero, not a real
# performance signal. The handful of DB/DL/LB/P rows are gadget-play noise
# (~54 rows total across 6 seasons), not standard fantasy-relevant
# production. Both excluded from the model.
MODEL_POSITIONS = ["QB", "RB", "WR", "TE"]


def filter_to_model_positions(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["position"].isin(MODEL_POSITIONS)].copy()


def split_by_season(
    df: pd.DataFrame, train_seasons: list[int], val_season: int, test_season: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits by season, not by row, so no future season ever leaks into
    training or validation."""
    train = df[df["season"].isin(train_seasons)].copy()
    val = df[df["season"] == val_season].copy()
    test = df[df["season"] == test_season].copy()
    return train, val, test


def fit_baseline(train: pd.DataFrame) -> dict:
    """Fits the last-resort fallback (per-position average fantasy_points)
    used by `baseline_predict` for rows with no trailing or prior-season
    history at all - fit from training data only, so it never leaks the
    validation/test distribution back into the baseline."""
    return train.groupby("position", observed=True)["fantasy_points"].mean().to_dict()


def baseline_predict(df: pd.DataFrame, position_fallback: dict) -> pd.Series:
    """Trailing-3-game average, falling back to the prior-season average,
    falling back to the position's training-set average - the bar the real
    model has to beat."""
    pred = df["trailing_3g_avg"].fillna(df["prior_season_avg_points"])
    return pred.fillna(df["position"].map(position_fallback))


def train_lightgbm(
    train: pd.DataFrame, val: pd.DataFrame, feature_columns: list[str] = FEATURE_COLUMNS
) -> lgb.LGBMRegressor:
    """Trains a LightGBM regressor on fantasy_points.

    Early-stops against the validation set (picks the number of trees by
    validation MAE) rather than a fixed tree count - the held-out test set
    stays completely untouched until final evaluation.
    """
    model = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.05, random_state=42)
    model.fit(
        train[feature_columns],
        train["fantasy_points"],
        eval_X=val[feature_columns],
        eval_y=val["fantasy_points"],
        eval_metric="mae",
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
    )
    return model
