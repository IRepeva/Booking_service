from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from db.postgres import get_db
from models.schemas import Event, EventInput
from services.events import EventService
from utils.authentication import security, get_token_payload
# from utils.cache import Cache

router = APIRouter()


@router.post('/create', response_model=Event, summary='Create event')
async def create_event(
        event: EventInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
) -> Event:
    """
    Create event with the following data:

    - **id**: unique id of the event
    - **name**: each event has a unique name
    - **place_id**: event's location
    - **start**: event's start datetime
    - **duration**: event's duration
    - **host_id**: event's organizer
    - **film_id**: film of the event
    - **participants**: number of participants
    - **comments**: any additional information
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    db_event = await EventService.get_by_name(session, event_name=event.name)
    if db_event:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Event with name {event.name} already exists"
        )
    return await EventService.create_event(
        session=session, event_data=event, user_id=user_id
    )


@router.get('/{event_id}', response_model=Event, summary="Get event by id")
# @Cache()
async def event_details(
        event_id: str,
        session: AsyncSession = Depends(get_db)
) -> Event:
    """
    Get all event information:

    - **name**: each event has a unique name
    - **place_id**: event's location
    - **start**: event's start datetime
    - **duration**: event's duration
    - **host_id**: event's organizer
    - **film_id**: film of the event
    - **participants**: number of participants
    - **comments**: any additional information
    """
    event = await EventService.get_by_id(session, event_id)
    if not event:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Event with id {event_id} is not found'
        )

    return event


@router.put(
    "/{event_id}/edit", response_model=Event, summary="Edit the event"
)
async def edit_event(
        event_id: str,
        new_event: EventInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
):
    """
    Change the event:

    - **name**: each event has a unique name
    - **place_id**: event's location
    - **start**: event's start datetime
    - **duration**: event's duration
    - **host_id**: event's organizer
    - **film_id**: film of the event
    - **participants**: number of participants
    - **comments**: any additional information
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    event = await EventService.edit_event(
        session=session, new_event=new_event, event_id=event_id, user_id=user_id
    )
    if not event:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Event with id {event_id} is not found'
        )
    return event


@router.delete(
    "/{event_id}/delete", summary="Delete event"
)
async def delete_event(
        event_id: str,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
) -> JSONResponse:
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    event = await EventService.delete_event(
        session=session, event_id=event_id, user_id=user_id
    )
    if not event:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Event with id {event_id} is not found'
        )
    return JSONResponse(
        status_code=200,
        content={"message": f"Event {event_id} was successfully deleted"}
    )
