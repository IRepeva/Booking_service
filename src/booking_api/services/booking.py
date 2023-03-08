import uuid
from typing import Iterable

from sqlalchemy import func, Integer, cast
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from booking_api.models.schemas import (
    BookingInput, BookingSchema, BookingDetails
)
from booking_api.services.base import BaseService
from booking_api.services.events import EventService
from booking_api.utils.exceptions import (
    EventNotFound, SeatNotFound, BookingNotFound, BadRequestException,
    ForbiddenException
)
from db.tables import Seat, Event
from db.tables.booking import BookingStatus, Booking


class BookingService(BaseService):
    model = Booking
    instance: str = 'booking'

    @classmethod
    async def create(
            cls, session: AsyncSession, data: BookingInput,
            user_id: uuid.UUID, extra: dict = None, commit=True
    ) -> BookingSchema:
        await cls.validate(data, session=session)

        extra = {'guest_id': user_id, 'status': BookingStatus.RESERVED.value}
        booking = await super().create(session, data, user_id, extra)
        return BookingSchema.from_orm(booking)

    @classmethod
    async def get_booking(
            cls, session: AsyncSession, booking_id: uuid.UUID
    ) -> BookingDetails:

        query = cls.get_booking_query(filters=(Booking.id == booking_id,))
        booking = (await session.execute(query)).first()
        return BookingDetails.from_orm(booking)

    @classmethod
    async def get_bookings(
            cls, session: AsyncSession, user_id: uuid.UUID
    ) -> list[BookingDetails]:
        query = cls.get_booking_query(filters=(Booking.guest_id == user_id,))
        bookings = (await session.execute(query)).all()
        return [BookingDetails.from_orm(booking) for booking in bookings]

    @staticmethod
    def get_booking_query(filters: Iterable):
        return (
            select(
                Booking.id, cast(Booking.status, Integer),
                func.json_build_object(
                    'id', Seat.id,
                    'row', Seat.row,
                    'seat', Seat.seat,
                    'type', Seat.type
                ).label('seats'),
                Event.id.label("event_id"),
                Event.name.label("event_name"),
                Event.start.label("event_start"),
                Event.duration.label("event_duration"),
            )
            .select_from(Booking)
            .join(
                Event, Event.id == Booking.event_id,
            )
            .join(
                Seat, Seat.id == Booking.seat_id,
            )
            .where(*filters)
        )

    @classmethod
    async def update_booking_status(
            cls,
            session: AsyncSession,
            booking_id: uuid.UUID,
            new_status: int,
            user_id: uuid.UUID
    ) -> dict:
        await cls.validate_user(session, booking_id, user_id)
        query = (
            update(Booking)
            .where(Booking.id == booking_id)
            .values(status=new_status)
        )
        await session.execute(query)
        await session.commit()
        return {"msg": "booking status was updated"}

    @classmethod
    async def validate(cls, data: BookingInput, *args, **kwargs):
        session = kwargs['session']
        event = await EventService.get_by_id(session, data.event_id)
        if not event:
            raise EventNotFound(data.event_id)

        event_seats = await cls.get_all(
            session, Seat.id, filters=(Seat.location_id == event.location_id,)
        )

        if data.seat_id not in event_seats:
            raise SeatNotFound(data.seat_id)

        occupied_seats = await cls.get_all(
            session, Booking.seat_id,
            filters=(Booking.event_id == data.event_id,)
        )
        if data.seat_id in occupied_seats:
            raise BadRequestException(
                message=f'Seat {data.seat_id} is already occupied'
            )

    @classmethod
    async def validate_user(
            cls, session: AsyncSession, _id: uuid.UUID, user_id: uuid.UUID
    ):
        booking = await cls.get_by_id(session, _id)
        if not booking:
            raise BookingNotFound(_id)

        if str(booking.guest_id) != user_id:
            raise ForbiddenException(
                message=f"Only guest can modify the booking {_id}"
            )

        return booking
