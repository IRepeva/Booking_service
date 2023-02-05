import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from booking_api.models.schemas import Event, EventEdit, EventInput
from booking_api.services.events import EventService
from booking_api.utils.authentication import get_token_payload, security
from db.utils.postgres import get_db

router = APIRouter(prefix="/events")


@router.post("/create", response_model=Event, summary="Create event")
async def create_event(
    event: EventInput, session: AsyncSession = Depends(get_db), token=Depends(security)
) -> Event:
    """
    Create event with the following data:

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
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    await EventService.validate_name(session, event.name)
    new_event = await EventService.create(session=session, data=event, user_id=user_id)
    return EventService.model_to_dict(new_event)


@router.get(
    "/{event_id}", response_model=Event, summary="Get detailed information about event"
)
async def event_details(
    event_id: str, session: AsyncSession = Depends(get_db)
) -> Event:
    """
    Get all event information:

    - **id**: each event has a unique id
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
            detail=f"Event with id {event_id} is not found",
        )

    return EventService.model_to_dict(event)


@router.put("/{event_id}/edit", response_model=Event, summary="Edit the event")
async def edit_event(
    event_id: uuid.UUID,
    new_event: EventEdit,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
):
    """
    Change the event:

    - **place_id**: event's location
    - **start**: event's start datetime
    - **duration**: event's duration
    - **host_id**: event's organizer
    - **film_id**: film of the event
    - **participants**: number of participants
    - **comments**: any additional information
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    event = await EventService.edit(
        session=session, new_data=new_event, _id=event_id, user_id=user_id
    )
    return EventService.model_to_dict(event)


@router.put("/{event_id}/rename", response_model=Event, summary="Rename the event")
async def rename_event(
    event_id: uuid.UUID,
    new_name: str,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
):
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    event = await EventService.rename(
        session=session, new_name=new_name, _id=event_id, user_id=user_id
    )
    return EventService.model_to_dict(event)


@router.delete("/{event_id}/delete", summary="Delete event")
async def delete_event(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
) -> JSONResponse:
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    event = await EventService.delete(session=session, _id=event_id, user_id=user_id)
    if not event:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Event with id {event_id} is not found",
        )
    return JSONResponse(
        status_code=200,
        content={"message": f"Event {event_id} was successfully deleted"},
    )
