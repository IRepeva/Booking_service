import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Optional

import requests
from fastapi import HTTPException
from sqlalchemy import Date, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import settings
from db.postgres import Base
from models.models import Event, Place, PurchasedFilm
from models.schemas import EventInput, EventEdit
from services.base import BaseService

MINIMUM_TIME_INTERVAL = 1800


class EventService(BaseService):
    model: Base = Event
    instance: str = 'event'

    @classmethod
    async def create(
            cls,
            session: AsyncSession,
            data: EventInput,
            user_id: str | uuid.UUID
    ) -> Event:
        await cls.validate(session, data, user_id)
        return await super().create(session, data, user_id)

    @classmethod
    async def edit(
            cls,
            session: AsyncSession,
            new_data: EventEdit,
            _id: uuid.UUID,
            user_id: uuid.UUID
    ) -> Optional[Event]:
        db_event = await cls.validate_host(session, _id, user_id)
        await cls.validate(session, new_data, user_id, _id)

        db_event.start = new_data.start
        db_event.duration = new_data.duration
        db_event.place_id = new_data.place_id
        db_event.film_id = new_data.film_id
        db_event.comments = new_data.comments
        db_event.participants = new_data.participants

        return await cls.save(session, db_event)

    @classmethod
    async def validate(
            cls,
            session: AsyncSession,
            data: EventInput | EventEdit,
            user_id: uuid.UUID,
            _id: uuid.UUID | None = None
    ):
        await cls.validate_time(
            session, data.start, data.duration, data.place_id, _id
        )
        await cls.validate_participants(
            session, data.participants, data.place_id
        )
        await cls.validate_movie_access(session, data.film_id, user_id)

    @classmethod
    async def validate_time(
            cls,
            session: AsyncSession,
            event_start: datetime,
            duration: int,
            place_id: str,
            _id: uuid.UUID | None = None
    ):
        if duration < MINIMUM_TIME_INTERVAL:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"The event should last at least 30 minutes"
            )

        if duration % MINIMUM_TIME_INTERVAL != 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"The event duration should be a multiple of 30 minutes"
            )

        now = datetime.utcnow()
        event_finish = event_start + timedelta(seconds=duration)
        if event_start < now:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Event can't be organized in the past"
            )

        place = (
            await session.execute(
                select(
                    Place
                ).where(
                    Place.id == place_id
                )
            )
        ).scalars().first()
        if not place:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'Place {place_id} not found'
            )

        if (
                event_start.time() > place.close
                or event_start.time() < place.open
                or event_finish.time() > place.close
        ):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'Event can be organized only at working hours: '
                       f'between {place.open} and {place.close} for {place_id}'
            )

        place_events = (
            await session.execute(
                select(
                    Event
                ).where(
                    Event.place_id == place_id,
                    (cast(Event.start, Date) == event_start.date())
                )
            )
        ).scalars().all()
        print(
            f'PLACE EVENTS: {[(event.id, event.name) for event in place_events]}')

        for place_event in place_events:
            if _id and place_event.id == _id:
                print('in continue')
                continue

            place_event_start = place_event.start
            place_event_finish = (
                    place_event_start + timedelta(seconds=place_event.duration)
            )
            print(f'exist: {place_event_start, place_event_finish}, '
                  f'want: {event_start, event_finish}, '
                  f'so {event_start <= place_event_finish, place_event_start <= event_finish}')
            if (
                    event_start < place_event_finish
                    and place_event_start <= event_finish
            ):
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f'The place is already occupied for this period'
                )

    @classmethod
    async def validate_participants(
            cls, session: AsyncSession, participants: int, place_id: str
    ):
        if participants <= 0:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'The event should be organized '
                       f'with at least 1 participant, not {participants}'
            )

        place_capacity = (
            await session.execute(
                select(
                    Place.capacity
                ).where(
                    Place.id == place_id
                )
            )
        ).scalars().first()
        if participants > place_capacity:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'The capacity of the {place_id} - {place_capacity}. '
                       f'It is not enough for the {participants} people'
            )

    @classmethod
    async def validate_movie_access(
            cls, session: AsyncSession, film_id: uuid.UUID, user_id: uuid.UUID
    ):
        response = requests.get(url=settings.free_films_url)
        if response.status_code != HTTPStatus.OK:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )
        if film_id in response:
            return

        purchased_movies = (
            await session.execute(
                select(
                    PurchasedFilm
                ).where(
                    PurchasedFilm.user_id == user_id
                )
            )
        ).scalars().all()
        if film_id not in [movie.film_id for movie in purchased_movies]:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'The {film_id} neither free nor bought'
            )
