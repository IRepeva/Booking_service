import datetime
import uuid
from typing import Optional

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from booking_api.models.schemas import (
    LocationEdit, LocationInput, SeatInput
)
from booking_api.services.base import BaseService
from booking_api.utils.exceptions import BadRequestException
from db.tables import Location, Seat
from db.tables.base import Base


class LocationService(BaseService):
    model: Base = Location
    instance: str = "location"

    @classmethod
    async def create(
            cls, session: AsyncSession, data: LocationInput,
            user_id: uuid.UUID, extra: dict = None, commit: bool = True
    ) -> Location:
        await cls.validate(data)
        return await super().create(session, data, user_id, commit=False)

    @classmethod
    async def delete(
            cls, session: AsyncSession, _id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Location]:

        await session.execute(delete(Seat).where(Seat.location_id == _id, ))
        return await super().delete(session, _id, user_id)

    @classmethod
    async def prepare_seats_data(
            cls, seats_data: list[SeatInput], location_id: uuid.UUID
    ):
        seats_data = [seat.dict() for seat in seats_data]
        for seat in seats_data:
            seat.update({"id": uuid.uuid4(), "location_id": location_id})
        return seats_data

    @classmethod
    async def rename(
            cls, session: AsyncSession, new_name: str, _id: uuid.UUID,
            user_id: uuid.UUID
    ) -> Optional[Location]:
        db_instance = await cls.validate_user(session, _id, user_id)
        await cls.validate_name(session, new_name)

        db_instance.name = new_name
        return await cls.save(session, db_instance)

    @classmethod
    async def validate(cls, data: LocationInput | LocationEdit, *args, **kwargs):
        cls.validate_capacity(data.capacity)
        cls.validate_time(data.open, data.close)

    @classmethod
    def validate_capacity(cls, capacity: int):
        if capacity <= 0:
            raise BadRequestException(
                message=f"Capacity of the location can't be {capacity},"
                        f" should be > 0",
            )

    @classmethod
    def validate_time(cls, open_time: datetime.time, close_time: datetime.time):
        if open_time >= close_time:
            raise BadRequestException(
                message=f"Close hours can't be less than open hours:"
                        f" {close_time} <= {open_time}",
            )

    @classmethod
    async def validate_name(cls, session: AsyncSession, name: str):
        db_location = await cls.get_first(
            session, filters=(cls.model.name == name,)
        )
        if db_location:
            raise BadRequestException(
                message=f"Location with name '{name}' already exists"
            )
