import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from booking_api.models.schemas import (
    LocationSchema, LocationEdit, LocationInput, LocationDetails,
    SeatInput
)
from booking_api.services.locations import LocationService
from booking_api.utils.authentication import security, check_authorization
from booking_api.utils.exceptions import LocationNotFound, BadRequestException
from db.tables import Seat
from db.utils.postgres import get_db

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("/", response_model=LocationSchema, summary="Add event's location")
async def add_location(
        location: LocationInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
        seats_input: list[SeatInput] | None = None,
) -> LocationSchema:
    """
    Create location with the following data:

    - **id**: unique location identification
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
        if location.capacity != len(seats_input):
            raise BadRequestException(
                message='Information should be provided for every seat'
            )
        seats_data = await LocationService.prepare_seats_data(
            seats_input, new_location.id
        )
    else:
        seats_data = [
            {
                'id': uuid.uuid4(),
                'location_id': new_location.id
            } for _ in range(location.capacity)
        ]

    session.add_all([Seat(**seat) for seat in seats_data])
    await session.commit()

    return LocationSchema.from_orm(new_location)


@router.get(
    "/{location_id}",
    response_model=LocationDetails,
    summary="Get detailed information about the location",
)
async def location_details(
    location_id: uuid.UUID, session: AsyncSession = Depends(get_db)
) -> LocationDetails:
    """
    Get all location information:

    - **name**: each location has a unique name
    - **coordinates**: location's coordinates
    - **open**: open hour
    - **close**: close hour
    - **host_id**: location's owner or None
    - **capacity**: maximum capacity of the location
    """
    location = await LocationService.get_by_id(session, location_id)
    if not location:
        raise LocationNotFound(location_id)

    return LocationDetails.from_orm(location)


@router.put(
    "/{location_id}",
    response_model=LocationDetails,
    summary="Edit the location"
)
async def edit_location(
    location_id: uuid.UUID,
    new_location: LocationEdit,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
) -> LocationDetails:
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
    return LocationDetails.from_orm(location)


@router.put(
    "/{location_id}/rename",
    response_model=LocationDetails,
    summary="Rename the location"
)
async def rename_location(
    location_id: uuid.UUID,
    new_name: str,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
) -> LocationDetails:
    user_id = check_authorization(token)

    location = await LocationService.rename(
        session=session, new_name=new_name, _id=location_id, user_id=user_id
    )
    return LocationDetails.from_orm(location)


@router.delete("/{location_id}", summary="Delete location")
async def delete_location(
    location_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
) -> JSONResponse:
    user_id = check_authorization(token)

    await LocationService.delete(
        session=session, _id=location_id, user_id=user_id
    )
    return JSONResponse(
        status_code=200,
        content={"message": f"Location {location_id} was successfully deleted"},
    )
