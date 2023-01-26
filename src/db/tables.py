import enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Time,
    sql,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy_utils import ChoiceType

Base = declarative_base()


class SeatType(enum.Enum):
    UNKNOWN = 0
    ECONOMY = 1
    COMFORT = 2
    VIP = 3


class EventSeatStatus(enum.Enum):
    EMPTY = 0
    RESERVED = 1
    BOOKED = 2


EventSeat = Table(
    "event_seat",
    Base.metadata,
    Column(
        "seat_id",
        UUID(as_uuid=True),
        ForeignKey("seat.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "event_id",
        UUID(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "status",
        ChoiceType(EventSeatStatus, impl=Integer()),
        default=EventSeatStatus.EMPTY,
        nullable=False,
    ),
    Column("price", Float, default=0),
)


GuestEvent = Table(
    "guest_event",
    Base.metadata,
    Column("guest_id", ForeignKey("guest.id", ondelete="CASCADE"), primary_key=True),
    Column("event_id", ForeignKey("event.id", ondelete="CASCADE"), primary_key=True),
    Column("event_score", Integer),
    CheckConstraint("host_score > 0 AND host_score < 10"),
    CheckConstraint("event_score > 0 AND event_score < 10"),
)


class SimplePrimaryKey:
    id = Column(UUID(as_uuid=True), primary_key=True)


class TimeStampMixin:
    modified = Column(DateTime, default=sql.func.now(), onupdate=sql.func.now())
    created = Column(DateTime, default=sql.func.now())


class UserMixin:

    rating = Column(Float)
    events_num = Column(Integer, comment="number of events")

    __table_args__ = (CheckConstraint("rating > 0  AND rating < 10"),)


class Guest(SimplePrimaryKey, TimeStampMixin, UserMixin, Base):
    __tablename__ = "guest"

    events = relationship("Event", secondary=GuestEvent, back_populates="guests")


class Host(SimplePrimaryKey, TimeStampMixin, UserMixin, Base):
    __tablename__ = "host"

    events = relationship("Event", back_populates="user", uselist=True)
    movies = relationship("PurchasedMovie", back_populates="user", uselist=True)


class Place(SimplePrimaryKey, TimeStampMixin, Base):
    __tablename__ = "place"

    name = Column(String, comment="Place name", unique=True)
    location = Column(String, comment="Place location", nullable=False)
    capacity = Column(Integer, comment="Number of seats", nullable=False)
    open = Column(Time, comment="Place opening time")
    close = Column(Time, comment="Place closing time")

    seats = relationship("Seat", back_populates="place", uselist=True)
    events = relationship("Event", back_populates="place", uselist=True)


class Seat(SimplePrimaryKey, TimeStampMixin, Base):
    __tablename__ = "seat"

    row = Column(Integer)
    seat = Column(Integer)
    type = Column(
        ChoiceType(SeatType, impl=Integer()), default=SeatType.UNKNOWN, nullable=False
    )

    place_id = Column(UUID(as_uuid=True), ForeignKey("place.id", ondelete="CASCADE"))
    place = relationship("Place", back_populates="seat")
    events = relationship(
        "Event", secondary=EventSeat, back_populates="seats", uselist=True
    )


class Event(SimplePrimaryKey, TimeStampMixin, Base):
    __tablename__ = "event"

    name = Column(String)
    start = Column(DateTime, nullable=False)
    duration = Column(Integer, comment="Event duration, s", nullable=False)
    movie_id = Column(UUID(as_uuid=True))
    notes = Column(String, comment="Extra information", nullable=False)
    participants = Column(Integer, comment="Number of participants", nullable=False)

    place_id = Column(UUID(as_uuid=True), ForeignKey("place.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("host.id", ondelete="CASCADE"))

    place = relationship("Place", back_populates="event")
    user = relationship("Host", back_populates="event")
    seats = relationship(
        "Seat", secondary=EventSeat, back_populates="events", uselist=True
    )
    guests = relationship(
        "Guest", secondary=GuestEvent, back_populates="events", uselist=True
    )


class PurchasedMovie(TimeStampMixin):
    movie_id = Column(UUID(as_uuid=True), primary_key=True)
    movie_name = Column(String)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("host.id", ondelete="CASCADE"), primary_key=True
    )

    user = relationship("Host", back_populates="movie")
