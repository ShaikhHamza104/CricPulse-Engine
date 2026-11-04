from typing import Any

import duckdb

from ipl_analytics.db.session import get_connection
from ipl_analytics.pipelines.transform import TEAM_MAPPING, VENUE_MAPPING
from ipl_analytics.schemas.match import (
    MatchDetail,
    MatchFilterParams,
    MatchSummary,
    PaginatedMatchResponse,
)


class MatchRepository:
    """Repository for querying IPL match data from DuckDB."""

    def __init__(self, connection: duckdb.DuckDBPyConnection | None = None) -> None:
        self.con = (
            connection if connection is not None else get_connection(read_only=True)
        )

    @staticmethod
    def _fetch_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
        """Convert DuckDB cursor rows into dicts while preserving SQL NULL as Python None.

        Note: Avoids `.df().to_dict(orient="records")` because Pandas converts
        SQL NULL into `float('nan')`, which crashes Pydantic's Optional[str] validation.
        """
        if cursor.description is None:
            return []
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_by_id(self, match_id: Any) -> MatchDetail | None:
        """Look up a single match by its match_id."""
        try:
            int_id = int(str(match_id).strip())
        except (ValueError, TypeError):
            return None

        query = """
            SELECT *
            FROM clean_matches
            WHERE match_id = ?
            LIMIT 1
        """
        cursor = self.con.execute(query, [int_id])
        rows = self._fetch_dicts(cursor)
        if not rows:
            return None

        return MatchDetail.model_validate(rows[0])

    def list_matches(
        self,
        filters: MatchFilterParams | None = None,
        season: int | None = None,
        team: str | None = None,
        venue: str | None = None,
        city: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedMatchResponse:
        """Browse matches with optional multi-criteria filters."""
        # Unpack from MatchFilterParams if supplied
        if filters is not None:
            season = filters.season if season is None else season
            team = filters.team if team is None else team
            venue = filters.venue if venue is None else venue
            city = filters.city if city is None else city
            limit = filters.limit
            offset = filters.offset

        safe_limit = min(max(1, limit), 100)
        safe_offset = max(0, offset)

        conditions: list[str] = []
        params: list[Any] = []

        if season is not None:
            conditions.append("CAST(season AS INTEGER) = ?")
            params.append(season)

        if team is not None and team.strip():
            raw_team = team.strip().lower()
            clean_team = TEAM_MAPPING.get(raw_team, raw_team)
            conditions.append("(LOWER(team1) = LOWER(?) OR LOWER(team2) = LOWER(?))")
            params.extend([clean_team, clean_team])

        if venue is not None and venue.strip():
            raw_venue = venue.strip().lower()
            clean_venue = VENUE_MAPPING.get(raw_venue, raw_venue)
            escaped_venue = (
                clean_venue.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            conditions.append("venue ILIKE ? ESCAPE '\\'")
            params.append(f"%{escaped_venue}%")

        if city is not None and city.strip():
            escaped_city = (
                city.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            conditions.append("city ILIKE ? ESCAPE '\\'")
            params.append(f"%{escaped_city}%")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # 1. Fetch total matching count (remains accurate even when offset >= total)
        count_query = f"SELECT COUNT(*) FROM clean_matches {where_clause}"
        count_row = self.con.execute(count_query, params).fetchone()
        total = int(count_row[0]) if count_row else 0

        # 2. Fetch paginated match rows
        data_query = f"""
            SELECT *
            FROM clean_matches
            {where_clause}
            ORDER BY match_id DESC
            LIMIT ? OFFSET ?
        """
        cursor = self.con.execute(data_query, [*params, safe_limit, safe_offset])
        rows = self._fetch_dicts(cursor)

        items = [MatchSummary.model_validate(row) for row in rows]

        return PaginatedMatchResponse(
            total=total,
            limit=safe_limit,
            offset=safe_offset,
            items=items,
        )

    def get_seasons(self) -> list[int]:
        """Return a descending list of all unique IPL seasons."""
        query = """
            SELECT DISTINCT CAST(season AS INTEGER) AS season_num
            FROM clean_matches
            WHERE season IS NOT NULL
            ORDER BY season_num DESC
        """
        rows = self.con.execute(query).fetchall()
        return [int(row[0]) for row in rows]
