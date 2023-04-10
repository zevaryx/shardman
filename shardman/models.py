from datetime import datetime

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


all_models = [Shard]
