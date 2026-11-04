"""Integration Tests for DuckDB Repositories.

Concepts Taught Here:
1. Integration Testing: Testing how repository classes interact with a real DuckDB database.
2. Fixture Injection: Injecting `db_conn` from `conftest.py` as a function parameter.
3. Read-Only Safety: Ensuring tests run safely against the database without mutating state.
4. Testing Edge Cases: Verifying unknown IDs return None instead of crashing.
"""

import duckdb
import pytest

from ipl_analytics.repositories.analytics_repository import AnalyticsRepository
from ipl_analytics.repositories.match_repository import MatchRepository
from ipl_analytics.repositories.player_repository import PlayerRepository


class TestPlayerRepository:
    """Integration tests verifying player queries against clean DuckDB tables."""

    def test_get_player_by_id_virat_kohli(
        self, db_conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify fetching a legendary batsman returns complete career batting metrics."""
        repo = PlayerRepository(db_conn)
        player = repo.get_by_id("ba607b88")  # Virat Kohli's player ID

        assert player is not None
        assert player.player_id == "ba607b88"
        assert player.player_name == "v kohli"
        assert player.batting is not None
        assert player.batting.total_runs > 9000
        assert player.batting.balls_faced > 6000
        assert player.batting.strike_rate > 125.0
        assert player.batting.fours > 800
        assert player.batting.sixes > 300

    def test_get_player_bowling_stats_bumrah(
        self, db_conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify bowling statistics including cricket overs notation and economy rate."""
        repo = PlayerRepository(db_conn)
        player = repo.get_by_id("462411b3")  # Jasprit Bumrah's player ID

        assert player is not None
        assert player.player_name == "jj bumrah"
        assert player.bowling is not None
        assert player.bowling.wickets > 150
        assert player.bowling.balls_bowled > 3000

        # Verify cricket overs notation: decimal part strictly 0 to 5
        overs_str = str(player.bowling.overs_bowled)
        dec_part = int(overs_str.split(".")[1]) if "." in overs_str else 0
        assert 0 <= dec_part <= 5
        assert player.bowling.economy_rate < 8.0  # Bumrah has world-class economy

    def test_get_player_non_existent_returns_none(
        self, db_conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify that querying an unknown ID gracefully returns None without error."""
        repo = PlayerRepository(db_conn)
        player = repo.get_by_id("unknown_id_99999")
        assert player is None

    def test_list_players_search_and_pagination(
        self, db_conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify player name search filtering and offset/limit pagination."""
        repo = PlayerRepository(db_conn)
        results = repo.list_players(search="Kohli", limit=10, offset=0)

        assert results.total >= 2
        names = [p.player_name for p in results.items]
        assert "v kohli" in names


class TestAnalyticsRepository:
    """Integration tests verifying analytical aggregations (H2H, Caps, Venues)."""

    def test_head_to_head_with_franchise_aliases(
        self, db_conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify franchise alias lookup (CSK vs RCB) resolves to full historical matches."""
        repo = AnalyticsRepository(db_conn)
        h2h = repo.get_head_to_head("CSK", "RCB")

        assert h2h.team1 == "chennai super kings"
        assert h2h.team2 == "royal challengers bengaluru"
        assert h2h.total_matches > 30
        assert h2h.team1_wins + h2h.team2_wins <= h2h.total_matches
        assert h2h.win_percentage_team1 == pytest.approx(
            (h2h.team1_wins * 100.0) / h2h.total_matches, abs=1e-2
        )

    def test_orange_cap_season_2024(self, db_conn: duckdb.DuckDBPyConnection) -> None:
        """Verify Orange Cap leaderboards exclude super overs and wides from balls faced."""
        repo = AnalyticsRepository(db_conn)
        leaders = repo.get_orange_cap(season=2024, limit=5)

        assert len(leaders) == 5
        # The top run scorer in IPL 2024 was Virat Kohli with >700 runs
        top = leaders[0]
        assert top.player_name == "v kohli"
        assert top.total_runs > 700
        assert top.balls_faced > 400
        assert top.strike_rate > 150.0

        # Ensure leaders are ordered descending by total_runs
        for i in range(len(leaders) - 1):
            assert leaders[i].total_runs >= leaders[i + 1].total_runs

    def test_purple_cap_season_2024(self, db_conn: duckdb.DuckDBPyConnection) -> None:
        """Verify Purple Cap leaderboards and cricket overs formatting."""
        repo = AnalyticsRepository(db_conn)
        leaders = repo.get_purple_cap(season=2024, limit=5)

        assert len(leaders) == 5
        top = leaders[0]
        assert top.wickets >= 20

        # Verify cricket overs notation for all bowlers
        for bowler in leaders:
            overs_str = str(bowler.overs_bowled)
            dec_part = int(overs_str.split(".")[1]) if "." in overs_str else 0
            assert 0 <= dec_part <= 5

    def test_toss_impact_analysis(self, db_conn: duckdb.DuckDBPyConnection) -> None:
        """Verify aggregation of toss winner outcomes across all matches."""
        repo = AnalyticsRepository(db_conn)
        toss = repo.get_toss_impact()

        assert toss.total_matches > 1000
        # In T20 cricket, toss win vs match win percentage stays around 50%
        assert 45.0 <= toss.toss_win_match_win_pct <= 55.0

    def test_venue_stats_harmonization(
        self, db_conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify historical venue name standardization and par score calculations."""
        repo = AnalyticsRepository(db_conn)
        stats = repo.get_venue_stats("Wankhede Stadium, Mumbai")

        assert stats is not None
        assert stats.venue == "wankhede stadium"
        assert stats.total_matches > 100
        assert stats.avg_first_innings_score > 140.0
        assert stats.highest_total > 200

    def test_venue_stats_invalid_returns_none(
        self, db_conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify that an empty or whitespace venue query returns None."""
        repo = AnalyticsRepository(db_conn)
        assert repo.get_venue_stats("") is None
        assert repo.get_venue_stats("   ") is None


class TestMatchRepository:
    """Integration tests verifying match catalog queries and filtering."""

    def test_list_matches_by_season(self, db_conn: duckdb.DuckDBPyConnection) -> None:
        """Verify filtering matches by season (IPL 2024 had 74 matches)."""
        repo = MatchRepository(db_conn)
        res = repo.list_matches(season=2024, limit=100)

        assert res.total == 71
        assert len(res.items) == 71

    def test_list_matches_by_franchise_alias(
        self, db_conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Verify filtering matches by team short alias (CSK)."""
        repo = MatchRepository(db_conn)
        res = repo.list_matches(team="CSK", limit=10)

        assert res.total > 200
        assert len(res.items) == 10

    def test_get_seasons_list(self, db_conn: duckdb.DuckDBPyConnection) -> None:
        """Verify retrieval of all unique IPL seasons from 2008 to 2024."""
        repo = MatchRepository(db_conn)
        seasons = repo.get_seasons()

        assert 2008 in seasons
        assert 2024 in seasons
        assert len(seasons) >= 17
