import uuid
from abc import abstractmethod
from http import HTTPStatus
from typing import Iterable, Optional

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from booking_api.models.schemas import Location
from db.tables import Event
from db.tables.base import Base


class BaseService:
    model: Base = None
    instance: str = None

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        data: BaseModel,
        user_id: str | uuid.UUID,
        commit=True,
    ) -> Base:
        data = data.dict()
        data.update({"host_id": user_id})

        instance = cls.model(**data)
        return await cls.save(session, instance, commit)

    @classmethod
    @abstractmethod
    async def edit(
        cls,
        session: AsyncSession,
        new_data: BaseModel,
        _id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[BaseModel]:
        ...

    @classmethod
    async def delete(
        cls, session: AsyncSession, _id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Location]:
        db_instance = await cls.validate_host(session, _id, user_id)

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
        cls, session: AsyncSession, model: Base = None, filters: Iterable = ()
    ):
        if model is None:
            model = cls.model

        return (await session.execute(select(model).where(*filters))).scalars().first()

    @classmethod
    async def get_all(
        cls, session: AsyncSession, model: Base = None, filters: Iterable = ()
    ):
        if model is None:
            model = cls.model

        return (await session.execute(select(model).where(*filters))).scalars().all()

    @classmethod
    async def save(cls, session: AsyncSession, instance: Base, commit=True):
        session.add(instance)
        await session.flush()
        if commit:
            await session.commit()
        await session.refresh(instance)
        return instance

    @classmethod
    async def validate_host(
        cls, session: AsyncSession, _id: uuid.UUID, user_id: uuid.UUID
    ):
        db_instance = await cls.get_by_id(session, _id)
        if not db_instance:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"{cls.instance} with id {_id} is not found",
            )

        if not await cls.is_host(db_instance.host_id, user_id):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"Only host can modify the {cls.instance} {_id}",
            )

        return db_instance

    @classmethod
    async def validate_name(cls, session: AsyncSession, name: str):
        db_instance = await cls.get_first(session, filters=(Event.name == name,))
        if db_instance:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"{cls.instance} with name {name} already exists",
            )

    @classmethod
    async def is_host(cls, host_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return True if str(host_id) == user_id else False

    @classmethod
    def model_to_dict(cls, model_instance: Base):
        return model_instance.__dict__
