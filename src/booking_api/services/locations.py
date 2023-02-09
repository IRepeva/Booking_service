import datetime
import uuid
from http import HTTPStatus
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from booking_api.models.schemas import LocationEdit, LocationInput, SeatInput
from booking_api.services.base import BaseService
from db.tables import Location, Seat
from db.utils.postgres import Base


class LocationService(BaseService):
    model: Base = Location
    instance: str = "location"

    @classmethod
    async def create(
            cls, session: AsyncSession,
            data: LocationInput,
            user_id: str | uuid.UUID,
            model: Base = None,
    ) -> Location:
        cls.validate(data)
        return await super().create(session, data, user_id, commit=False)

    @classmethod
    async def create_seat(
            cls, session: AsyncSession,
            data: SeatInput,
            location_id: uuid.UUID
    ):
        data = data.dict() if data else {}
        data.update({"location_id": location_id})

        data.update({'id': uuid.uuid4()})
        instance = Seat(**data)
        await cls.save(session, instance)

    @classmethod
    async def create_default_seats(cls, session: AsyncSession, location: Location):
        data = {'location_id': location.id}
        for seat_id in [uuid.uuid4() for _ in range(location.capacity)]:
            data.update({'id': seat_id})
            instance = Seat(**data)
            await cls.save(session, instance)

    @classmethod
    async def edit(
        cls,
        session: AsyncSession,
        new_data: LocationEdit,
        _id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Location]:
        db_location = await cls.validate_host(session, _id, user_id)
        cls.validate(new_data)

        db_location.coordinates = new_data.coordinates
        db_location.capacity = new_data.capacity
        db_location.open = new_data.open
        db_location.close = new_data.close
        return await cls.save(session, db_location)

    @classmethod
    async def rename(
        cls, session: AsyncSession, new_name: str, _id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Location]:
        db_instance = await cls.validate_host(session, _id, user_id)
        await cls.validate_name(session, new_name)

        db_instance.name = new_name
        return await cls.save(session, db_instance)

    @classmethod
    def validate(cls, data: LocationInput | LocationEdit):
        cls.validate_capacity(data.capacity)
        cls.validate_time(data.open, data.close)

    @classmethod
    def validate_capacity(cls, capacity: int):
        if capacity <= 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Capacity of the location can't be {capacity}, should be > 0",
            )

    @classmethod
    def validate_time(cls, open_time: datetime.time, close_time: datetime.time):
        if open_time >= close_time:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Close hours can't be less than open hours: "
                f"{close_time} <= {open_time}",
            )
