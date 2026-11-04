"""Unit Tests for Cricket Domain Calculations & Analytics Logic.

Concepts Taught Here:
1. Domain Mathematics: Testing custom business/cricket logic in isolation.
2. `pytest.approx`: Safe floating-point comparison (avoiding IEEE 754 precision issues).
3. `pytest.raises`: Asserting that invalid data correctly raises expected exceptions.
4. Boundary/Edge Testing: Handling 0 balls, division by zero, and maximum values.
"""

from pydantic import ValidationError
import pytest

from ipl_analytics.schemas.player import BattingStats


# --- Domain Helper Functions for Cricket Mathematics ---
def calculate_cricket_overs(balls_bowled: int) -> float:
    """Convert total legal deliveries into standard cricket overs notation.

    Formula: (balls // 6) + ((balls % 6) / 10.0)
    Example: 7 balls -> 1.1 overs (1 over + 1 ball)
    """
    if balls_bowled < 0:
        raise ValueError("Deliveries cannot be negative")
    completed_overs = balls_bowled // 6
    remaining_balls = balls_bowled % 6
    return completed_overs + (remaining_balls / 10.0)


def calculate_strike_rate(runs: int, balls_faced: int) -> float:
    """Calculate batting strike rate (runs per 100 balls faced).

    Protects against ZeroDivisionError when balls_faced == 0.
    """
    if balls_faced <= 0:
        return 0.0
    return round((runs * 100.0) / balls_faced, 2)


def calculate_economy_rate(runs_conceded: int, balls_bowled: int) -> float:
    """Calculate bowling economy rate (average runs conceded per 6-ball over).

    Formula: runs_conceded / (balls_bowled / 6.0)
    Protects against ZeroDivisionError when balls_bowled == 0.
    """
    if balls_bowled <= 0:
        return 0.0
    overs_exact = balls_bowled / 6.0
    return round(runs_conceded / overs_exact, 2)


def calculate_batting_average(runs: int, dismissals: int) -> float | None:
    """Calculate batting average (runs scored per dismissal).

    In official cricket rules, if a batter was never dismissed (dismissals == 0),
    their batting average is undefined (None / not out).
    """
    if dismissals <= 0:
        return None
    return round(runs / dismissals, 2)


class TestCricketOversNotation:
    """Tests ensuring cricket overs notation strictly conforms to cricket laws."""

    @pytest.mark.parametrize(
        ("balls", "expected_overs"),
        [
            (0, 0.0),
            (1, 0.1),
            (2, 0.2),
            (3, 0.3),
            (4, 0.4),
            (5, 0.5),
            (6, 1.0),  # 6 balls complete an over, rolls over to 1.0!
            (7, 1.1),
            (11, 1.5),
            (12, 2.0),
            (120, 20.0),  # Full 20 overs in a T20 match
            (3631, 605.1),  # Bumrah's career deliveries
        ],
    )
    def test_overs_decimal_representation(
        self, balls: int, expected_overs: float
    ) -> None:
        """Verify balls are converted to standard (completed_overs.remaining_balls)."""
        overs = calculate_cricket_overs(balls)
        # Using pytest.approx to avoid floating point precision quirks
        assert overs == pytest.approx(expected_overs, abs=1e-4)

    def test_overs_decimal_part_is_strictly_between_0_and_5(self) -> None:
        """CRITICAL DOMAIN RULE: Overs decimal part can NEVER be .6, .7, .8, or .9."""
        for balls in range(0, 300):
            overs = calculate_cricket_overs(balls)
            overs_str = f"{overs:.1f}"
            decimal_part = int(overs_str.split(".")[1])
            msg = f"Illegal cricket overs value: {overs} from {balls} balls"
            assert 0 <= decimal_part <= 5, msg

    def test_negative_balls_raises_value_error(self) -> None:
        """Concept: Using `pytest.raises` to verify exception handling."""
        with pytest.raises(ValueError, match="Deliveries cannot be negative"):
            calculate_cricket_overs(-1)


class TestBattingMetrics:
    """Tests verifying batting calculations (Strike Rate & Batting Average)."""

    @pytest.mark.parametrize(
        ("runs", "balls", "expected_sr"),
        [
            (100, 50, 200.0),  # 200 strike rate (century in 50 balls)
            (50, 40, 125.0),
            (33, 22, 150.0),
            (0, 10, 0.0),  # 0 runs in 10 balls
            (50, 0, 0.0),  # Division by zero protection (0 balls faced)
        ],
    )
    def test_strike_rate_calculation(
        self, runs: int, balls: int, expected_sr: float
    ) -> None:
        """Verify strike rate calculation and zero-balls division safety."""
        sr = calculate_strike_rate(runs, balls)
        assert sr == pytest.approx(expected_sr, abs=1e-2)

    def test_batting_average_for_not_out_batter(self) -> None:
        """Verify that a batter who is not out (0 dismissals) returns None."""
        avg = calculate_batting_average(runs=150, dismissals=0)
        assert avg is None

    def test_batting_average_calculation(self) -> None:
        """Verify standard batting average calculation."""
        avg = calculate_batting_average(runs=9336, dismissals=231)
        assert avg == pytest.approx(40.42, abs=1e-2)


class TestBowlingMetrics:
    """Tests verifying bowling economy rate and overs calculations."""

    @pytest.mark.parametrize(
        ("runs_conceded", "balls_bowled", "expected_econ"),
        [
            (24, 24, 6.0),  # 4 overs (24 balls) for 24 runs -> Economy 6.00
            (30, 24, 7.5),  # 4 overs for 30 runs -> Economy 7.50
            (4441, 3631, 7.34),  # Bumrah career economy (4441 runs / 605.167 overs)
            (20, 0, 0.0),  # Division by zero protection (0 balls bowled)
        ],
    )
    def test_economy_rate_calculation(
        self, runs_conceded: int, balls_bowled: int, expected_econ: float
    ) -> None:
        """Verify economy rate handles completed and partial overs accurately."""
        econ = calculate_economy_rate(runs_conceded, balls_bowled)
        assert econ == pytest.approx(expected_econ, abs=1e-2)


class TestSchemaValidationWithPytest:
    """Tests showing how to validate Pydantic models with pytest."""

    def test_valid_batting_stats_schema(self) -> None:
        """Verify BattingStats model accepts valid cricket data."""
        stats = BattingStats(
            matches_played=275,
            total_runs=9336,
            balls_faced=6926,
            strike_rate=134.8,
            fours=844,
            sixes=316,
            batting_average=40.42,
        )
        assert stats.total_runs == 9336
        assert stats.strike_rate == 134.8

    def test_invalid_schema_type_raises_validation_error(self) -> None:
        """Ensure Pydantic rejects invalid types using pytest.raises(ValidationError)."""
        with pytest.raises(ValidationError):
            # Passing invalid data payload to model_validate
            BattingStats.model_validate(
                {
                    "matches_played": 10,
                    "total_runs": "not-a-number",
                    "balls_faced": 50,
                    "strike_rate": 100.0,
                    "fours": 4,
                    "sixes": 1,
                }
            )
