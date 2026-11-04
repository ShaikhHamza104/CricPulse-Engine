from typing import Any

import duckdb

from ipl_analytics.db.session import get_connection
from ipl_analytics.pipelines.transform import TEAM_MAPPING, VENUE_MAPPING
from ipl_analytics.schemas.analytics import (
    HeadToHeadResponse,
    TossImpactResponse,
    VenueStatsResponse,
)
from ipl_analytics.schemas.player import (
    PlayerBattingStats,
    PlayerBowlingStats,
)


class AnalyticsRepository:
    """Repository for IPL analytical aggregations and leaderboards in DuckDB."""

    def __init__(self, connection: duckdb.DuckDBPyConnection | None = None) -> None:
        self.con = (
            connection if connection is not None else get_connection(read_only=True)
        )
        self._delivery_cols = self._get_table_columns("clean_deliveries")

    def _get_table_columns(self, table_name: str) -> set[str]:
        """Inspect column names once to adapt safely to the ETL table schema."""
        try:
            rows = self.con.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            return {str(row[1]).lower() for row in rows}
        except Exception:
            return set()

    @staticmethod
    def _fetch_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
        """Convert DuckDB cursor rows into dicts while preserving SQL NULL as Python None."""
        if cursor.description is None:
            return []
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_head_to_head(self, team1: str, team2: str) -> HeadToHeadResponse:
        """Compare two teams across all historical IPL matches, harmonizing franchise renamings."""
        raw_t1 = team1.strip().lower()
        raw_t2 = team2.strip().lower()
        t1 = TEAM_MAPPING.get(raw_t1, raw_t1)
        t2 = TEAM_MAPPING.get(raw_t2, raw_t2)

        query = """
            WITH h2h_matches AS (
                SELECT
                    team1,
                    team2,
                    winner
                FROM clean_matches
                WHERE (LOWER(team1) = LOWER(?) AND LOWER(team2) = LOWER(?))
                   OR (LOWER(team1) = LOWER(?) AND LOWER(team2) = LOWER(?))
            ),
            counts AS (
                SELECT
                    COUNT(*) AS total_matches,
                    COUNT(*) FILTER (WHERE LOWER(winner) = LOWER(?)) AS team1_wins,
                    COUNT(*) FILTER (WHERE LOWER(winner) = LOWER(?)) AS team2_wins,
                    COUNT(*) FILTER (
                        WHERE winner IS NULL
                           OR LOWER(winner) NOT IN (LOWER(?), LOWER(?))
                    ) AS ties_or_no_result
                FROM h2h_matches
            )
            SELECT
                ? AS team1,
                ? AS team2,
                total_matches,
                team1_wins,
                team2_wins,
                ties_or_no_result,
                COALESCE(
                    ROUND((team1_wins * 100.0) / NULLIF(total_matches, 0), 2),
                    0.0
                ) AS win_percentage_team1,
                COALESCE(
                    ROUND((team2_wins * 100.0) / NULLIF(total_matches, 0), 2),
                    0.0
                ) AS win_percentage_team2
            FROM counts
        """
        params = [t1, t2, t2, t1, t1, t2, t1, t2, t1, t2]
        rows = self._fetch_dicts(self.con.execute(query, params))
        return HeadToHeadResponse.model_validate(rows[0])

    def get_toss_impact(self) -> TossImpactResponse:
        """Aggregate how winning the toss impacts match outcomes and decisions."""
        query = """
            WITH toss_counts AS (
                SELECT
                    COUNT(*) AS total_matches,
                    COUNT(*) FILTER (
                        WHERE winner IS NOT NULL
                          AND toss_winner IS NOT NULL
                          AND LOWER(toss_winner) = LOWER(winner)
                    ) AS toss_winner_match_wins,
                    COUNT(*) FILTER (
                        WHERE LOWER(COALESCE(toss_decision, '')) = 'field'
                    ) AS chose_field_count,
                    COUNT(*) FILTER (
                        WHERE LOWER(COALESCE(toss_decision, '')) = 'bat'
                    ) AS chose_bat_count
                FROM clean_matches
            )
            SELECT
                total_matches,
                toss_winner_match_wins,
                COALESCE(
                    ROUND(
                        (toss_winner_match_wins * 100.0)
                        / NULLIF(total_matches, 0),
                        2
                    ),
                    0.0
                ) AS toss_win_match_win_pct,
                chose_field_count,
                chose_bat_count
            FROM toss_counts
        """
        rows = self._fetch_dicts(self.con.execute(query))
        return TossImpactResponse.model_validate(rows[0])

    def get_venue_stats(self, venue: str) -> VenueStatsResponse | None:
        """Calculate match and innings scoring statistics for a specific venue.

        Domain Rules Applied:
        - Harmonizes historical venue name variations (e.g. Wankhede variations).
        - Excludes Super Overs (COALESCE(is_super_over, 0) = 0).
        - Averages 1st innings par score ONLY on completed/bowled-out innings
          (>=19 overs or 10 wickets), preventing rain-shortened 5-over or washed-out
          matches from corrupting the venue par score.
        """
        raw_venue = venue.strip().lower()
        if not raw_venue:
            return None

        clean_venue = VENUE_MAPPING.get(raw_venue, raw_venue)

        query = """
            WITH venue_matches AS (
                SELECT
                    match_id,
                    venue,
                    city
                FROM clean_matches m
                WHERE LOWER(m.venue) = LOWER(?)
                   OR m.venue ILIKE ? ESCAPE '\\'
            ),
            innings_totals AS (
                SELECT
                    vm.match_id,
                    d.innings AS inning_id,
                    COALESCE(SUM(d.total_runs), 0) AS innings_score,
                    MAX(d.over_number) AS max_over,
                    COUNT(*) FILTER (WHERE d.is_wicket = TRUE) AS wickets_lost
                FROM venue_matches vm
                JOIN clean_deliveries d ON vm.match_id = d.match_id
                WHERE COALESCE(d.is_super_over, 0) = 0
                GROUP BY vm.match_id, d.innings
            )
            SELECT
                (SELECT MODE(venue) FROM venue_matches) AS venue,
                (SELECT MODE(city) FROM venue_matches WHERE city IS NOT NULL) AS city,
                (SELECT COUNT(*) FROM venue_matches) AS total_matches,
                COALESCE(
                    ROUND(
                        AVG(innings_score) FILTER (
                            WHERE inning_id = 1
                              AND (max_over >= 19 OR wickets_lost >= 10)
                        ),
                        2
                    ),
                    0.0
                ) AS avg_first_innings_score,
                COALESCE(MAX(innings_score), 0) AS highest_total
            FROM innings_totals
        """
        escaped = (
            clean_venue.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        rows = self._fetch_dicts(self.con.execute(query, [clean_venue, f"%{escaped}%"]))

        if not rows or rows[0]["total_matches"] == 0:
            return None

        return VenueStatsResponse.model_validate(rows[0])

    def get_orange_cap(
        self, season: int | None = None, limit: int = 10
    ) -> list[PlayerBattingStats]:
        """Return top run-scorers adhering to official IPL rules.

        Excludes super overs and wides from balls faced.
        """
        safe_limit = min(max(1, limit), 100)

        season_clause = ""
        params: list[Any] = []
        if season is not None:
            season_clause = "AND CAST(m.season AS INTEGER) = ?"
            params.append(season)

        query = f"""
            WITH dedup_players AS (
                SELECT
                    LOWER(player_name) AS name_key,
                    MIN(player_id) AS player_id,
                    MIN(player_name) AS player_name
                FROM clean_players
                GROUP BY LOWER(player_name)
            )
            SELECT
                COALESCE(p.player_id, d.batter) AS player_id,
                COALESCE(p.player_name, d.batter) AS player_name,
                COUNT(DISTINCT d.match_id) AS matches_played,
                COALESCE(SUM(d.batter_runs), 0) AS total_runs,
                COUNT(*) FILTER (WHERE COALESCE(d.wides, 0) = 0) AS balls_faced,
                COALESCE(
                    ROUND(
                        (SUM(d.batter_runs) * 100.0)
                        / NULLIF(COUNT(*) FILTER (WHERE COALESCE(d.wides, 0) = 0), 0),
                        2
                    ),
                    0.0
                ) AS strike_rate,
                COUNT(*) FILTER (WHERE d.batter_runs = 4 AND d.is_boundary = TRUE) AS fours,
                COUNT(*) FILTER (WHERE d.batter_runs = 6 AND d.is_boundary = TRUE) AS sixes
            FROM clean_deliveries d
            JOIN clean_matches m ON d.match_id = m.match_id
            LEFT JOIN dedup_players p ON LOWER(d.batter) = p.name_key
            WHERE COALESCE(d.is_super_over, 0) = 0
              {season_clause}
            GROUP BY d.batter, p.player_id, p.player_name
            ORDER BY total_runs DESC, strike_rate DESC, balls_faced ASC
            LIMIT ?
        """
        params.append(safe_limit)
        rows = self._fetch_dicts(self.con.execute(query, params))
        return [PlayerBattingStats.model_validate(row) for row in rows]

    def get_purple_cap(
        self, season: int | None = None, limit: int = 10
    ) -> list[PlayerBowlingStats]:
        """Return top wicket-takers adhering to official bowler rules and excluding super overs."""
        safe_limit = min(max(1, limit), 100)

        season_clause = ""
        params: list[Any] = []
        if season is not None:
            season_clause = "AND CAST(m.season AS INTEGER) = ?"
            params.append(season)

        query = f"""
            WITH dedup_players AS (
                SELECT
                    LOWER(player_name) AS name_key,
                    MIN(player_id) AS player_id,
                    MIN(player_name) AS player_name
                FROM clean_players
                GROUP BY LOWER(player_name)
            ),
            bowler_agg AS (
                SELECT
                    COALESCE(p.player_id, d.bowler) AS player_id,
                    COALESCE(p.player_name, d.bowler) AS player_name,
                    COUNT(*) FILTER (
                        WHERE CAST(d.is_wicket AS BOOLEAN)
                          AND LOWER(COALESCE(d.dismissal_kind, '')) NOT IN (
                              'run out',
                              'retired hurt',
                              'retired out',
                              'obstructing the field'
                          )
                    ) AS wickets,
                    COUNT(*) FILTER (
                        WHERE COALESCE(d.wides, 0) = 0
                          AND COALESCE(d.noballs, 0) = 0
                    ) AS balls_bowled,
                    COALESCE(
                        SUM(
                            d.batter_runs
                            + COALESCE(d.wides, 0)
                            + COALESCE(d.noballs, 0)
                        ),
                        0
                    ) AS runs_conceded
                FROM clean_deliveries d
                JOIN clean_matches m ON d.match_id = m.match_id
                LEFT JOIN dedup_players p ON LOWER(d.bowler) = p.name_key
                WHERE COALESCE(d.is_super_over, 0) = 0
                  {season_clause}
                GROUP BY d.bowler, p.player_id, p.player_name
            )
            SELECT
                player_id,
                player_name,
                wickets,
                balls_bowled,
                (balls_bowled // 6) + ((balls_bowled % 6) / 10.0) AS overs_bowled,
                runs_conceded,
                COALESCE(
                    ROUND((runs_conceded * 6.0) / NULLIF(balls_bowled, 0), 2),
                    0.0
                ) AS economy_rate
            FROM bowler_agg
            ORDER BY wickets DESC, economy_rate ASC, runs_conceded ASC
            LIMIT ?
        """
        params.append(safe_limit)
        rows = self._fetch_dicts(self.con.execute(query, params))
        return [PlayerBowlingStats.model_validate(row) for row in rows]
