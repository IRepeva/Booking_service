import uuid
from datetime import datetime

from models.mixin import MixinModel


class EventInput(MixinModel):
    name: str
    place_id: uuid.UUID | str
    start: datetime
    duration: int
    host_id: uuid.UUID | str
    film_id: uuid.UUID | str
    comments: str | None
    participants: int


class Event(EventInput):
    id: uuid.UUID | str
