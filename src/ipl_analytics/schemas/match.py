from datetime import date as dt_date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class MatchBase(BaseModel):
    """Base class for Match data model."""
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    match_id: int = Field(..., description="Unique identifier for the match")
    season: int = Field(..., description="Season of the match")
    date: dt_date = Field(..., description="Calendar date of the match")
    team1: str = Field(..., description="Name of the first team")
    team2: str = Field(..., description="Name of the second team")


class MatchSummary(MatchBase):
    """Class for Match summary data model, extending MatchBase."""
    winner: Optional[str] = Field(
        None, description="Name of the winning team (optional due to rain washouts)"
    )
    outcome_status: Optional[str] = Field(
        None, description="Status of the match outcome (e.g., completed, cancelled, etc.)"
    )


class MatchDetail(MatchSummary):
    """Class for detailed Match data model, extending MatchSummary."""
    venue: str = Field(..., description="Venue of the match")
    city: str = Field(..., description="City where the match was played")
    toss_winner: Optional[str] = Field(
        None, description="Team that won the toss (optional if abandoned before toss)"
    )
    toss_decision: Optional[Literal["bat", "field"]] = Field(
        None, description="Decision made by the toss-winning team (bat/field)"
    )
    year: int = Field(..., ge=1877, le=2100, description="Year of the match")
    month: int = Field(..., ge=1, le=12, description="Month of the match (1-12)")

    @model_validator(mode="after")
    def check_year_and_month_match_date(self) -> "MatchDetail":
        """Ensure year and month fields match the parsed date object."""
        if self.year != self.date.year or self.month != self.date.month:
            raise ValueError(
                f"year ({self.year}) and month ({self.month}) do not match date ({self.date})"
            )
        return self


class MatchFilterParams(BaseModel):
    """Class for filtering Match query parameters."""
    season: Optional[int] = Field(None, description="Season to filter matches (optional)")
    team: Optional[str] = Field(None, description="Team name to filter matches (optional)")
    venue: Optional[str] = Field(None, description="Venue substring to filter matches (optional)")
    city: Optional[str] = Field(None, description="City to filter matches (optional)")
    date: Optional[dt_date] = Field(None, description="Date to filter matches (optional)")
    limit: int = Field(
        20, ge=1, le=100, description="Number of records to return (page size)"
    )
    offset: int = Field(
        0, ge=0, description="Number of records to skip (page skip)"
    )


class PaginatedMatchResponse(BaseModel):
    """Class for paginated Match list responses."""
    total: int = Field(..., ge=0, description="Total matches matching filter")
    limit: int = Field(..., ge=1, description="Page limit applied")
    offset: int = Field(..., ge=0, description="Page offset applied")
    items: list[MatchSummary] = Field(..., description="List of match summaries")