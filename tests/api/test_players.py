"""API Endpoint Tests for Players and Analytics Routes.

Concepts Taught Here:
1. REST API Testing: Querying resources by ID and search parameters.
2. Analytics Endpoint Testing: Verifying statistical computations via HTTP.
3. Path Parameter Validation: Verifying HTTP 404 on missing records.
4. Schema Completeness: Checking that JSON responses contain expected fields.
"""

from fastapi.testclient import TestClient


class TestPlayersAPI:
    """Tests verifying player search, listing, and career profile endpoints."""

    def test_list_players_search_kohli(self, client: TestClient) -> None:
        """Verify GET /api/v1/players/?search=Kohli returns matching player profiles."""
        response = client.get("/api/v1/players/", params={"search": "Kohli"})
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 2

        names = [p["player_name"] for p in data["items"]]
        assert "v kohli" in names

    def test_get_player_profile_by_id_success(self, client: TestClient) -> None:
        """Verify GET /api/v1/players/{player_id} returns full batting & bowling stats."""
        # Virat Kohli's ID
        response = client.get("/api/v1/players/ba607b88")
        assert response.status_code == 200

        profile = response.json()
        assert profile["player_id"] == "ba607b88"
        assert profile["player_name"] == "v kohli"

        # Verify Batting stats
        batting = profile["batting"]
        assert batting is not None
        assert batting["total_runs"] > 9000
        assert batting["strike_rate"] > 130.0

    def test_get_player_profile_not_found(self, client: TestClient) -> None:
        """Verify GET /api/v1/players/{player_id} returns 404 for unknown player ID."""
        response = client.get("/api/v1/players/invalid_player_id_999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAnalyticsAPI:
    """Tests verifying analytics endpoints (H2H, Orange Cap, Purple Cap, Toss, Venue)."""

    def test_head_to_head_api_with_aliases(self, client: TestClient) -> None:
        """Verify GET /api/v1/analytics/head-to-head handles team acronyms (CSK vs RCB)."""
        response = client.get(
            "/api/v1/analytics/head-to-head",
            params={"team1": "CSK", "team2": "RCB"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["team1"] == "chennai super kings"
        assert data["team2"] == "royal challengers bengaluru"
        assert data["total_matches"] == 35
        assert data["team1_wins"] == 21
        assert data["team2_wins"] == 14
        assert data["win_percentage_team1"] == 60.0

    def test_orange_cap_api(self, client: TestClient) -> None:
        """Verify GET /api/v1/analytics/orange-cap returns top run scorers for a season."""
        response = client.get(
            "/api/v1/analytics/orange-cap",
            params={"season": 2024, "limit": 3},
        )
        assert response.status_code == 200

        leaders = response.json()
        assert len(leaders) == 3
        top_batsman = leaders[0]
        assert top_batsman["player_name"] == "v kohli"
        assert top_batsman["total_runs"] > 700

    def test_purple_cap_api(self, client: TestClient) -> None:
        """Verify GET /api/v1/analytics/purple-cap returns top wicket takers for a season."""
        response = client.get(
            "/api/v1/analytics/purple-cap",
            params={"season": 2024, "limit": 3},
        )
        assert response.status_code == 200

        leaders = response.json()
        assert len(leaders) == 3
        assert leaders[0]["wickets"] >= 20

    def test_toss_impact_api(self, client: TestClient) -> None:
        """Verify GET /api/v1/analytics/toss-impact returns win percentage metrics."""
        response = client.get("/api/v1/analytics/toss-impact")
        assert response.status_code == 200

        data = response.json()
        assert data["total_matches"] > 1000
        assert "toss_win_match_win_pct" in data

    def test_venue_stats_api_success(self, client: TestClient) -> None:
        """Verify GET /api/v1/analytics/venue calculates venue historical stats."""
        response = client.get(
            "/api/v1/analytics/venue",
            params={"venue": "Wankhede Stadium, Mumbai"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["venue"] == "wankhede stadium"
        assert data["total_matches"] > 100
        assert data["avg_first_innings_score"] > 140.0

    def test_venue_stats_api_not_found(self, client: TestClient) -> None:
        """Verify GET /api/v1/analytics/venue returns 404 for unknown stadium."""
        response = client.get(
            "/api/v1/analytics/venue",
            params={"venue": "unknown stadium nowhere"},
        )
        assert response.status_code == 404
