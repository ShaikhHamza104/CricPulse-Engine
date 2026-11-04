"""API Endpoint Tests for Matches & Health Checks.

Concepts Taught Here:
1. FastAPI TestClient: Testing HTTP requests and responses in-memory without running a server.
2. HTTP Status Codes: Verifying 200 (OK), 404 (Not Found), and 422 (Validation Error).
3. Query Parameters: Testing URL filters (`?season=2024&limit=10`).
4. Production Headers: Testing middleware headers (`X-Request-ID`, `X-Process-Time`).
"""

from fastapi.testclient import TestClient


class TestSystemHealthEndpoints:
    """Tests verifying server health and database connectivity."""

    def test_health_check(self, client: TestClient) -> None:
        """Verify the /health endpoint returns 200 and online status."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "online"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

        # Verify OWASP and telemetry headers set by custom middleware
        assert "x-request-id" in response.headers
        assert "x-process-time" in response.headers

    def test_db_health_check(self, client: TestClient) -> None:
        """Verify /db-health performs an active query without connection leaks."""
        response = client.get("/db-health")
        assert response.status_code == 200

        data = response.json()
        assert data["database"] == "DuckDB"
        assert data["status"] == "connected"
        assert data["alive"] is True


class TestMatchesAPI:
    """Tests verifying match catalog, filtering, pagination, and detail routes."""

    def test_list_matches_default_pagination(self, client: TestClient) -> None:
        """Verify GET /api/v1/matches/ returns paginated match records."""
        response = client.get("/api/v1/matches/")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] > 1000
        assert len(data["items"]) <= 20  # Default limit is 20

    def test_list_matches_filter_by_season(self, client: TestClient) -> None:
        """Verify filtering matches by season via query parameter ?season=2024."""
        response = client.get("/api/v1/matches/", params={"season": 2024, "limit": 10})
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 71
        assert len(data["items"]) == 10
        for match in data["items"]:
            assert match["season"] == 2024

    def test_list_matches_filter_by_team_alias(self, client: TestClient) -> None:
        """Verify filtering matches by franchise alias ?team=CSK."""
        response = client.get("/api/v1/matches/", params={"team": "CSK", "limit": 5})
        assert response.status_code == 200

        data = response.json()
        assert data["total"] > 200
        assert len(data["items"]) == 5

    def test_get_match_seasons(self, client: TestClient) -> None:
        """Verify GET /api/v1/matches/seasons returns all distinct IPL years."""
        response = client.get("/api/v1/matches/seasons")
        assert response.status_code == 200

        data = response.json()
        assert "seasons" in data
        seasons = data["seasons"]
        assert isinstance(seasons, list)
        assert 2008 in seasons
        assert 2024 in seasons

    def test_get_match_by_id_success(self, client: TestClient) -> None:
        """Verify GET /api/v1/matches/{match_id} returns detailed match record."""
        # Use first match from 2024 final: 1426312
        response = client.get("/api/v1/matches/1426312")
        assert response.status_code == 200

        match = response.json()
        assert match["match_id"] == 1426312
        assert match["season"] == 2024
        assert "venue" in match
        assert "winner" in match

    def test_get_match_by_id_not_found(self, client: TestClient) -> None:
        """Concept: Verifying that requesting an invalid match ID returns HTTP 404."""
        response = client.get("/api/v1/matches/999999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_invalid_query_parameter_validation(self, client: TestClient) -> None:
        """Concept: Verifying that FastAPI Pydantic validation rejects bad types with HTTP 422."""
        # Passing text for season where an integer is expected
        response = client.get("/api/v1/matches/", params={"season": "not-a-year"})
        assert response.status_code == 422
