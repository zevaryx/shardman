from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ConnectConfirmed(BaseModel):
    shard_id: int
    max_shards: int
    session_id: str
    sleep_duration: float = 0.0


class ShardProjection(BaseModel):
    shard_id: int
    last_beat: datetime
    guild_count: int | None = None
    latency: float | None = None


class ShardProjectionExtra(ShardProjection):
    extra: Any | None = None


class Status(BaseModel):
    total_shards: int
    shards: list[ShardProjection]
