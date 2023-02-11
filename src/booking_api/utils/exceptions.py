class BaseAPIException(Exception):
    message: str = ""
    extras: dict = {}


class NotFoundException(BaseAPIException):
    def __init__(self, message: str, extras: dict):
        self.message = message
        self.extras = extras


class UniqueConflictException(BaseAPIException):
    def __init__(self, message: str, extras: dict):
        self.message = message
        self.extras = extras


class ForbiddenException(BaseAPIException):
    def __init__(self, message: str, extras: dict):
        self.message = "Method not allowed"
        self.extras = extras


class BookingNotFoundException(NotFoundException):
    def __init__(self, booking_id: str):
        self.message = f"Booking not found by given ID"
        self.extras = {"booking_id": booking_id}


class EventNotFoundException(NotFoundException):
    def __init__(self, event_id: str):
        self.message = f"Event not found by given ID"
        self.extras = {"event_id": event_id}


class SeatNotFoundException(NotFoundException):
    def __init__(self, seat_id: str):
        self.message = f"Seat not found by given ID"
        self.extras = {"seat_id": seat_id}
