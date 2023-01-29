from sqlalchemy import Column, Date, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from db.tables.base import Base
from db.tables.links import PurchasedMovieHost
from db.tables.mixins import TimeStampMixin


class PurchasedMovie(TimeStampMixin, Base):
    __tablename__ = "purchased_movie"

    movie_id = Column("movie_id", UUID(as_uuid=True), primary_key=True)
    movie_name = Column(String)
    release_date = Column(Date)

    owners = relationship(
        "Host", secondary=PurchasedMovieHost, back_populates="movies", uselist=True
    )
