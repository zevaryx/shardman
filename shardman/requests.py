from typing import Any

from pydantic import BaseModel


class Heartbeat(BaseModel):
    session_id: str
    guild_count: int | None = None
    latency: float | None = None

    extra: Any | None = None


class SessionID(BaseModel):
    session_id: str

