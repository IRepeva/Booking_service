from pydantic import BaseSettings, Field


class PostgresConfig(BaseSettings):
    user: str = Field(default="admin")
    password: str = Field(default="admin")
    db: str = Field(default="booking")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)

    class Config:
        env_prefix = "postgres"


class BookingsConfig(BaseSettings):
    db: PostgresConfig = PostgresConfig()


app_cofig = BookingsConfig()
