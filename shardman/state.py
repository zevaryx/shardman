import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum

import ulid
from aiohttp import ClientSession
from beanie.operators import In

from shardman.config import load_config
from shardman.models import Shard


class AlertType(Enum):
    Connect = 65280
    Disconnect = 16711680


class StateManager:
    def __init__(self):
        self._config = load_config()
        self._token = self._config.token
        self.total_shards = 1
        self.max_concurrency = 1
        self.__session = ClientSession(
            base_url="https://discord.com",
            headers={"Authorization": f"Bot {self._token}"},
        )
        self.lock = asyncio.Lock()
        self.buckets = defaultdict(list)

    async def check_sessions(self):
        td = timedelta(seconds=self._config.max_seconds)

        # In case of restart, wait MAX_SECONDS before starting task
        await asyncio.sleep(self._config.max_seconds)

        while True:
            async for shard in Shard.find():
                if shard.last_beat + td <= datetime.now(tz=timezone.utc):
                    await self.send_alert(shard, alert_type=AlertType.Disconnect)
                    await shard.delete()
            await asyncio.sleep(10)

    async def send_alert(self, shard: Shard, alert_type: AlertType):
        config = load_config()
        if not config.webhook_url:
            return
        last_beat = int(shard.last_beat.timestamp())
        fields = [
            {"name": "Status Type", "value": alert_type.name, "inline": True},
            {"name": "Shard ID", "value": str(shard.shard_id), "inline": True},
            {"name": "Last Heartbeat", "value": f"<t:{last_beat}:R>", "inline": True},
        ]
        embed = {
            "content": config.webhook_content,
            "embeds": [
                {
                    "title": "NOTICE",
                    "description": "A shard has changed status!",
                    "color": alert_type.value,
                    "fields": fields,
                }
            ],
            "username": "Shardman Alerts",
        }
        async with ClientSession() as session:
            _resp = await session.post(
                config.webhook_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(embed),
            )

    async def get_bot_info(self) -> None:
        """Get bot info using bot token."""
        resp = await self.__session.get("/api/v10/gateway/bot")
        data = await resp.json()
        resp.raise_for_status()
        max_shards = data.get("shards")
        self.total_shards = self._config.max_shards or max_shards
        self.max_concurrency = data.get("session_start_limit").get("max_concurrency")
        for i in range(self.total_shards):
            bucket = i % self.max_concurrency
            self.buckets[bucket].append(i)

    async def get_shard_id(self) -> int | None:
        """Get needed shard ID, if any are available"""
        shards = await Shard.find().to_list()
        if len(shards) == 0:
            return 0

        shard_ids = [x.shard_id for x in shards]
        missing_shards = sorted(set(range(0, self.total_shards)).difference(shard_ids))

        if len(missing_shards) == 0:
            return None

        return missing_shards[0]

    async def get_sleep_delay(self, shard_id: int) -> float:
        """
        Get how long a shard needs to sleep to connect

        Args:
            shard_id: Shard ID to check

        Returns:
            Sleep delay
        """
        bucket = self.buckets[shard_id % self.max_concurrency]

        # If first shard in bucket, don't sleep
        if bucket.index(shard_id) == 0:
            return 0

        # Get all shards in the bucket that are already connected
        bucket_shards = await Shard.find(In(Shard.shard_id, bucket)).to_list()

        # If no shards are connected, sleep default amount + 0.1
        if len(bucket_shards) == 0:
            return (bucket.index(shard_id) * 5.0) + 0.1

        # Get shards earlier in the bucket
        lower_shards = sorted([x for x in bucket_shards if x.shard_id < shard_id], key=lambda x: x.shard_id)

        now = datetime.now(tz=timezone.utc)

        # Increase sleep time by difference between when the shard was supposed to connect and now
        sleep_time = 0.1
        for shard in lower_shards:
            timestamp = ulid.from_str(shard.session_id).timestamp().datetime
            sleep_time += max(5 - (now - timestamp).total_seconds(), 0)

        # Get exact sleep amount + 0.1 seconds
        return sleep_time
