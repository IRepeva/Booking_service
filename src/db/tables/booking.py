import enum

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import ChoiceType

from db.tables.base import Base
from db.tables.mixins import SimplePrimaryKey, TimeStampMixin


class BookingStatus(enum.Enum):
    EMPTY = 0
    RESERVED = 1
    BOOKED = 2


class Booking(SimplePrimaryKey, TimeStampMixin, Base):
    __tablename__ = 'booking'

    seat_id = Column(
        'seat_id',
        UUID(as_uuid=True),
        ForeignKey("seat.id", ondelete="CASCADE"),
        nullable=False
    )
    event_id = Column(
        'event_id',
        UUID(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        nullable=False
    )
    guest_id = Column(
        'guest_id',
        UUID(as_uuid=True),
        ForeignKey("guest.id", ondelete="CASCADE"),
        nullable=True
    )
    status = Column(
        ChoiceType(BookingStatus, impl=Integer()),
        default=BookingStatus.EMPTY,
        nullable=False
    )
