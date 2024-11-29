from fastapi import APIRouter
from .endpoints import drivers, sessions, coordinates

api_router = APIRouter()
api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(coordinates.router, prefix="/coordinates", tags=["coordinates"])