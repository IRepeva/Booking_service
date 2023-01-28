import uuid
from datetime import datetime, time

from models.mixin import MixinModel


class EventEdit(MixinModel):
    place_id: uuid.UUID | str
    start: datetime
    duration: int
    film_id: uuid.UUID | str
    comments: str | None
    participants: int


class EventInput(EventEdit):
    name: str


class Event(EventInput):
    id: uuid.UUID | str


class PlaceEdit(MixinModel):
    location: str
    capacity: int
    open: time
    close: time


class PlaceInput(PlaceEdit):
    name: str


class Place(PlaceInput):
    id: uuid.UUID | str
    host_id: uuid.UUID | str | None
