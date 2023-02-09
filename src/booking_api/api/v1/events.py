import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from booking_api.models.schemas import Event, EventInput
from booking_api.services.events import EventService
from booking_api.utils.authentication import security, check_authorization
from db.utils.postgres import get_db

router = APIRouter(prefix="/events")


@router.post("/", response_model=Event, summary="Create event")
async def create_event(
        event: EventInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
) -> Event:
    """
    Create event with the following data:

    - **name**: each event has a unique name
    - **location_id**: event's location
    - **start**: event's start datetime
    - **duration**: event's duration
    - **host_id**: event's organizer
    - **movie_id**: film of the event
    - **participants**: number of participants
    - **notes**: any additional information
    """
    user_id = check_authorization(token)
    new_event = await EventService.create(session=session,
                                          data=event,
                                          user_id=user_id)
    return EventService.model_to_dict(new_event)


@router.get(
    "/{event_id}", response_model=Event,
    summary="Get detailed information about event"
)
async def event_details(
        event_id: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> Event:
    """
    Get all event information:

    - **id**: each event has a unique id
    - **name**: each event has a unique name
    - **location_id**: event's location
    - **start**: event's start datetime
    - **duration**: event's duration
    - **host_id**: event's organizer
    - **movie_id**: film of the event
    - **participants**: number of participants
    - **notes**: any additional information
    """
    event = await EventService.get_by_id(session, event_id)
    if not event:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Event with id {event_id} is not found",
        )

    return EventService.model_to_dict(event)


@router.put("/{event_id}", response_model=Event, summary="Edit the event")
async def edit_event(
        event_id: uuid.UUID,
        new_event: EventInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
):
    """
    Change the event:

    - **location_id**: event's location
    - **start**: event's start datetime
    - **duration**: event's duration
    - **host_id**: event's organizer
    - **movie_id**: film of the event
    - **participants**: number of participants
    - **notes**: any additional information
    """
    user_id = check_authorization(token)
    event = await EventService.edit(
        session=session, new_data=new_event, _id=event_id, user_id=user_id
    )
    return EventService.model_to_dict(event)


@router.delete("/{event_id}", summary="Delete event")
async def delete_event(
        event_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
) -> JSONResponse:
    user_id = check_authorization(token)
    event = await EventService.delete(session=session,
                                      _id=event_id,
                                      user_id=user_id)
    if not event:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Event with id {event_id} is not found",
        )
    return JSONResponse(
        status_code=200,
        content={"message": f"Event {event_id} was successfully deleted"},
    )
