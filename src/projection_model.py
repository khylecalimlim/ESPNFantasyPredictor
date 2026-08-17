"""Train/eval scaffolding for the Step 3 fantasy points projection model."""

import pandas as pd

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
