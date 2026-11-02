from ipl_analytics.db.session import get_connection
import duckdb
from fastapi import Depends
from ipl_analytics.repositories.match_repository import MatchRepository
from ipl_analytics.repositories.player_repository import PlayerRepository
from ipl_analytics.repositories.analytics_repository import AnalyticsRepository

def get_db():
    conn = get_connection(read_only=True)
    try:
        yield conn  # Gives the connection to the route
    finally:
        conn.close()  # ALWAYS runs when the request is done, even if an error happened!


def get_match_repo(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> MatchRepository:
    return MatchRepository(connection=con)

def get_player_repo(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> PlayerRepository:
    return PlayerRepository(connection=con)

def get_analytics_repo(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> AnalyticsRepository:
    return AnalyticsRepository(connection=con)