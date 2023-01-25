import uuid

import sqlalchemy
from sqlalchemy.dialects.postgresql import UUID

from db.postgres import Base


class Event(Base):
    __tablename__ = 'event'

    id = sqlalchemy.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = sqlalchemy.Column(sqlalchemy.String(30), unique=True, index=True)
    place_id = sqlalchemy.Column(UUID(as_uuid=True), nullable=False)
    start = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    duration = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    host_id = sqlalchemy.Column(UUID(as_uuid=True), nullable=False)
    film_id = sqlalchemy.Column(UUID(as_uuid=True), nullable=False)
    participants = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    comments = sqlalchemy.Column(sqlalchemy.Text)


class Place(Base):
    __tablename__ = 'place'

    id = sqlalchemy.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name = sqlalchemy.Column(sqlalchemy.String(30), unique=True, index=True)
    location = sqlalchemy.Column(sqlalchemy.String(30))
    capacity = sqlalchemy.Column(sqlalchemy.Integer)
    open = sqlalchemy.Column(sqlalchemy.Time)
    close = sqlalchemy.Column(sqlalchemy.Time)


class PurchasedFilm(Base):
    __tablename__ = 'purchased_film'

    id = sqlalchemy.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = sqlalchemy.Column(UUID(as_uuid=True), nullable=False)
    film_id = sqlalchemy.Column(UUID(as_uuid=True), nullable=False)
