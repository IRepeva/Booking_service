from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from db.tables.base import Base
from db.tables.booking import Booking
from db.tables.mixins import SimplePrimaryKey, TimeStampMixin


class Event(SimplePrimaryKey, TimeStampMixin, Base):
    __tablename__ = "event"

    name = Column(String)
    start = Column(DateTime, nullable=False)
    duration = Column(Integer, comment="Event duration, s", nullable=False)
    notes = Column(String, comment="Extra information")
    participants = Column(Integer, comment="Number of participants", nullable=False)

    movie_id = Column(
        "movie_id", ForeignKey("purchased_movie.movie_id", ondelete="CASCADE")
    )
    location_id = Column(
        UUID(as_uuid=True), ForeignKey("location.id", ondelete="CASCADE")
    )
    host_id = Column(UUID(as_uuid=True), ForeignKey("host.id", ondelete="CASCADE"))

    location = relationship("Location", back_populates="events")
    host = relationship("Host", back_populates="event")

    seats = relationship(
        "Seat", secondary=Booking, back_populates="events", uselist=True
    )
    guests = relationship(
        "Guest", secondary=Booking, back_populates="events", uselist=True
    )
