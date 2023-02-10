import uuid
from datetime import datetime

from booking_api.models.mixin import MixinModel
from db.tables import SeatType, BookingStatus


class EventSchema(MixinModel):
    id: uuid.UUID | str
    name: str
    start: datetime
    duratioin: int
    location_id: uuid.UUID | str
    host_id: uuid.UUID | str
    movie_id: uuid.UUID | str
    participants: int


class BookingInput(MixinModel):
    event_id: uuid.UUID | str
    seat_id: uuid.UUID | str


class BookingSchema(MixinModel):
    id: uuid.UUID | str
    seat_id: uuid.UUID | str
    event_id: uuid.UUID | str
    guest_id: uuid.UUID | str
    status: int
    price: float

    class Config:
        orm_mode = True


class BookingInfoSchema(MixinModel):
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

    class Config:
        orm_mode = True


class SeatSchema(MixinModel):
    seat_id: uuid.UUID | str
    row: int
    seat: int
    type: SeatType


class EventShemaList(MixinModel):
    id: uuid.UUID | str
    name: str
    start: datetime
    duration: int
    movie_name: str
    location_name: str
    seats: list[SeatSchema]
