import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from booking_api.models.schemas import (
    BookingInput, BookingSchema, BookingDetails
)
from booking_api.services.booking import BookingService
from booking_api.utils.authentication import check_authorization, security
from db.utils.postgres import get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingSchema, summary="Create booking")
async def create_booking(
        booking: BookingInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
):
    user_id = check_authorization(token)
    return await BookingService.create(session=session, data=booking,
                                       user_id=user_id)


@router.get("/{booking_id}", response_model=BookingDetails,
            summary="Get booking")
async def get_booking(
        booking_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
) -> BookingDetails:
    check_authorization(token)
    return await BookingService.get_booking(session, booking_id)


@router.get("/", response_model=list[BookingDetails],
            summary="Get all user bookings")
async def get_bookings(
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
) -> list[BookingDetails]:
    user_id = check_authorization(token)
    return await BookingService.get_bookings(session, user_id=user_id)


@router.delete("/{booking_id}", summary="Delete booking")
async def delete_booking(
        booking_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
):
    user_id = check_authorization(token)
    await BookingService.delete(session, _id=booking_id, user_id=user_id)

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={"message": f"Booking {booking_id} was successfully deleted"},
    )


@router.put("/update_status/{booking_id}", summary="Update booking status")
async def update_booking_status(
        booking_id: uuid.UUID,
        status: int,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
):
    user_id = check_authorization(token)
    return await BookingService.update_booking_status(
        session=session,
        booking_id=booking_id,
        new_status=status,
        user_id=user_id
    )


@router.put("/{booking_id}", summary="Update booking")
async def update_booking(
        booking_id: uuid.UUID,
        new_booking: BookingInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
):
    user_id = check_authorization(token)
    booking = await BookingService.edit(
        session=session, new_data=new_booking, _id=booking_id, user_id=user_id
    )
    return BookingSchema.from_orm(booking)
