from datetime import datetime
from typing import Any

from beanie import Document


class Shard(Document):
    shard_id: int
    last_beat: datetime
    """The last time the shard sent a heartbeat."""
    session_id: str
    """The session ID of the provisioned shard."""

    guild_count: int | None = None
    latency: float | None = None
    """The latency of the Shard's gateway connection."""
    extra: Any | None = None

    class Config:
        arbitrary_types_allowed = True


all_models = [Shard]
