from sqlalchemy.orm import relationship

from db.tables.base import Base
from db.tables.booking import Booking
from db.tables.links import PurchasedMovieHost
from db.tables.mixins import SimplePrimaryKey, TimeStampMixin, UserMixin


class Guest(SimplePrimaryKey, TimeStampMixin, UserMixin, Base):
    __tablename__ = "guest"
    guest_events = relationship(
        "Event", secondary=Booking.__table__, back_populates="event_guests", uselist=True
    )
    guest_seats = relationship(
        "Seat", secondary=Booking.__table__, back_populates="seat_guests", uselist=True
    )


class Host(SimplePrimaryKey, TimeStampMixin, UserMixin, Base):
    __tablename__ = "host"

    events = relationship("Event", back_populates="host", uselist=True)
    movies = relationship(
        "PurchasedMovie",
        secondary=PurchasedMovieHost,
        back_populates="owners",
        uselist=True,
    )
