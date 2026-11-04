
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ipl_analytics.api.dependencies import get_analytics_repo
from ipl_analytics.pipelines.transform import TEAM_MAPPING
from ipl_analytics.repositories.analytics_repository import AnalyticsRepository
from ipl_analytics.schemas.analytics import (
    HeadToHeadResponse,
    TossImpactResponse,
    VenueStatsResponse,
)
from ipl_analytics.schemas.player import (
    PlayerBattingStats,
    PlayerBowlingStats,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/head-to-head", response_model=HeadToHeadResponse)
def head_to_head(
    team1: str = Query(..., description="First team name (e.g. 'Chennai Super Kings')"),
    team2: str = Query(..., description="Second team name (e.g. 'Mumbai Indians')"),
    repo: AnalyticsRepository = Depends(get_analytics_repo),
):
    """
    Get historical head-to-head rivalry statistics between two teams.
    """
    raw_t1 = team1.strip().lower()
    raw_t2 = team2.strip().lower()
    norm1 = TEAM_MAPPING.get(raw_t1, raw_t1)
    norm2 = TEAM_MAPPING.get(raw_t2, raw_t2)

    if norm1 == norm2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="team1 and team2 must be two different teams.",
        )
    return repo.get_head_to_head(team1=team1, team2=team2)


@router.get("/toss-impact", response_model=TossImpactResponse)
def toss_impact(
    repo: AnalyticsRepository = Depends(get_analytics_repo),
):
    """
    Get toss decision impact analysis across all historical matches.
    """
    return repo.get_toss_impact()


@router.get("/venue", response_model=VenueStatsResponse)
def venue_stats(
    venue: str = Query(..., description="Stadium venue name (e.g. 'Wankhede Stadium')"),
    repo: AnalyticsRepository = Depends(get_analytics_repo),
):
    """
    Get stadium scoring records, averages, and total matches played.
    """
    stats = repo.get_venue_stats(venue=venue)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venue '{venue}' not found.",
        )
    return stats


@router.get("/orange-cap", response_model=list[PlayerBattingStats])
def orange_cap(
    season: int | None = Query(
        None, description="Filter by IPL season year (e.g. 2023)"
    ),
    limit: int = Query(10, ge=1, le=100, description="Leaderboard size (default 10)"),
    repo: AnalyticsRepository = Depends(get_analytics_repo),
):
    """
    Get the top run-scorers leaderboard (Orange Cap) for all-time or a specific season.
    """
    return repo.get_orange_cap(season=season, limit=limit)


@router.get("/purple-cap", response_model=list[PlayerBowlingStats])
def purple_cap(
    season: int | None = Query(
        None, description="Filter by IPL season year (e.g. 2023)"
    ),
    limit: int = Query(10, ge=1, le=100, description="Leaderboard size (default 10)"),
    repo: AnalyticsRepository = Depends(get_analytics_repo),
):
    """
    Get the top wicket-takers leaderboard (Purple Cap) adhering to official bowler rules.
    """
    return repo.get_purple_cap(season=season, limit=limit)
