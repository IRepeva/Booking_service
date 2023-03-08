import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from booking_api.models.schemas import EventSchema, EventInput, EventDetails
from booking_api.services.events import EventService
from booking_api.utils.authentication import check_authorization, security
from db.utils.postgres import get_db

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventSchema, summary="Create event")
async def create_event(
        event: EventInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
) -> EventSchema:
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
    return await EventService.create(session=session, data=event,
                                     user_id=user_id)


@router.get(
    "/{event_id}", response_model=EventDetails,
    summary="Get detailed information about event"
)
async def event_details(
        event_id: uuid.UUID,
        session: AsyncSession = Depends(get_db)
) -> EventDetails:
    """
    Get all event information:

    - **name**: each event has a unique name
    - **location_id**: event's location
    - **start**: event's start datetime
    - **duration**: event's duration
    - **host_id**: event's organizer
    - **movie_id**: film of the event
    - **participants**: number of participants
    - **notes**: any additional information
    - **seats**: seats that are available for the event
    """
    return await EventService.get_event(session, event_id)


@router.put("/{event_id}", response_model=EventSchema, summary="Edit the event")
async def edit_event(
        event_id: uuid.UUID,
        new_event: EventInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
) -> EventSchema:
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
    return EventSchema.from_orm(event)


@router.delete("/{event_id}", summary="Delete event")
async def delete_event(
        event_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
) -> JSONResponse:
    user_id = check_authorization(token)
    await EventService.delete(session=session, _id=event_id, user_id=user_id)

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"message": f"Event {event_id} was successfully deleted"},
    )


@router.get("/", response_model=list[EventDetails],  summary="Get all events")
async def get_events(
        session: AsyncSession = Depends(get_db),
) -> list[EventDetails]:
    """
    Get the detailed information on all events for which bookings are available
    """
    return await EventService.get_events(session)
