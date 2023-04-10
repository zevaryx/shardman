from pydantic import BaseModel


class ConnectConfirmed(BaseModel):
    shard: int
    max_shards: int
    session_id: str
    sleep_duration: float = 0.0
