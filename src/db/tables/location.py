from sqlalchemy import Column, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from db.tables.base import Base
from db.tables.mixins import SimplePrimaryKey, TimeStampMixin


class Location(SimplePrimaryKey, TimeStampMixin, Base):
    __tablename__ = "location"

    name = Column(String, comment="location name", unique=True, nullable=False)
    coordinates = Column(String, comment="location location", nullable=False)
    capacity = Column(Integer, comment="Number of seats", nullable=False)
    open = Column(Time, comment="location opening time", nullable=False)
    close = Column(Time, comment="location closing time", nullable=False)
    host_id = Column(
        "host_id", UUID(as_uuid=True), ForeignKey("host.id", ondelete="CASCADE")
    )

    seats = relationship("Seat", back_populates="location", uselist=True, lazy='selectin')
    events = relationship("Event", back_populates="location", uselist=True)
