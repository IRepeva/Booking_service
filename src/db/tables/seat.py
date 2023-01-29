import enum

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType

from db.tables.base import Base
from db.tables.booking import Booking
from db.tables.mixins import SimplePrimaryKey, TimeStampMixin


class SeatType(enum.Enum):
    UNKNOWN = 0
    ECONOMY = 1
    COMFORT = 2
    VIP = 3


class Seat(SimplePrimaryKey, TimeStampMixin, Base):
    __tablename__ = "seat"

    row = Column(Integer)
    seat = Column(Integer)
    type = Column(
        ChoiceType(SeatType, impl=Integer()), default=SeatType.UNKNOWN, nullable=False
    )

    location_id = Column(
        UUID(as_uuid=True), ForeignKey("location.id", ondelete="CASCADE")
    )
    location = relationship("location", back_populates="seat")

    events = relationship(
        "Event", secondary=Booking, back_populates="seats", uselist=True
    )
    guests = relationship(
        "Guest", secondary=Booking, back_populates="seats", uselist=True
    )
