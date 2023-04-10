from typing import Any

from pydantic import BaseModel


class Hearbeat(BaseModel):
    session_id: str
    guild_count: int | None = None
    latency: float | None = None

    extra: Any | None = None
