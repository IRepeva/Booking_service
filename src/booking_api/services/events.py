import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Iterable

import requests
from fastapi import HTTPException
from sqlalchemy import Date, Interval, String, cast
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from booking_api.models.schemas import EventInput, EventDetails, EventSchema
from booking_api.services.base import BaseService
from booking_api.services.locations import LocationService
from booking_api.utils.exceptions import (
    LocationNotFound, EventNotFound, BadRequestException, ForbiddenException
)
from config.base import settings
from db.tables import Event, Location, PurchasedMovie, PurchasedMovieHost, Seat
from db.tables.base import Base
from db.tables.booking import Booking


class EventService(BaseService):
    model: Base = Event
    instance: str = "event"

    @classmethod
    async def create(
            cls, session: AsyncSession, data: EventInput,
            user_id: uuid.UUID, extra: dict = None, commit=True
    ) -> EventSchema:
        await cls.validate(data, session=session, user_id=user_id)
        event = await super().create(session, data, user_id)
        return EventSchema.from_orm(event)

    @classmethod
    async def get_events(cls, session: AsyncSession) -> list[EventDetails]:
        query_seats = (
            select(Booking.seat_id)
            .filter(Booking.event_id == Event.id)
        )
        filters = (Event.start > datetime.now(), ~Seat.id.in_(query_seats))
        query = cls.get_event_query(filters)
        events = (await session.execute(query)).all()
        return [EventDetails.from_orm(event) for event in events]

    @classmethod
    async def get_event(
            cls, session: AsyncSession, event_id: uuid.UUID
    ) -> EventDetails:
        query = cls.get_event_query(filters=(Event.id == event_id,))
        print(f'query: {query}, event_id: {event_id}')
        event = (await session.execute(query)).first()
        print(f'event: {event}')
        if not event:
            raise EventNotFound(event_id)

        return EventDetails.from_orm(event)

    @classmethod
    async def validate(cls, data: EventInput | EventInput, *args, **kwargs):
        session, user_id = kwargs['session'], kwargs['user_id']
        location = await cls.validate_location(
            session, data.location_id, user_id
        )
        await cls.validate_time(
            session, data.start, data.duration, location, kwargs.get('_id')
        )
        await cls.validate_participants(session, data.participants, location.id)
        await cls.validate_movie_access(session, data.movie_id, user_id)

    @classmethod
    async def validate_location(
            cls, session: AsyncSession, _id: uuid.UUID, user_id: uuid.UUID
    ):
        location = await LocationService.get_by_id(session, _id)
        if not location:
            raise LocationNotFound(_id)
        if location.host_id and not await LocationService.is_host(
                location.host_id, user_id
        ):
            raise ForbiddenException(
                message=f"Only host can organize events at the location {_id}"
            )
        return location

    @classmethod
    async def validate_time(
            cls,
            session: AsyncSession,
            event_start: datetime,
            duration: int,
            location: Location,
            _id: uuid.UUID | None = None,
    ):
        if duration < settings.minimum_time_interval:
            raise BadRequestException(
                message="The event should last at least 30 minutes"
            )

        if duration % settings.minimum_time_interval != 0:
            raise BadRequestException(
                message="The duration of the event should be"
                        " in increments of 30 minutes"
            )

        now = datetime.utcnow()
        event_finish = event_start + timedelta(seconds=duration)
        if event_start < now:
            raise BadRequestException(
                message="Event can't be organized in the past",
            )

        if not (
                location.close >= event_finish.time()
                > event_start.time() >= location.open
        ):
            raise BadRequestException(
                message=f"Event can be organized only at working hours:"
                        f" between {location.open} and {location.close}"
                        f" for {location.id}",
            )

        filters = (
            Event.location_id == location.id,
            (cast(Event.start, Date) == event_start.date()),
            event_start < (
                    Event.start + cast(
                        cast(Event.duration, String) + " seconds",
                        Interval
                    )
            ),
            Event.start < event_finish,
        )
        if _id:
            filters += (Event.id != _id,)

        if await cls.get_first(session, filters=filters):
            raise BadRequestException(
                message="The location is already occupied for this period",
            )

    @classmethod
    async def validate_participants(
            cls,
            session: AsyncSession,
            participants: int,
            location_id: uuid.UUID,
    ):
        if participants <= 0:
            raise BadRequestException(
                message=f"The event should be organized "
                        f"with at least 1 participant, not {participants}",
            )

        location_capacity = await cls.get_first(
            session, Location.capacity, (Location.id == location_id,)
        )
        if participants > location_capacity:
            raise BadRequestException(
                message=f"The capacity of {location_id} - {location_capacity}."
                        f" It is not enough for the {participants} people",
            )

    @classmethod
    async def validate_movie_access(
            cls, session: AsyncSession, movie_id: uuid.UUID, user_id: uuid.UUID
    ):
        response = requests.get(url=settings.free_films_url)
        if response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=response.status_code,
                                detail=response.text)

        if str(movie_id) in response.json():
            return

        purchased_movies = await cls.get_purchased_movies(
            session, filters=(PurchasedMovieHost.c.host_id == user_id,)
        )
        if movie_id not in (movie.movie_id for movie in purchased_movies):
            raise BadRequestException(
                message=f"The {movie_id} neither free nor bought",
            )

    @classmethod
    async def get_purchased_movies(
            cls, session: AsyncSession, filters: Iterable = ()
    ) -> list[PurchasedMovie]:
        stmt = (
            select(PurchasedMovie)
            .join(
                PurchasedMovieHost,
                PurchasedMovieHost.c.purchased_movie_id == PurchasedMovie.movie_id,
            )
            .where(*filters)
        )

        return (await session.execute(stmt)).scalars().all()

    @staticmethod
    def get_event_query(filters: Iterable):
        return (
            select(
                Event.name, Event.start, Event.duration, Event.host_id,
                Event.participants, Event.notes, Event.movie_id,
                Event.location_id,
                func.array_agg(
                    func.json_build_object(
                        'id', Seat.id,
                        'row', Seat.row,
                        'seat', Seat.seat,
                        'type', Seat.type
                    ), type_=ARRAY(JSON)
                ).label('seats'),
            )
            .select_from(Event)
            .join(
                Seat, Seat.location_id == Event.location_id,
            )
            .group_by(
                Event.name, Event.start, Event.duration, Event.host_id,
                Event.participants, Event.notes, Event.movie_id,
                Event.location_id
            )
            .where(*filters)
        )
