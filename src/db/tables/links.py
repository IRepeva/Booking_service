from sqlalchemy import Column, ForeignKey, Table

from db.tables.base import Base

PurchasedMovieHost = Table(
    "purchased_movies",
    Base.metadata,
    Column("host_id", ForeignKey("host.id", ondelete="CASCADE")),
    Column(
        "purchased_movie_id", ForeignKey("purchased_movie.movie_id", ondelete="CASCADE")
    ),
)
