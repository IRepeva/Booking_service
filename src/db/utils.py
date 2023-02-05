from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config.base import app_cofig

engine = create_async_engine(
    "postgresql+asyncpg://%s:%s@%s:%s/%s"
    % (
        app_cofig.db.user,
        app_cofig.db.password,
        app_cofig.db.host,
        app_cofig.db.port,
        app_cofig.db.db,
    )
)

session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
