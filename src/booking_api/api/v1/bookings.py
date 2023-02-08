from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from booking_api.models.booking import BookingInput
from booking_api.services.booking import BookingService
from booking_api.utils.authentication import security, get_token_payload
from db.utils.postgres import get_db

router = APIRouter(tags=["bookings"])


@router.post('/create_booking', summary='Createbooking')
async def create_booking(
        booking: BookingInput,
        session: AsyncSession = Depends(get_db),
        token=Depends(security)
):
    """
    Create Booking
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    new_booking = await BookingService(session).create(
        data=booking, user_id=user_id
    )
    return new_booking


@router.get('/booking/{booking_id}', summary='Get booking')
async def get_booking(
        booking_id: str,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
):
    """
    Get booking
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    events = await BookingService(session).get_booking(
        booking_id=booking_id
    )
    return events


@router.get('/booking/', summary='Get all user bookings')
async def get_bookings(
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
):
    """
    Get all user bookings
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    bookings = await BookingService(session).get_bookings(
        user_id=user_id
    )
    return bookings


@router.delete('/booking/{booking_id}', summary='Get event')
async def delete_booking(
        booking_id: str,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
):
    """
    Get all events for which you can book a seat
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    events = await BookingService(session).delete_booking(
        booking_id=booking_id,
        user_id=user_id
    )
    return events


@router.put('/booking/{booking_id}/edit', summary='Update booking status')
async def update_booking(
        booking_id: str,
        status: int,
        session: AsyncSession = Depends(get_db),
        token=Depends(security),
):
    """
    Update Booking
    """
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    bookings = await BookingService(session).update_booking_status(
        new_status=status,
        booking_id=booking_id,
        user_id=user_id
    )
    return bookings
