import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from booking_api.models.schemas import (
    Location, LocationEdit, LocationInput, SeatInput
)
from booking_api.services.locations import LocationService
from booking_api.utils.authentication import security, check_authorization
from db.tables import Seat
from db.utils.postgres import get_db

router = APIRouter(prefix="/locations")


@router.post("/", response_model=Location, summary="Add event's location")
async def add_location(
        location: LocationInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
        seats_input: list[SeatInput] | None = None,
) -> Location:
    """
    Create location with the following data:

    - **name**: each location has a unique name
    - **coordinates**: location's coordinates
    - **open**: open hour
    - **close**: close hour
    - **capacity**: maximum capacity of the location
    """
    user_id = check_authorization(token)

    await LocationService.validate_name(session, name=location.name)
    new_location = await LocationService.create(
        session=session, data=location, user_id=user_id
    )
    if seats_input:
        seats_data = await LocationService.prepare_seats_data(seats_input,
                                                              new_location.id)
    else:
        seats_data = [
            {
                'id': uuid.uuid4(),
                'location_id': new_location.id
            } for _ in range(location.capacity)
        ]

    session.add_all([Seat(**seat) for seat in seats_data])
    await session.commit()

    return LocationService.model_to_dict(new_location)


@router.get(
    "/{location_id}",
    response_model=Location,
    summary="Get detailed information about the location",
)
async def location_details(
    location_id: str, session: AsyncSession = Depends(get_db)
) -> Location:
    """
    Get all location information:

    - **id**: unique id of the location
    - **name**: each location has a unique name
    - **coordinates**: location's coordinates
    - **open**: open hour
    - **close**: close hour
    - **host_id**: location's owner or None
    - **capacity**: maximum capacity of the location
    """
    location = await LocationService.get_by_id(session, location_id)
    if not location:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Location with id {location_id} is not found",
        )

    return LocationService.model_to_dict(location)


@router.put("/{location_id}", response_model=Location, summary="Edit the location")
async def edit_location(
    location_id: uuid.UUID,
    new_location: LocationEdit,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
) -> Location:
    """
    Change the location:

    - **coordinates**: location's coordinates
    - **open**: open hour
    - **close**: close hour
    - **capacity**: maximum capacity of the location
    """
    user_id = check_authorization(token)

    location = await LocationService.edit(
        session=session, new_data=new_location, _id=location_id, user_id=user_id
    )
    return LocationService.model_to_dict(location)


@router.put("/{location_id}/rename", response_model=Location, summary="Rename the location")
async def rename_location(
    location_id: uuid.UUID,
    new_name: str,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
) -> Location:
    user_id = check_authorization(token)

    location = await LocationService.rename(
        session=session, new_name=new_name, _id=location_id, user_id=user_id
    )
    return LocationService.model_to_dict(location)


@router.delete("/{location_id}", summary="Delete location")
async def delete_location(
    location_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
) -> JSONResponse:
    user_id = check_authorization(token)

    await LocationService.delete(session=session, _id=location_id, user_id=user_id)
    return JSONResponse(
        status_code=200,
        content={"message": f"Location {location_id} was successfully deleted"},
    )
