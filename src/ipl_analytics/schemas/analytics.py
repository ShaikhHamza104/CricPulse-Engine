from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Security & resilience config for analytics response models:
# - extra="ignore": Strips unmodeled SQL columns so internal DB fields are never leaked
# - allow_inf_nan=False: Rejects NaN / Infinity floats (e.g. from SQL division by zero)
#   that would otherwise crash FastAPI's JSON serializer with a 500 error
ANALYTICS_MODEL_CONFIG = ConfigDict(
    str_strip_whitespace=True,
    from_attributes=True,
    extra="ignore",
    allow_inf_nan=False,
)


class HeadToHeadResponse(BaseModel):
    """Response model for head-to-head match statistics between two teams.
    Fields:
        team1: Name of the first team (e.g., "Mumbai Indians").
        team2: Name of the second team (e.g., "Chennai Super Kings").
        total_matches: Total matches played between the two teams.
        team1_wins: Total wins by team1 against team2.
        team2_wins: Total wins by team2 against team1.
        ties_or_no_result: Total matches that ended in a tie or no result.
        win_percentage_team1: Win percentage of team1 against team2.
        win_percentage_team2: Win percentage of team2 against team1.
    """

    model_config = ANALYTICS_MODEL_CONFIG

    team1: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the first team",
    )
    team2: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the second team",
    )
    total_matches: int = Field(
        ...,
        ge=0,
        description="Total matches played between the two teams",
    )
    team1_wins: int = Field(
        ...,
        ge=0,
        description="Total wins by team1 against team2",
    )
    team2_wins: int = Field(
        ...,
        ge=0,
        description="Total wins by team2 against team1",
    )
    ties_or_no_result: int = Field(
        ...,
        ge=0,
        description="Total matches that ended in a tie or no result",
    )
    win_percentage_team1: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Win percentage of team1 against team2",
    )
    win_percentage_team2: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Optional win percentage of team2 against team1",
    )

    @model_validator(mode="after")
    def validate_head_to_head_invariants(self) -> Self:
        if self.team1.casefold() == self.team2.casefold():
            raise ValueError("team1 and team2 must be two different teams.")

        counted_matches = self.team1_wins + self.team2_wins + self.ties_or_no_result
        if counted_matches != self.total_matches:
            raise ValueError(
                f"Sum of outcomes ({counted_matches}) must equal "
                f"total_matches ({self.total_matches})."
            )

        if self.total_matches == 0 and (
            self.win_percentage_team1 > 0.0 or (self.win_percentage_team2 or 0.0) > 0.0
        ):
            raise ValueError("Win percentages must be 0.0 when total_matches is 0.")

        return self


class TossImpactResponse(BaseModel):
    """Response model for toss impact statistics across matches."""

    model_config = ANALYTICS_MODEL_CONFIG

    total_matches: int = Field(
        ...,
        ge=0,
        description="Total matches analyzed for toss impact",
    )
    toss_winner_match_wins: int = Field(
        ...,
        ge=0,
        description="Total matches won by the toss-winning team",
    )
    toss_win_match_win_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of matches won by the toss-winning team",
    )
    chose_field_count: int = Field(
        ...,
        ge=0,
        description="Total matches where the toss-winning team chose to field first",
    )
    chose_bat_count: int = Field(
        ...,
        ge=0,
        description="Total matches where the toss-winning team chose to bat first",
    )

    @model_validator(mode="after")
    def validate_toss_invariants(self) -> Self:
        if self.toss_winner_match_wins > self.total_matches:
            raise ValueError("toss_winner_match_wins cannot exceed total_matches.")

        if (self.chose_field_count + self.chose_bat_count) > self.total_matches:
            raise ValueError(
                "Sum of chose_field_count and chose_bat_count cannot exceed total_matches."
            )

        if self.total_matches == 0 and self.toss_win_match_win_pct > 0.0:
            raise ValueError(
                "toss_win_match_win_pct must be 0.0 when total_matches is 0."
            )

        return self


class VenueStatsResponse(BaseModel):
    """Response model for venue-specific match statistics."""

    model_config = ANALYTICS_MODEL_CONFIG

    venue: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the venue",
    )
    city: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="City where the venue is located (nullable in Cricsheet data)",
    )
    total_matches: int = Field(
        ...,
        ge=0,
        description="Total matches played at the venue",
    )
    avg_first_innings_score: float = Field(
        ...,
        ge=0.0,
        description="Average score in the first innings at the venue",
    )
    highest_total: int = Field(
        ...,
        ge=0,
        description="Highest total score recorded at the venue",
    )

    @model_validator(mode="after")
    def validate_venue_invariants(self) -> Self:
        if self.total_matches > 0 and self.avg_first_innings_score > self.highest_total:
            raise ValueError(
                f"avg_first_innings_score ({self.avg_first_innings_score}) "
                f"cannot exceed highest_total ({self.highest_total})."
            )

        if self.total_matches == 0 and (
            self.avg_first_innings_score > 0.0 or self.highest_total > 0
        ):
            raise ValueError(
                "avg_first_innings_score and highest_total must be 0 when total_matches is 0."
            )

        return self
