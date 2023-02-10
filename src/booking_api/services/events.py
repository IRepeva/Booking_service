import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Optional, Iterable

import requests
from fastapi import HTTPException
from sqlalchemy import Date, Interval, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from booking_api.models.schemas import EventInput
from booking_api.services.base import BaseService
from booking_api.services.locations import LocationService
from config.base import settings
from db.tables import (
    Event,
    Location,
    PurchasedMovie,
    PurchasedMovieHost,
)
from db.utils.postgres import Base

MINIMUM_TIME_INTERVAL = 1800


class EventService(BaseService):
    model: Base = Event
    instance: str = "event"

    @classmethod
    async def create(
            cls, session: AsyncSession, data: EventInput,
            user_id: str | uuid.UUID, model: Base = None
    ) -> Event:
        await cls.validate(session, data, user_id)
        return await super().create(session, data, user_id)

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
        location = await cls.validate_location(session, data.location_id, user_id)
        await cls.validate_time(session, data.start, data.duration, location, _id)
        await cls.validate_participants(session, data.participants, location.id)
        await cls.validate_movie_access(session, data.movie_id, user_id)

    @classmethod
    async def validate_location(
            cls, session: AsyncSession, _id: uuid.UUID, user_id: uuid.UUID
    ):
        location = await LocationService.get_by_id(session, _id)
        if not location:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Location {_id} not found"
            )
        if location.host_id and not await LocationService.is_host(location.host_id, user_id):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"Only host can organize events at the location {_id}",
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

        if not location.close >= event_finish.time() > event_start.time() >= location.open:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Event can be organized only at working hours: "
                       f"between {location.open} and {location.close} "
                       f"for {location.id}",
            )

        filters = (
            Event.location_id == location.id,
            (cast(Event.start, Date) == event_start.date()),
            event_start < Event.start + cast(
                cast(Event.duration, String) + " seconds", Interval
            ),
            Event.start < event_finish,
        )
        if _id:
            filters += (Event.id != _id,)

        if await cls.get_first(session, filters=filters):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="The location is already occupied for this period",
            )

    @classmethod
    async def validate_participants(
            cls,
            session: AsyncSession,
            participants: int,
            location_id: uuid.UUID,
    ):
        if participants <= 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"The event should be organized "
                       f"with at least 1 participant, not {participants}",
            )

        location_capacity = await cls.get_first(
            session, Location.capacity, (Location.id == location_id,)
        )
        if participants > location_capacity:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'The capacity of the {location_id} - {location_capacity}. '
                       f'It is not enough for the {participants} people'
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
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"The {movie_id} neither free nor bought",
            )

    @classmethod
    async def get_purchased_movies(
            cls, session: AsyncSession, filters: Iterable = ()
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
