from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ipl_analytics.api.dependencies import get_player_repo
from ipl_analytics.repositories.player_repository import PlayerRepository
from ipl_analytics.schemas.player import PaginatedPlayerResponse, PlayerProfile

router = APIRouter(
    prefix="/players",
    tags=["players"]
)
@router.get("", response_model=PaginatedPlayerResponse)
def list_players(
        search: Optional[str] = Query(None, description="Search player by name"),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        repo: PlayerRepository = Depends(get_player_repo)
):
    """
    List players with optional search and pagination.
    """
    return repo.list_players(search=search, limit=limit, offset=offset)

@router.get("/{player_id}", response_model=PlayerProfile)
def get_player(player_id: str, repo: PlayerRepository = Depends(get_player_repo)):
    """
    Get player career profile by player ID.
    """
    player = repo.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
