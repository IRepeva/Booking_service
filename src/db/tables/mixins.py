from sqlalchemy import Column, DateTime, String, sql
from sqlalchemy.dialects.postgresql import UUID


class SimplePrimaryKey:
    id = Column(UUID(as_uuid=True), primary_key=True)


class TimeStampMixin:
    modified = Column(DateTime, default=sql.func.now(), onupdate=sql.func.now())
    created = Column(DateTime, default=sql.func.now())


class UserMixin:
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
