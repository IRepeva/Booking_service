from enum import Enum
from functools import lru_cache
from logging import config as logging_config

from core.logger import LOGGING
from pydantic import BaseSettings, Field

# LOGGING
logging_config.dictConfig(LOGGING)


class PostgresSettings(BaseSettings):
    user: str = 'postgres'
    password: str = 'password'
    host: str = 'localhost'
    port: int = 5432
    db: str = 'movies'

    @property
    def dsn(self):
        return f'postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}'

    class Config:
        env_prefix = "POSTGRES_"


class RedisSettings(BaseSettings):
    url: str = 'redis://127.0.0.1:6379'

    class Config:
        env_prefix = "REDIS_"


class Settings(BaseSettings):
    project_name = Field('tickets_booker', env='PROJECT_NAME')
    free_films_url = 'http://127.0.0.1:8000/api/fake/free_movies'
    postgres: PostgresSettings = PostgresSettings()
    redis: RedisSettings = RedisSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
