import datetime
import uuid
from http import HTTPStatus
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import Base
from models.models import Place
from models.schemas import PlaceInput, PlaceEdit
from fastapi import HTTPException
from services.base import BaseService


class PlaceService(BaseService):
    model: Base = Place
    instance: str = 'place'

    @classmethod
    async def create(
            cls,
            session: AsyncSession,
            data: PlaceInput,
            user_id: str | uuid.UUID
    ) -> Place:
        cls.validate(data)
        return await super().create(session, data, user_id)

    @classmethod
    async def edit(
            cls,
            session: AsyncSession,
            new_data: PlaceEdit,
            _id: uuid.UUID,
            user_id: uuid.UUID
    ) -> Optional[Place]:
        db_place = await cls.validate_host(session, _id, user_id)
        cls.validate(new_data)

        db_place.location = new_data.location
        db_place.capacity = new_data.capacity
        db_place.open = new_data.open
        db_place.close = new_data.close
        return await cls.save(session, db_place)

    @classmethod
    def validate(cls, data: PlaceInput | PlaceEdit):
        cls.validate_capacity(data.capacity)
        cls.validate_time(data.open, data.close)

    @classmethod
    def validate_capacity(cls, capacity: int):
        if capacity <= 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Capacity of the place can't be {capacity}, "
                       f"should be > 0"
            )

    @classmethod
    def validate_time(cls, open_time: datetime.time, close_time: datetime.time):
        if open_time >= close_time:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Close hours can't be less than open hours: "
                       f"{close_time} <= {open_time}"
            )
