from os import environ
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

__all__ = ["Config", "load_config"]


class Config(BaseModel):
    mongodb: str
    database: str
    secret: str
    token: str
    max_seconds: int
    max_shards: Optional[int] = None


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
        max_shards = environ.get("MAX_SHARDS")
        if max_shards:
            max_shards = int(max_shards)

        _config = Config(
            mongodb=mongodb,
            secret=secret,
            database=database,
            token=token,
            max_seconds=max_seconds,
            max_shards=max_shards,
        )

    return _config
