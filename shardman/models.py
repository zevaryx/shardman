from datetime import datetime

from beanie import Document


class Shard(Document):
    shard_id: int
    last_beat: datetime
    session_id: str
    valid_session: bool = True


all_models = [Shard]
