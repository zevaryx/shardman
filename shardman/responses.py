from datetime import datetime

from pydantic import BaseModel


class ConnectConfirmed(BaseModel):
    shard_id: int
    max_shards: int
    session_id: str
    sleep_duration: float = 0.0


class ShardResponse(BaseModel):
    shard_id: int
    last_beat: datetime
    session_id: str
    guild_count: int | None = None
    latency: float | None = None
