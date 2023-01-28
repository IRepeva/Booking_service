import enum
import uuid

import sqlalchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType

from db.postgres import Base


class EventSeatStatus(enum.Enum):
    EMPTY = 0
    RESERVED = 1
    BOOKED = 2


class SeatType(enum.Enum):
    UNKNOWN = 0
    ECONOMY = 1
    COMFORT = 2
    VIP = 3


EventSeat = sqlalchemy.Table(
    "event_seat",
    Base.metadata,
    sqlalchemy.Column(
        "seat_id",
        UUID(as_uuid=True),
        sqlalchemy.ForeignKey("seat.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sqlalchemy.Column(
        "event_id",
        UUID(as_uuid=True),
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sqlalchemy.Column(
        "status",
        ChoiceType(EventSeatStatus, impl=sqlalchemy.Integer()),
        default=EventSeatStatus.EMPTY,
        nullable=False,
    ),
    sqlalchemy.Column("price", sqlalchemy.Float),
)


class Seat(Base):
    __tablename__ = "seat"

    id = sqlalchemy.Column(UUID(as_uuid=True), primary_key=True)
    row = sqlalchemy.Column(sqlalchemy.Integer)
    seat = sqlalchemy.Column(sqlalchemy.Integer)
    type = sqlalchemy.Column(
        ChoiceType(SeatType, impl=sqlalchemy.Integer()),
        default=SeatType.UNKNOWN, nullable=False
    )
    place_id = sqlalchemy.Column(
        UUID(as_uuid=True),
        sqlalchemy.ForeignKey("place.id", ondelete="CASCADE")
    )
    place = relationship("Place", back_populates="seat")

    events = relationship("Event", secondary=EventSeat, back_populates="seats")


class Event(Base):
    __tablename__ = 'event'

    id = sqlalchemy.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = sqlalchemy.Column(sqlalchemy.String(30), unique=True, index=True)
    place_id = sqlalchemy.Column(UUID(as_uuid=True), sqlalchemy.ForeignKey("place.id", ondelete="CASCADE"), nullable=False)
    start = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    duration = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    host_id = sqlalchemy.Column(UUID(as_uuid=True), nullable=False)
    film_id = sqlalchemy.Column(UUID(as_uuid=True), nullable=False)
    participants = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    comments = sqlalchemy.Column(sqlalchemy.Text)

    place = relationship("Place", back_populates="event")
    seats = relationship("Seat", secondary=EventSeat, back_populates="events")


class Place(Base):
    __tablename__ = 'place'

    id = sqlalchemy.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = sqlalchemy.Column(sqlalchemy.String(30), unique=True, index=True)
    location = sqlalchemy.Column(sqlalchemy.String(30), nullable=False)
    capacity = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    host_id = sqlalchemy.Column(UUID(as_uuid=True))
    open = sqlalchemy.Column(sqlalchemy.Time, nullable=False)
    close = sqlalchemy.Column(sqlalchemy.Time, nullable=False)

    seat = relationship("Seat", back_populates="place", uselist=True)
    event = relationship("Event", back_populates="place", uselist=True)


class PurchasedFilm(Base):
    __tablename__ = 'purchased_film'

    id = sqlalchemy.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = sqlalchemy.Column(UUID(as_uuid=True), nullable=False)
    film_id = sqlalchemy.Column(UUID(as_uuid=True), nullable=False)
