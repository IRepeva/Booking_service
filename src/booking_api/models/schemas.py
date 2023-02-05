import uuid
from datetime import datetime, time

from booking_api.models.mixin import MixinModel


class EventEdit(MixinModel):
    location_id: uuid.UUID
    start: datetime
    duration: int
    movie_id: uuid.UUID
    notes: str | None
    participants: int


class EventInput(EventEdit):
    name: str


class Event(EventInput):
    id: uuid.UUID


class PlaceEdit(MixinModel):
    coordinates: str
    capacity: int
    open: time
    close: time


class PlaceInput(PlaceEdit):
    name: str


class Place(PlaceInput):
    id: uuid.UUID
    host_id: uuid.UUID | None
