from functools import lru_cache
from logging import config as logging_config

from pydantic import BaseSettings, Field

from config.logger import LOGGING

# LOGGING
logging_config.dictConfig(LOGGING)


class PostgresConfig(BaseSettings):
    user: str = Field(default="admin")
    password: str = Field(default="admin")
    db: str = Field(default="booking")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)

    class Config:
        env_prefix = "postgres_"

    @property
    def dsn(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisSettings(BaseSettings):
    url: str = "redis://127.0.0.1:6379"

    class Config:
        env_prefix = "REDIS_"


class Settings(BaseSettings):
    project_name = Field("tickets_booker", env="PROJECT_NAME")
    free_films_url = "http://127.0.0.1:8000/booking_api/v1/movies/free_movies"
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisSettings = RedisSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
