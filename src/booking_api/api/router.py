from fastapi.routing import APIRouter

from booking_api.api.v1 import events, movies, locations, bookings

router = APIRouter(prefix="/v1")

router.include_router(events.router)
router.include_router(locations.router)
router.include_router(movies.router)
router.include_router(bookings.router)
