from fastapi import APIRouter
from ipl_analytics.api.v1.endpoints import analytics, matches, players

api_router = APIRouter()
api_router.include_router(matches.router)
api_router.include_router(players.router)
api_router.include_router(analytics.router)