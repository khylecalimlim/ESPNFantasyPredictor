"""Load and normalize player/stat data into the schema defined in schema.py.

Phase 1 reads from manually-supplied CSVs. The `validate_schema` /
`normalize_player_week` functions operate on DataFrames directly so the same
logic will work once an `espn_api`-backed loader is added later (see
ROADMAP.md Step 2 "(Later)" items) without needing to change here.
"""

import pandas as pd

from schema import PLAYERS_SCHEMA, WEEKLY_STATS_SCHEMA, FULL_PPR_SCORING


def validate_schema(df: pd.DataFrame, schema: dict, table_name: str) -> pd.DataFrame:
    """Check required columns are present and cast to the expected dtypes."""
    missing = set(schema) - set(df.columns)
    if missing:
        raise ValueError(f"{table_name} is missing required columns: {sorted(missing)}")
    return df.astype(schema)


def load_players_csv(path: str) -> pd.DataFrame:
    return validate_schema(pd.read_csv(path), PLAYERS_SCHEMA, "players")


def load_weekly_stats_csv(path: str) -> pd.DataFrame:
    return validate_schema(pd.read_csv(path), WEEKLY_STATS_SCHEMA, "weekly_stats")


def compute_fantasy_points(weekly_df: pd.DataFrame, scoring: dict = FULL_PPR_SCORING) -> pd.Series:
    """Full PPR fantasy points for each row, from the raw stat columns."""
    points = pd.Series(0.0, index=weekly_df.index)
    for stat, weight in scoring.items():
        points += weekly_df[stat] * weight
    return points


def normalize_player_week(players_df: pd.DataFrame, weekly_df: pd.DataFrame) -> pd.DataFrame:
    """Merge player metadata onto weekly stats and attach computed fantasy points."""
    players_df = validate_schema(players_df, PLAYERS_SCHEMA, "players")
    weekly_df = validate_schema(weekly_df, WEEKLY_STATS_SCHEMA, "weekly_stats")

    merged = weekly_df.merge(players_df, on=["player_id", "season"], how="left", validate="many_to_one")
    if merged["name"].isna().any():
        orphaned = merged.loc[merged["name"].isna(), ["player_id", "season"]].drop_duplicates()
        raise ValueError(f"weekly_stats has (player_id, season) not found in players: {orphaned.values.tolist()}")

    merged["fantasy_points"] = compute_fantasy_points(merged)
    return merged.sort_values(["season", "week", "player_id"]).reset_index(drop=True)
