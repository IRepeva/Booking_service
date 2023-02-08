import uuid
import enum
from datetime import datetime
from pydantic import BaseModel

from db.tables import SeatType


class BookingStatus(enum.Enum):
    EMPTY = 0
    RESERVED = 1
    BOOKED = 2


class EventSchema(BaseModel):
    id: uuid.UUID | str
    name: str
    start: datetime
    duratioin: int
    location_id: uuid.UUID | str
    host_id: uuid.UUID | str
    movie_id: uuid.UUID | str
    participants: int


class BookingInput(BaseModel):
    event_id: uuid.UUID | str
    seat_id: uuid.UUID | str


class BookingSchema(BaseModel):
    id: uuid.UUID | str
    seat_id: uuid.UUID | str
    event_id: uuid.UUID | str
    guest_id: uuid.UUID | str
    status: BookingStatus
    price: float


class BookingInfoSchema(BaseModel):
    id: uuid.UUID | str
    seat_id: uuid.UUID | str
    seat_row: int
    seat_seat: int
    seat_type: SeatType
    event_id: uuid.UUID | str
    event_name: str
    event_start: datetime
    event_duration: int
    guest_id: uuid.UUID | str
    status: BookingStatus
    price: float


class SeatSchema(BaseModel):
    seat_id: uuid.UUID | str
    row: int
    seat: int
    type: SeatType


class EventShemaList(BaseModel):
    id: uuid.UUID | str
    name: str
    start: datetime
    duration: int
    movie_name: str
    location_name: str
    seats: list[SeatSchema]
