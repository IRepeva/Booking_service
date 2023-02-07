import enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Table, sql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import ChoiceType

from db.tables.base import Base


class BookingStatus(enum.Enum):
    EMPTY = 0
    RESERVED = 1
    BOOKED = 2


Booking = Table(
    "booking",
    Base.metadata,
    Column(
        "seat_id",
        UUID(as_uuid=True),
        ForeignKey("seat.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "guest_id",
        UUID(as_uuid=True),
        ForeignKey("guest.id", ondelete="CASCADE"),
        nullable=True,
    ),
    Column(
        "status",
        ChoiceType(BookingStatus, impl=Integer()),
        default=BookingStatus.EMPTY,
        nullable=False,
    ),
    Column("price", Float, default=0),
    Column("modified", DateTime, default=sql.func.now(), onupdate=sql.func.now()),
    Column("created", DateTime, default=sql.func.now()),
)
