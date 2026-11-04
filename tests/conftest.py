"""Global Pytest Configuration and Shared Test Fixtures.

This module sets up:
1. `test_db`: A DuckDB connection configured in read-only mode with guaranteed cleanup.
2. `client`: A FastAPI TestClient for testing HTTP endpoints without launching a live server.
"""

from collections.abc import Generator
from pathlib import Path

import duckdb
from fastapi.testclient import TestClient
import pytest

from ipl_analytics.main import app

# Path to the processed DuckDB database
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "ipl.duckdb"


@pytest.fixture(scope="session")
def test_db_path() -> Path:
    """Provide the absolute path to the processed DuckDB database."""
    assert DB_PATH.exists(), f"Database not found at {DB_PATH}. Run pipeline first."
    return DB_PATH


@pytest.fixture(scope="function")
def db_conn(test_db_path: Path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Yield a read-only DuckDB connection per test and guarantee teardown/cleanup."""
    con = duckdb.connect(database=str(test_db_path), read_only=True)
    try:
        yield con
    finally:
        con.close()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient session for testing HTTP endpoints."""
    with TestClient(app) as test_client:
        yield test_client
