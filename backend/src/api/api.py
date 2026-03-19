"""
API module handling router of the app endpoints.
"""

from fastapi import APIRouter
<<<<<<< HEAD
from backend.src.core.settings import settings
=======
from backend.src.core.config import settings
>>>>>>> 01e3a91 (Our single commit)
from backend.src.api.endpoints.app import router as app_router
from backend.src.api.endpoints.hw import router as hw_router


api_router = APIRouter(prefix=settings.FASTAPI.API_STR)

api_router.include_router(app_router, prefix="/apps", tags=["apps"])
api_router.include_router(hw_router, prefix="/hardware", tags=["hardware"])
