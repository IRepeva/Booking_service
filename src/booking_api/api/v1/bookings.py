from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from booking_api.models.booking import BookingInput
from booking_api.services.booking import BookingService
from booking_api.utils.authentication import check_authorization, security
from db.utils.postgres import get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", summary="Create booking")
async def create_booking(
    booking: BookingInput,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
):
    """
    Create Booking
    """
    user_id = check_authorization(token)
    new_booking = await BookingService(session).create(
        data=booking, user_id=user_id
    )
    return new_booking


@router.get("/{booking_id}", summary="Get booking")
async def get_booking(
    booking_id: str,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
):
    """
    Get booking
    """
    check_authorization(token)
    events = await BookingService(session).get_booking(
        booking_id=booking_id
    )
    return events


@router.get("/", summary="Get all user bookings")
async def get_bookings(
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
):
    """
    Get all user bookings
    """
    user_id = check_authorization(token)
    bookings = await BookingService(session).get_bookings(
        user_id=user_id
    )
    return bookings


@router.delete("/{booking_id}", summary="Get event")
async def delete_booking(
    booking_id: str,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
):
    """
    Get all events for which you can book a seat
    """
    user_id = check_authorization(token)
    events = await BookingService(session).delete_booking(
        booking_id=booking_id, user_id=user_id
    )
    return events


@router.put("/{booking_id}", summary="Update booking status")
async def update_booking(
    booking_id: str,
    status: int,
    session: AsyncSession = Depends(get_db),
    token=Depends(security),
):
    """
    Update Booking
    """
    user_id = check_authorization(token)
    bookings = await BookingService(session).update_booking_status(
        booking_id=booking_id,
        new_status=status,
        user_id=user_id
    )
    return bookings
