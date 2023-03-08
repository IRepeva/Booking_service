import uuid
from abc import abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from booking_api.utils.exceptions import ForbiddenException, NotFoundException
from db.tables.base import Base


@dataclass
class BaseService:
    model: Base = None
    instance: str = None

    @classmethod
    async def create(
            cls,
            session: AsyncSession,
            data: BaseModel,
            user_id: uuid.UUID,
            extra: dict = None,
            commit=True,
    ) -> Base:
        if extra is None:
            extra = {"host_id": user_id}

        data = data.dict()
        data.update(extra)

        instance = cls.model(**data)
        return await cls.save(session, instance, commit)

    @classmethod
    async def edit(
            cls,
            session: AsyncSession,
            new_data: BaseModel,
            _id: uuid.UUID,
            user_id: uuid.UUID,
    ) -> Optional[BaseModel]:
        db_instance = await cls.validate_user(session, _id, user_id)
        await cls.validate(
            data=new_data, session=session, user_id=user_id, _id=_id
        )

        for key, value in new_data.dict().items():
            setattr(db_instance, key, value)

        return await cls.save(session, db_instance)

    @classmethod
    async def delete(
            cls, session: AsyncSession, _id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[BaseModel]:
        db_instance = await cls.validate_user(session, _id, user_id)

        await session.delete(db_instance)
        await session.commit()
        return db_instance

    @classmethod
    async def get_by_id(
            cls, session: AsyncSession, _id: str | uuid.UUID, model: Base = None
    ):
        if not model:
            model = cls.model

        return (
            (await session.execute(select(model).where(model.id == _id)))
            .scalars()
            .first()
        )

    @classmethod
    async def get_first(
            cls, session: AsyncSession, model: Base = None,
            filters: Iterable = ()
    ):
        if model is None:
            model = cls.model

        return (
            (await session.execute(select(model).where(*filters)))
            .scalars()
            .first()
        )

    @classmethod
    async def get_all(
            cls, session: AsyncSession,
            model: Base = None,
            filters: Iterable = ()
    ):
        if model is None:
            model = cls.model

        return (
            (await session.execute(select(model).where(*filters)))
            .scalars()
            .all()
        )

    @classmethod
    async def save(cls, session: AsyncSession, instance: Base, commit=True):
        session.add(instance)
        await session.flush()
        if commit:
            await session.commit()
        return instance

    @classmethod
    async def validate_user(
            cls, session: AsyncSession, _id: uuid.UUID, user_id: uuid.UUID
    ):
        db_instance = await cls.get_by_id(session, _id)
        if not db_instance:
            raise NotFoundException(
                message=f"{cls.instance} with id {_id} was not found",
            )

        if not await cls.is_host(db_instance.host_id, user_id):
            raise ForbiddenException(
                message=f"Only host can modify the {cls.instance} {_id}"
            )

        return db_instance

    @classmethod
    async def is_host(cls, host_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return True if str(host_id) == user_id else False

    @classmethod
    def model_to_dict(cls, model_instance: Base):
        return model_instance.__dict__

    @classmethod
    @abstractmethod
    async def validate(cls, data, *args, **kwargs):
        ...
