"""Connects to the user's real ESPN Fantasy league via espn_api.

Reads credentials/league IDs from a gitignored .env file (see .env.example
for the expected keys) rather than hardcoding them, since espn_s2/SWID are
session credentials.
"""

import os

from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()


def get_league(league_id: int, year: int) -> League:
    """Connects to an ESPN Fantasy league, using .env cookies if present.

    Public leagues work with no credentials; private leagues need ESPN_S2 and
    SWID set in .env (both required together, or omit both for a public league).
    """
    espn_s2 = os.environ.get("ESPN_S2") or None
    swid = os.environ.get("SWID") or None
    return League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)


def get_last_year_league() -> League:
    """Convenience wrapper for the league ID/year pair stored in .env."""
    return get_league(
        league_id=int(os.environ["LEAGUE_ID_LAST_YEAR"]),
        year=int(os.environ["SEASON_YEAR_LAST"]),
    )
