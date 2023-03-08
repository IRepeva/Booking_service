import uuid
from datetime import datetime
from datetime import time

from booking_api.models.mixin import MixinModel
from db.tables import SeatType, BookingStatus


class SeatInput(MixinModel):
    row: int
    seat: int
    type: SeatType

    class Config:
        orm_mode = True


class SeatSchema(SeatInput):
    id: uuid.UUID

    class Config:
        orm_mode = True


class EventInput(MixinModel):
    name: str
    location_id: uuid.UUID
    start: datetime
    duration: int
    movie_id: uuid.UUID
    notes: str | None
    participants: int


class EventSchema(EventInput):
    id: uuid.UUID

    class Config:
        orm_mode = True


class EventDetails(EventInput):
    seats: list[SeatSchema]

    class Config:
        orm_mode = True


class LocationEdit(MixinModel):
    coordinates: str
    capacity: int
    open: time
    close: time


class LocationInput(LocationEdit):
    name: str


class LocationDetails(LocationInput):
    host_id: uuid.UUID | None

    class Config:
        orm_mode = True


class LocationSchema(LocationDetails):
    id: uuid.UUID


class BookingInput(MixinModel):
    event_id: uuid.UUID
    seat_id: uuid.UUID | list[uuid.UUID]


class BookingBase(MixinModel):
    event_id: uuid.UUID
    status: int | BookingStatus


class BookingSchema(BookingBase):
    id: uuid.UUID
    guest_id: uuid.UUID

    class Config:
        orm_mode = True


class BookingDetails(BookingBase):
    seats: SeatSchema
    event_name: str
    event_start: datetime
    event_duration: int

    class Config:
        orm_mode = True
