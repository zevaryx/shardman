from os import environ
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

__all__ = ["Config", "load_config"]


class Config(BaseModel):
    mongodb: str
    database: str = "shardman"
    secret: str
    token: str
    max_seconds: int = 60
    max_shards: Optional[int] = None
    cors_origins: Optional[list[str]] = None
    webhook_url: Optional[str] = None
    webhook_content: Optional[str] = None

    @validator("max_shards", "cors_origins", "webhook_url", "webhook_content", pre=True)
    def allow_none(cls, v):
        if v == "":
            return None
        return v


_config: Config = None


def load_config() -> Config:
    global _config
    if _config is None:
        load_dotenv()

        mongodb = environ.get("MONGO_URI")
        database = environ.get("DATABASE", "shardman")
        secret = environ.get("SECRET_KEY")
        token = environ.get("BOT_TOKEN")
        max_seconds = int(environ.get("MAX_SECONDS", 60))
        max_shards = environ.get("MAX_SHARDS", None)
        cors_origins = environ.get("CORS_ORIGINS", None)

        webhook_url = environ.get("WEBHOOK_URL", None)
        webhook_content = environ.get("WEBHOOK_CONTENT", None)

        if max_shards:
            max_shards = int(max_shards)

        if cors_origins:
            cors_origins = cors_origins.split(",")

        _config = Config(
            mongodb=mongodb,
            secret=secret,
            database=database,
            token=token,
            max_seconds=max_seconds,
            max_shards=max_shards,
            cors_origins=cors_origins,
            webhook_url=webhook_url,
            webhook_content=webhook_content,
        )

    return _config
