from typing import Optional
from fastapi import APIRouter, Depends,HTTPException, Query
from  ipl_analytics.api.dependencies import get_match_repo
from ipl_analytics.repositories.match_repository import MatchRepository
from ipl_analytics.schemas.match import MatchDetail,PaginatedMatchResponse

router = APIRouter(
    prefix="/matches",
    tags=["matches"])

@router.get("/seasons")
def get_seasons(match_repo:MatchRepository = Depends(get_match_repo)):
    """
    Get all the seasons available in the database.
    """
    seasons = match_repo.get_seasons()
    return {"seasons": seasons}

@router.get("/{match_id}", response_model=MatchDetail)
def get_match(match_id: int, match_repo: MatchRepository = Depends(get_match_repo)):
    """
    Get match details by match ID.
    """
    match = match_repo.get_by_id(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

# /matches
@router.get("/", response_model=PaginatedMatchResponse)
def list_matches(
        season: Optional[int] = Query(None, description="Filter by season"),
        team: Optional[str] = Query(None, description="Filter by team name"),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        repo: MatchRepository = Depends(get_match_repo),
):
    """
    List matches with optional filtering by season and pagination.
    """
    return  repo.list_matches(season=season, team=team, limit=limit, offset=offset)
