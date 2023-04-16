import asyncio
import json
from datetime import datetime, timedelta, timezone
from enum import Enum

from aiohttp import ClientSession

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
        self.__session = ClientSession(base_url="https://discord.com", headers={"Authorization": f"Bot {self._token}"})
        self.lock = asyncio.Lock()

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
                config.webhook_url, headers={"Content-Type": "application/json"}, data=json.dumps(embed)
            )

    async def get_bot_info(self) -> None:
        """Get bot info using bot token."""
        resp = await self.__session.get("/api/v10/gateway/bot")
        data = await resp.json()
        resp.raise_for_status()
        self.total_shards = self._config.max_shards or data.get("shards")
        self.max_concurrency = data.get("session_start_limit").get("max_concurrency")

    async def get_shard_id(self) -> int | None:
        """Get needed shard ID, if any are available"""
        shards = await Shard.find().to_list()
        if len(shards) == 0:
            return 0

        shard_ids = [x.shard_id for x in shards]
        missing_shards = sorted(set(range(0, self.total_shards)).difference(shard_ids))

        if len(missing_shards) == 0:
            return

        return missing_shards[0]
