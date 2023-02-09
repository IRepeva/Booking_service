import uuid
from datetime import datetime, time

from booking_api.models.mixin import MixinModel


class EventInput(MixinModel):
    name: str
    location_id: uuid.UUID
    start: datetime
    duration: int
    movie_id: uuid.UUID
    notes: str | None
    participants: int


class Event(EventInput):
    id: uuid.UUID


class LocationEdit(MixinModel):
    coordinates: str
    capacity: int
    open: time
    close: time


class LocationInput(LocationEdit):
    name: str


class Location(LocationInput):
    id: uuid.UUID
    host_id: uuid.UUID | None


class SeatInput(MixinModel):
    id: uuid.UUID
    row: int
    seat: int
    type: int

