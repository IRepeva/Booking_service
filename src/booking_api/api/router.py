from fastapi.routing import APIRouter
from v1 import events, movies, places

router = APIRouter(prefix="v1/")

router.include_router(events.router)
router.include_router(places.router)
router.include_router(movies.router)
