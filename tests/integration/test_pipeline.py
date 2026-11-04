"""Integration Tests for the ETL Pipeline & Processed Datasets.

Concepts Taught Here:
1. Pipeline Verification: Ensuring the ETL output meets data quality constraints.
2. Referential Integrity: Confirming deliveries reference valid match IDs.
3. Domain Invariants: Checking overs range (0 to 19) and wicket completeness.
"""

import duckdb


def _get_count(db: duckdb.DuckDBPyConnection, sql: str) -> int:
    """Helper to safely fetch a single scalar count from DuckDB."""
    row = db.execute(sql).fetchone()
    assert row is not None, "Query returned no rows"
    return int(row[0])


class TestDataPipelineIntegrity:
    """Tests verifying the loaded tables in DuckDB meet all quality contracts."""

    def test_table_row_counts(self, db_conn: duckdb.DuckDBPyConnection) -> None:
        """Verify all three core tables are populated with expected row volumes."""
        matches_count = _get_count(db_conn, "SELECT COUNT(*) FROM clean_matches")
        deliveries_count = _get_count(db_conn, "SELECT COUNT(*) FROM clean_deliveries")
        players_count = _get_count(db_conn, "SELECT COUNT(*) FROM clean_players")

        assert matches_count >= 1240, f"Expected >=1240 matches, got {matches_count}"
        assert deliveries_count >= 290000, (
            f"Expected >=290000 balls, got {deliveries_count}"
        )
        assert players_count >= 800, f"Expected >=800 players, got {players_count}"

    def test_referential_integrity(self, db_conn: duckdb.DuckDBPyConnection) -> None:
        """Verify no orphan deliveries exist without a corresponding match record."""
        orphan_count = _get_count(
            db_conn,
            """
            SELECT COUNT(*)
            FROM clean_deliveries d
            LEFT JOIN clean_matches m ON d.match_id = m.match_id
            WHERE m.match_id IS NULL
            """,
        )
        assert orphan_count == 0, f"Found {orphan_count} orphan deliveries"

    def test_overs_range_integrity(self, db_conn: duckdb.DuckDBPyConnection) -> None:
        """Verify over numbers are strictly between 0 and 19 (standard 20-over T20 match)."""
        invalid_overs = _get_count(
            db_conn,
            """
            SELECT COUNT(*)
            FROM clean_deliveries
            WHERE over_number < 0 OR over_number > 19
            """,
        )
        assert invalid_overs == 0, (
            f"Found {invalid_overs} deliveries with invalid over numbers"
        )

    def test_wickets_integrity(self, db_conn: duckdb.DuckDBPyConnection) -> None:
        """Verify that every wicket delivery has a recorded dismissal_kind."""
        invalid_wickets = _get_count(
            db_conn,
            """
            SELECT COUNT(*)
            FROM clean_deliveries
            WHERE is_wicket = TRUE AND dismissal_kind IS NULL
            """,
        )
        assert invalid_wickets == 0, (
            f"Found {invalid_wickets} wickets without dismissal kind"
        )
