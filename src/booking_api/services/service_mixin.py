from sqlalchemy.ext.asyncio import AsyncSession


class ServiceMixin:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session
