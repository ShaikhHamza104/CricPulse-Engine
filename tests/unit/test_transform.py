"""Unit Tests for Data Transformation & Mapping Logic.

Concepts Taught Here:
1. Pure Function Testing: Testing logic that transforms data without databases or network calls.
2. `@pytest.mark.parametrize`: Running one test function with multiple input/expected combinations.
3. Edge Case Handling: Testing case-insensitivity, whitespace, and unknown inputs.
"""

import pytest

from ipl_analytics.pipelines.transform import (
    TEAM_MAPPING,
    VENUE_CITY_MAP,
    VENUE_MAPPING,
)


class TestFranchiseMapping:
    """Tests verifying team name harmonization and franchise acronym lookups."""

    @pytest.mark.parametrize(
        ("input_alias", "expected_team"),
        [
            ("csk", "chennai super kings"),
            ("mi", "mumbai indians"),
            ("rcb", "royal challengers bengaluru"),
            ("kkr", "kolkata knight riders"),
            ("srh", "sunrisers hyderabad"),
            ("dc", "delhi capitals"),
            ("dd", "delhi capitals"),
            ("rr", "rajasthan royals"),
            ("pbks", "punjab kings"),
            ("kxip", "punjab kings"),
            ("lsg", "lucknow super giants"),
            ("gt", "gujarat titans"),
            ("rps", "rising pune supergiant"),
            ("gl", "gujarat lions"),
            ("pw", "pune warriors"),
            ("ktk", "kochi tuskers kerala"),
            ("dch", "deccan chargers"),
        ],
    )
    def test_franchise_alias_resolution(
        self, input_alias: str, expected_team: str
    ) -> None:
        """Verify standard IPL acronyms resolve to canonical franchise names."""
        clean_input = input_alias.strip().lower()
        resolved_name = TEAM_MAPPING.get(clean_input, clean_input)
        assert resolved_name == expected_team

    @pytest.mark.parametrize(
        ("historical_name", "current_name"),
        [
            ("delhi daredevils", "delhi capitals"),
            ("kings xi punjab", "punjab kings"),
            ("royal challengers bangalore", "royal challengers bengaluru"),
            ("rising pune supergiants", "rising pune supergiant"),
        ],
    )
    def test_historical_franchise_renaming(
        self, historical_name: str, current_name: str
    ) -> None:
        """Verify older franchise identities map to their modern equivalent."""
        assert TEAM_MAPPING.get(historical_name) == current_name

    def test_unknown_team_preserves_original(self) -> None:
        """Ensure unmapped team names pass through unharmed as fallback."""
        unknown_team = "somerset county"
        result = TEAM_MAPPING.get(unknown_team, unknown_team)
        assert result == unknown_team


class TestVenueMapping:
    """Tests verifying historical stadium harmonization."""

    @pytest.mark.parametrize(
        ("raw_venue", "canonical_venue"),
        [
            ("feroz shah kotla", "arun jaitley stadium"),
            ("arun jaitley stadium, delhi", "arun jaitley stadium"),
            ("wankhede stadium, mumbai", "wankhede stadium"),
            ("eden gardens, kolkata", "eden gardens"),
            ("m chinnaswamy stadium, bengaluru", "m chinnaswamy stadium"),
            ("sardar patel stadium, motera", "narendra modi stadium, ahmedabad"),
            ("subrata roy sahara stadium", "maharashtra cricket association stadium"),
        ],
    )
    def test_venue_normalization(self, raw_venue: str, canonical_venue: str) -> None:
        """Verify stadium variations correctly standardize to unified names."""
        assert VENUE_MAPPING.get(raw_venue) == canonical_venue

    def test_venue_city_backfill(self) -> None:
        """Verify missing cities for international venues are correctly populated."""
        assert VENUE_CITY_MAP.get("dubai international cricket stadium") == "dubai"
        assert VENUE_CITY_MAP.get("sharjah cricket stadium") == "sharjah"
