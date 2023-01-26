import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from db.postgres import get_db
from models.schemas import Place, PlaceInput, PlaceEdit
from services.places import PlaceService
from utils.authentication import security, get_token_payload

router = APIRouter()


@router.post('/add', response_model=Place, summary="Add event's location")
async def add_place(
        place: PlaceInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
) -> Place:
    """
    Create place with the following data:

    - **name**: each place has a unique name
    - **location**: place's location
    - **open**: open hour
    - **close**: close hour
    - **capacity**: maximum capacity of the place
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    await PlaceService.validate_name(session, name=place.name)
    new_place = await PlaceService.create(
        session=session, data=place, user_id=user_id
    )
    return PlaceService.model_to_dict(new_place)


@router.get(
    '/{place_id}',
    response_model=Place,
    summary="Get detailed information about the place"
)
async def place_details(
        place_id: str,
        session: AsyncSession = Depends(get_db)
) -> Place:
    """
    Get all place information:

    - **id**: unique id of the place
    - **name**: each place has a unique name
    - **location**: place's location
    - **open**: open hour
    - **close**: close hour
    - **host_id**: place's owner or None
    - **capacity**: maximum capacity of the place
    """
    place = await PlaceService.get_by_id(session, place_id)
    if not place:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Place with id {place_id} is not found'
        )

    return PlaceService.model_to_dict(place)


@router.put(
    "/{place_id}/edit", response_model=Place, summary="Edit the place"
)
async def edit_place(
        place_id: uuid.UUID,
        new_place: PlaceEdit,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
) -> Place:
    """
    Change the place:

    - **location**: place's location
    - **open**: open hour
    - **close**: close hour
    - **capacity**: maximum capacity of the place
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    place = await PlaceService.edit(
        session=session, new_data=new_place, _id=place_id, user_id=user_id
    )
    return PlaceService.model_to_dict(place)


@router.put(
    "/{place_id}/rename", response_model=Place, summary="Rename the place"
)
async def rename_place(
        place_id: uuid.UUID,
        new_name: str,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
) -> Place:
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    place = await PlaceService.rename(
        session=session, new_name=new_name, _id=place_id, user_id=user_id
    )
    return PlaceService.model_to_dict(place)


@router.delete("/{place_id}/delete", summary="Delete place")
async def delete_place(
        place_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
) -> JSONResponse:
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    await PlaceService.delete(
        session=session, _id=place_id, user_id=user_id
    )
    return JSONResponse(
        status_code=200,
        content={"message": f"Place {place_id} was successfully deleted"}
    )
