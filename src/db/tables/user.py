from sqlalchemy.orm import relationship

from db.tables.base import Base
from db.tables.booking import Booking
from db.tables.links import PurchasedMovieHost
from db.tables.mixins import SimplePrimaryKey, TimeStampMixin, UserMixin


class Guest(SimplePrimaryKey, TimeStampMixin, UserMixin, Base):
    __tablename__ = "guest"
    events = relationship(
        "Event", secondary=Booking, back_populates="guests", uselist=True
    )
    seats = relationship(
        "Seat", secondary=Booking, back_populates="guests", uselist=True
    )


class Host(SimplePrimaryKey, TimeStampMixin, UserMixin, Base):
    __tablename__ = "host"

    events = relationship("Event", back_populates="user", uselist=True)
    movies = relationship(
        "PurchasedMovie",
        secondary=PurchasedMovieHost,
        back_populates="owners",
        uselist=True,
    )
