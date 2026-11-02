from typing import Any, Optional
import duckdb

from ipl_analytics.db.session import get_connection
from ipl_analytics.schemas.player import (
    BattingStats,
    BowlingStats,
    PaginatedPlayerResponse,
    PlayerBase,
    PlayerProfile,
)


class PlayerRepository:
    """Repository for querying IPL player profiles and statistics from DuckDB."""

    def __init__(
        self, connection: Optional[duckdb.DuckDBPyConnection] = None
    ) -> None:
        self.con = (
            connection
            if connection is not None
            else get_connection(read_only=True)
        )

    @staticmethod
    def _fetch_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
        """Convert DuckDB cursor rows into dicts while preserving SQL NULL as Python None."""
        if cursor.description is None:
            return []
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _get_batting_stats(self, player_name: str) -> Optional[BattingStats]:
        """Calculate career batting stats for a player from clean_deliveries."""
        query = """
            SELECT
                COUNT(DISTINCT match_id) AS matches_played,
                COALESCE(SUM(batter_runs), 0) AS total_runs,
                COUNT(*) FILTER (WHERE COALESCE(wides, 0) = 0) AS balls_faced,
                COALESCE(
                    ROUND(
                        (SUM(batter_runs) * 100.0)
                        / NULLIF(COUNT(*) FILTER (WHERE COALESCE(wides, 0) = 0), 0),
                        2
                    ),
                    0.0
                ) AS strike_rate,
                COUNT(*) FILTER (WHERE batter_runs = 4) AS fours,
                COUNT(*) FILTER (WHERE batter_runs = 6) AS sixes
            FROM clean_deliveries
            WHERE LOWER(batter) = LOWER(?)
        """
        rows = self._fetch_dicts(self.con.execute(query, [player_name]))
        if not rows or rows[0]["matches_played"] == 0:
            return None

        return BattingStats.model_validate(rows[0])

    def _get_bowling_stats(self, player_name: str) -> Optional[BowlingStats]:
        """Calculate career bowling stats for a player from clean_deliveries."""
        query = """
            WITH bowler_deliveries AS (
                SELECT
                    COUNT(*) AS total_deliveries,
                    COUNT(*) FILTER (
                        WHERE is_wicket = TRUE
                          AND LOWER(COALESCE(dismissal_kind, '')) NOT IN (
                              'run out',
                              'retired hurt',
                              'retired out',
                              'obstructing the field'
                          )
                    ) AS wickets,
                    COUNT(*) FILTER (
                        WHERE COALESCE(wides, 0) = 0
                          AND COALESCE(noballs, 0) = 0
                    ) AS balls_bowled,
                    COALESCE(
                        SUM(
                            batter_runs
                            + COALESCE(wides, 0)
                            + COALESCE(noballs, 0)
                        ),
                        0
                    ) AS runs_conceded
                FROM clean_deliveries
                WHERE LOWER(bowler) = LOWER(?)
            )
            SELECT
                total_deliveries,
                wickets,
                balls_bowled,
                ROUND(balls_bowled / 6.0, 1) AS overs_bowled,
                runs_conceded,
                COALESCE(
                    ROUND((runs_conceded * 6.0) / NULLIF(balls_bowled, 0), 2),
                    0.0
                ) AS economy_rate
            FROM bowler_deliveries
        """
        rows = self._fetch_dicts(self.con.execute(query, [player_name]))
        if not rows or rows[0]["total_deliveries"] == 0:
            return None

        return BowlingStats.model_validate(rows[0])

    def get_by_id(self, player_id: str) -> Optional[PlayerProfile]:
        """Look up a single player by player_id and compute their career profile."""
        clean_id = player_id.strip()
        if not clean_id:
            return None

        player_query = """
            SELECT player_id, player_name
            FROM clean_players
            WHERE player_id = ?
            LIMIT 1
        """
        player_rows = self._fetch_dicts(
            self.con.execute(player_query, [clean_id])
        )
        if not player_rows:
            return None

        player_name = player_rows[0]["player_name"]
        batting = self._get_batting_stats(player_name)
        bowling = self._get_bowling_stats(player_name)

        return PlayerProfile(
            player_id=player_rows[0]["player_id"],
            player_name=player_name,
            batting=batting,
            bowling=bowling,
        )

    def list_players(
        self,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedPlayerResponse:
        """Browse players with optional case-insensitive substring search."""
        safe_limit = min(max(1, limit), 100)
        safe_offset = max(0, offset)

        conditions: list[str] = []
        params: list[Any] = []

        if search is not None and search.strip():
            # Escape SQL LIKE wildcards (%, _, \) so user input is treated literally
            escaped_search = (
                search.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            conditions.append("player_name ILIKE ? ESCAPE '\\'")
            params.append(f"%{escaped_search}%")

        where_clause = (
            f"WHERE {' AND '.join(conditions)}" if conditions else ""
        )

        # 1. Total matching players count
        count_query = f"SELECT COUNT(*) FROM clean_players {where_clause}"
        count_row = self.con.execute(count_query, params).fetchone()
        total = int(count_row[0]) if count_row else 0

        # 2. Paginated player items
        data_query = f"""
            SELECT player_id, player_name
            FROM clean_players
            {where_clause}
            ORDER BY player_name ASC, player_id ASC
            LIMIT ? OFFSET ?
        """
        cursor = self.con.execute(
            data_query, [*params, safe_limit, safe_offset]
        )
        rows = self._fetch_dicts(cursor)

        items = [PlayerBase.model_validate(row) for row in rows]

        return PaginatedPlayerResponse(
            total=total,
            limit=safe_limit,
            offset=safe_offset,
            items=items,
        )
