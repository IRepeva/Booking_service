import uuid
from typing import List
from uuid import UUID

from fastapi import APIRouter

FREE_MOVIES = [
    UUID("b4c0bba7-02fc-442a-83df-3e5884571c97"),
    UUID("05ccc1c0-1d65-4962-9947-415d4be93eab"),
    UUID("f4ccf1fc-43a4-4504-b357-56d863a0ad52"),
    UUID("84245d4c-fb50-46e1-9a38-c0ca01717750"),
    UUID("d49e71c2-abda-4873-8e07-0de3e8d640ef"),
    UUID("ada1a9f8-f000-4c31-8bc2-8ca532dde10a"),
    UUID("659ed9ef-525a-449d-8d2e-60d72e893c54"),
    UUID("0edaab9e-ddae-4b31-a604-0e8c06415976"),
    UUID("2355806b-6486-4db4-82be-9d78e311be4c"),
    UUID("1537dde8-daae-4e70-8150-093e7df157e9"),
]

router = APIRouter(prefix="/movies")


@router.get(
    "/free_movies", response_model=List[uuid.UUID], summary="Get list of free movies"
)
async def free_movies() -> List[uuid.UUID]:
    return FREE_MOVIES
