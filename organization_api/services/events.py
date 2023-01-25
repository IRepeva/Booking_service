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
from models.models import Event, Place, PurchasedFilm
from models.schemas import EventInput


class EventService:

    @classmethod
    async def get_by_id(cls, session: AsyncSession, event_id: str | uuid.UUID):
        result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_name(cls, session: AsyncSession, event_name: str):
        result = await session.execute(
            select(Event).where(Event.name == event_name)
        )
        return result.scalars().first()

    @classmethod
    async def create_event(
            cls,
            session: AsyncSession,
            event_data: EventInput,
            user_id: str | uuid.UUID
    ) -> Event:
        await cls.time_validation(
            session, event_data.start, event_data.duration, event_data.place_id
        )
        await cls.participants_validation(
            session, event_data.participants, event_data.place_id
        )
        await cls.movie_validation(session, event_data.film_id, user_id)

        event_data = event_data.dict()
        event_data.update({'host_id': user_id})

        event = Event(**event_data)
        return await cls.save_event(session, event)

    @classmethod
    async def edit_event(
            cls,
            session: AsyncSession,
            new_event: EventInput,
            event_id: str,
            user_id: str
    ) -> Optional[Event]:
        db_event = await cls.get_by_id(session, event_id)
        if not db_event:
            return None

        if not cls.is_host(db_event, user_id):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f'Only host can modify the event'
            )

        db_event.name = new_event.name
        db_event.datetime = new_event.datetime
        db_event.duration = new_event.duration
        # fill other
        return await cls.save_event(session, db_event)

    @classmethod
    async def delete_event(
            cls,
            session: AsyncSession,
            event_id: str,
            user_id: str
    ) -> Optional[Event]:
        db_event = await cls.get_by_id(session, event_id)
        if not db_event:
            return None

        if not cls.is_host(db_event, user_id):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f'Only host can delete the event'
            )

        session.delete(db_event)
        session.commit()
        return db_event

    @classmethod
    async def save_event(cls, session: AsyncSession, event: Event):
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    @classmethod
    def is_host(cls, event: Event, user_id: str):
        return True if event.host_id == user_id else False

    @classmethod
    async def time_validation(
            cls,
            session: AsyncSession,
            event_start: datetime,
            duration: int,
            place_id: str
    ):
        now = datetime.utcnow()
        event_finish = event_start + timedelta(seconds=duration)
        print('TIME', event_start, now)
        if event_start < now:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Event can't be organized in the past"
            )
        
        place_open_hours = await session.execute(
            select(
                Place.open, Place.close
            ).where(
                Place.id == place_id
            )
        )
        place_open_hours = place_open_hours.scalars().first()
        if not place_open_hours:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'Incorrect place {place_id}'
            )

        place_open, place_close = place_open_hours
        if event_start.time() < place_open or event_finish.time() > place_close:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'Event can be organized only at working hours: '
                       f'between {place_open} and {place_close} for {place_id}'
            )
        
        place_events = await session.execute(
            select(
                Event
            ).where(
                Event.place_id == place_id,
                (cast(Event.datetime, Date) == event_start.date())
            )
        )
        place_events = place_events.scalars().all()
        for place_event in place_events:
            place_event_start = place_event.start
            place_event_finish = (
                    place_event_start + timedelta(seconds=place_event.duration)
            )
            if (
                    event_start <= place_event_finish
                    and place_event_start <= event_finish
            ):
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f'The place is already occupied for this period'
                )

    @classmethod
    async def participants_validation(
            cls, session: AsyncSession, participants: int, place_id: str
    ):
        place_capacity = await session.execute(
            select(
                Place.capacity
            ).where(
                Place.id == place_id
            )
        )
        place_capacity = place_capacity.scalars().first()
        if participants > place_capacity:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'The capacity of the {place_id} - {place_capacity}. '
                       f'It is not enough for the {participants} people'
            )

    @classmethod
    async def movie_validation(
            cls, session: AsyncSession, film_id: str, user_id: str
    ):
        response = requests.get(url=settings.free_films_url)
        if response.status_code != HTTPStatus.OK:
            raise Exception(
                f"Status code {response.status_code} {response.text}"
            )
        if film_id in response:
            return

        purchased_movies = await session.execute(
            select(
                PurchasedFilm
            ).where(
                PurchasedFilm.user_id == user_id
            )
        )
        purchased_movies = purchased_movies.scalars().all()
        if film_id not in purchased_movies:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f'The {film_id} neither free nor bought'
            )
