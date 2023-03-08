import uuid
from http import HTTPStatus
from typing import Iterable

from fastapi import HTTPException


class NotFoundException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=message)


class BadRequestException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=message)


class ForbiddenException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=HTTPStatus.FORBIDDEN, detail=message)


class BookingNotFound(NotFoundException):
    def __init__(self, booking_id: uuid.UUID):
        super().__init__(message=f'Booking {booking_id} was not found')


class EventNotFound(NotFoundException):
    def __init__(self, event_id: uuid.UUID):
        super().__init__(message=f'Event {event_id} was not found')


class LocationNotFound(NotFoundException):
    def __init__(self, location_id: uuid.UUID):
        super().__init__(message=f'Location {location_id} was not found')


class SeatNotFound(NotFoundException):
    def __init__(self, seat_id: uuid.UUID | Iterable):
        super().__init__(message=f'Seat(s) {seat_id} was not found')
