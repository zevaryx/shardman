from os import environ

from dotenv import load_dotenv
from pydantic import BaseModel

__all__ = ["Config", "load_config"]


class Config(BaseModel):
    mongodb: str
    database: str
    secret: str
    max_shards: int
    max_seconds: int


_config: Config = None


def load_config() -> Config:
    global _config
    if _config is None:
        load_dotenv()

        mongodb = environ.get("MONGO_URI")
        database = environ.get("DATABASE", "shardman")
        secret = environ.get("SECRET_KEY")
        max_shards = int(environ.get("MAX_SHARDS"))
        max_seconds = int(environ.get("MAX_SECONDS", 60))

        _config = Config(
            mongodb=mongodb, secret=secret, database=database, max_shards=max_shards, max_seconds=max_seconds
        )

    return _config
