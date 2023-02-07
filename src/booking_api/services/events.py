import random
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Optional

import requests
from fastapi import HTTPException
from sqlalchemy import Date, Interval, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from booking_api.models.schemas import EventInput
from booking_api.services.base import BaseService
from booking_api.services.places import PlaceService
from config.base import settings
from db.tables import (
    Booking,
    BookingStatus,
    Event,
    Location,
    PurchasedMovie,
    PurchasedMovieHost,
    Seat,
)
from db.utils.postgres import Base

MINIMUM_TIME_INTERVAL = 1800


class EventService(BaseService):
    model: Base = Event
    instance: str = "event"

    @classmethod
    async def create(
        cls, session: AsyncSession, data: EventInput, user_id: str | uuid.UUID
    ) -> Event:
        vacant_seats = await cls.validate(session, data, user_id)
        event = await super().create(session, data, user_id)

        event_seat_data = {"event_id": event.id, "status": BookingStatus.BOOKED}
        for seat_id in random.sample(vacant_seats, data.participants):
            event_seat_data.update({"seat_id": seat_id})
            insert_stmt = Booking.insert().values(**event_seat_data)
            await session.execute(insert_stmt)
            await session.commit()

        return event

    @classmethod
    async def edit(
        cls,
        session: AsyncSession,
        new_data: EventInput,
        _id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Event]:
        db_event = await cls.validate_host(session, _id, user_id)
        await cls.validate(session, new_data, user_id, _id)

        db_event.name = new_data.name
        db_event.start = new_data.start
        db_event.duration = new_data.duration
        db_event.location_id = new_data.location_id
        db_event.movie_id = new_data.movie_id
        db_event.notes = new_data.notes
        db_event.participants = new_data.participants

        return await cls.save(session, db_event)

    @classmethod
    async def validate(
        cls,
        session: AsyncSession,
        data: EventInput | EventInput,
        user_id: uuid.UUID,
        _id: uuid.UUID | None = None,
    ):
        place = await cls.validate_place(session, data.location_id, user_id)
        await cls.validate_time(data.start, data.duration, place)
        vacant_seats = await cls.validate_participants(
            session, data.start, data.duration, data.participants, place, _id
        )
        await cls.validate_movie_access(session, data.movie_id, user_id)
        return vacant_seats

    @classmethod
    async def validate_place(
        cls, session: AsyncSession, _id: uuid.UUID, user_id: uuid.UUID
    ):
        place = await PlaceService.get_by_id(session, _id)
        if not place:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"Place {_id} not found"
            )
        if place.host_id and not await PlaceService.is_host(place.host_id, user_id):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"Only host can organize events at the place {_id}",
            )
        return place

    @classmethod
    async def validate_time(
        cls,
        event_start: datetime,
        duration: int,
        place: Location,
    ):
        if duration < MINIMUM_TIME_INTERVAL:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="The event should last at least 30 minutes",
            )

        if duration % MINIMUM_TIME_INTERVAL != 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="The event duration should be a multiple of 30 minutes",
            )

        now = datetime.utcnow()
        event_finish = event_start + timedelta(seconds=duration)
        if event_start < now:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Event can't be organized in the past",
            )

        if not place:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail=f"Place {place.id} not found"
            )

        if (
            event_start.time() > place.close
            or event_start.time() < place.open
            or event_finish.time() > place.close
        ):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Event can be organized only at working hours: "
                f"between {place.open} and {place.close} for {place.id}",
            )

    @classmethod
    async def validate_participants(
        cls,
        session: AsyncSession,
        event_start: datetime,
        duration: int,
        participants: int,
        place: Location,
        _id: uuid.UUID | None = None,
    ):
        if participants <= 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"The event should be organized "
                f"with at least 1 participant, not {participants}",
            )
        event_finish = event_start + timedelta(seconds=duration)

        filters = (
            Event.location_id == place.id,
            (cast(Event.start, Date) == event_start.date()),
            event_start
            < Event.start + cast(cast(Event.duration, String) + " seconds", Interval),
            Event.start < event_finish,
        )
        if _id:
            filters += (Event.id != _id,)
        place_events = await cls.get_all(session, filters=filters)

        vacant_seats = None
        for place_event in place_events:
            vacant_seats = await cls.get_vacant_seats(session, place_event.id)
            if not vacant_seats:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="The place is already occupied for this period",
                )

            if participants > len(vacant_seats):
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"There are {len(vacant_seats)} vacant seats. "
                    f"It is not enough for {participants} people",
                )
        return (
            vacant_seats
            if vacant_seats
            else await cls.get_all(session, Seat.id, (Seat.place_id == place.id,))
        )

    @classmethod
    async def validate_movie_access(
        cls, session: AsyncSession, movie_id: uuid.UUID, user_id: uuid.UUID
    ):
        response = requests.get(url=settings.free_films_url)
        if response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        if str(movie_id) in response.json():
            return

        purchased_movies = await cls.get_purchased_movies(
            session, filters=(PurchasedMovieHost.c.host_id == user_id,)
        )
        if movie_id not in (movie.movie_id for movie in purchased_movies):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"The {movie_id} neither free nor bought",
            )

    @classmethod
    async def get_vacant_seats(cls, session: AsyncSession, event_id: uuid.UUID):
        return (
            await session.execute(
                select(Seat)
                .join(Booking, Seat.id == Booking.c.seat_id)
                .where(
                    Booking.c.status == BookingStatus.EMPTY,
                    Booking.c.event_id == event_id,
                )
            )
        ).all()

    @classmethod
    async def get_purchased_movies(
        cls, session: AsyncSession, filters: list | tuple = (), *args, **kwargs
    ):
        stmt = (
            select(PurchasedMovie)
            .join(
                PurchasedMovieHost,
                PurchasedMovieHost.c.purchased_movie_id == PurchasedMovie.movie_id,
            )
            .where(*filters)
        )

        return (await session.execute(stmt)).scalars().all()
