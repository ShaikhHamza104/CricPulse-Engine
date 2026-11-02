from typing import Optional, Self
from pydantic import BaseModel, ConfigDict, Field, model_validator


# Shared config for database/API response models:
# - from_attributes=True: allows ORM / DuckDB row instantiation
# - extra="ignore": prevents crashes when SQL queries include helper columns
#   (e.g., COUNT(*) OVER() AS total_count)
RESPONSE_MODEL_CONFIG = ConfigDict(
    str_strip_whitespace=True,
    from_attributes=True,
    extra="ignore",
)


class PlayerBase(BaseModel):
    """Base class for Player identity.

    Fields:
        player_id: Unique identifier for the player (e.g., "b0512837").
        player_name: Name of the player (e.g., "v kohli").
    """

    model_config = RESPONSE_MODEL_CONFIG

    player_id: str = Field(
        ..., min_length=1, description="Unique identifier for the player"
    )
    player_name: str = Field(
        ..., min_length=1, description="Name of the player"
    )


class BattingStats(BaseModel):
    """Pure batting metrics without player identity fields (used for nesting).

    Fields:
        matches_played: Total matches played (e.g., 200).
        total_runs: Total runs scored (e.g., 5000).
        balls_faced: Total balls faced (e.g., 4000).
        strike_rate: Batting strike rate (e.g., 125.0).
        fours: Total number of fours hit (e.g., 400).
        sixes: Total number of sixes hit (e.g., 100).
    """

    model_config = RESPONSE_MODEL_CONFIG

    matches_played: int = Field(
        ..., ge=0, description="Total matches played by the player"
    )
    total_runs: int = Field(
        ..., ge=0, description="Total runs scored by the player"
    )
    balls_faced: int = Field(
        ..., ge=0, description="Total balls faced by the player"
    )
    strike_rate: float = Field(
        ..., ge=0.0, description="Strike rate of the player"
    )
    fours: int = Field(
        ..., ge=0, description="Total number of fours hit by the player"
    )
    sixes: int = Field(
        ..., ge=0, description="Total number of sixes hit by the player"
    )

    @model_validator(mode="after")
    def validate_batting_invariants(self) -> Self:
        boundary_runs = (self.fours * 4) + (self.sixes * 6)
        if boundary_runs > self.total_runs:
            raise ValueError(
                f"Boundary runs ({boundary_runs}) cannot exceed total_runs ({self.total_runs})."
            )
        if (self.fours + self.sixes) > self.balls_faced:
            raise ValueError(
                "Total boundaries (fours + sixes) cannot exceed balls_faced."
            )
        if self.balls_faced == 0 and self.total_runs > 0:
            raise ValueError("total_runs must be 0 when balls_faced is 0.")
        return self


class BowlingStats(BaseModel):
    """Pure bowling metrics without player identity fields (used for nesting).

    Fields:
        wickets: Total wickets taken (ge=0).
        balls_bowled: Total legal balls bowled (ge=0).
        overs_bowled: Total overs bowled (ge=0.0).
        runs_conceded: Total runs conceded (ge=0).
        economy_rate: Bowling economy rate (ge=0.0).
    """

    model_config = RESPONSE_MODEL_CONFIG

    wickets: int = Field(
        ..., ge=0, description="Total wickets taken by the player"
    )
    balls_bowled: int = Field(
        ..., ge=0, description="Total balls bowled by the player"
    )
    overs_bowled: float = Field(
        ..., ge=0.0, description="Total overs bowled by the player"
    )
    runs_conceded: int = Field(
        ..., ge=0, description="Total runs conceded by the player"
    )
    economy_rate: float = Field(
        ..., ge=0.0, description="Economy rate of the player"
    )

    @model_validator(mode="after")
    def validate_bowling_invariants(self) -> Self:
        # Note: runs_conceded > 0 or wickets > 0 (stumping off a wide) can legally
        # happen with 0 legal balls_bowled, so only overs_bowled is checked here.
        if self.balls_bowled == 0 and self.overs_bowled > 0:
            raise ValueError("overs_bowled must be 0.0 when balls_bowled is 0.")
        return self


class PlayerBattingStats(PlayerBase, BattingStats):
    """Flat player batting model for leaderboards (e.g., Orange Cap) and SQL rows."""


class PlayerBowlingStats(PlayerBase, BowlingStats):
    """Flat player bowling model for leaderboards (e.g., Purple Cap) and SQL rows."""


class PlayerProfile(PlayerBase):
    """Combined player profile model without redundant nested IDs/names.

    Both `batting` and `bowling` may be None for squad members, substitute
    fielders, or players who appeared in a match without batting or bowling.
    """

    batting: Optional[BattingStats] = Field(
        default=None,
        description="Batting statistics of the player (None if player never batted)",
    )
    bowling: Optional[BowlingStats] = Field(
        default=None,
        description="Bowling statistics of the player (None if player never bowled)",
    )


class PaginatedPlayerResponse(BaseModel):
    """Paginated list envelope for GET /players endpoints."""

    model_config = RESPONSE_MODEL_CONFIG

    total: int = Field(..., ge=0, description="Total matching players")
    limit: int = Field(..., ge=1, description="Page size limit")
    offset: int = Field(..., ge=0, description="Page offset")
    items: list[PlayerBase] = Field(
        default_factory=list, description="List of player summaries"
    )