"""Data Access Layer (DAL) Repositories for DuckDB queries."""

from ipl_analytics.repositories.analytics_repository import AnalyticsRepository
from ipl_analytics.repositories.match_repository import MatchRepository
from ipl_analytics.repositories.player_repository import PlayerRepository

__all__ = [
    "AnalyticsRepository",
    "MatchRepository",
    "PlayerRepository",
]
