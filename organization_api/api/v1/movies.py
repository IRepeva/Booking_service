import uuid
from typing import List

from fastapi import APIRouter

FREE_MOVIES = [uuid.uuid4() for _ in range(10)]

router = APIRouter()


@router.get(
    '/free_movies',
    response_model=List[uuid.UUID],
    summary="Get list of free movies"
)
async def free_movies() -> List[uuid.UUID]:
    return FREE_MOVIES
