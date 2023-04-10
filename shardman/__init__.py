import asyncio
from datetime import datetime, timedelta, timezone

import ulid
from aiohttp import ClientSession
from beanie import init_beanie
from fastapi import Depends, FastAPI, HTTPException, Header
from motor.motor_asyncio import AsyncIOMotorClient

from shardman.config import load_config
from shardman.models import Shard, all_models
from shardman.responses import ConnectConfirmed

api = FastAPI(title="Shardman")

shard_lock = asyncio.Lock()
max_concurrency = 1
total_shards = 1

next_halt_time: datetime = None
left_before_halt = 5


async def check_sessions():
    config = load_config()
    td = timedelta(seconds=config.max_seconds)
    while True:
        async for shard in Shard.find():
            if shard.last_beat + td <= datetime.now(tz=timezone.utc):
                await shard.delete()
        await asyncio.sleep(10)


@api.on_event("startup")
async def startup():
    global max_concurrency, total_shards
    config = load_config()
    client = AsyncIOMotorClient(config.mongodb, tz_aware=True, tzinfo=timezone.utc)
    await init_beanie(database=client[config.database], document_models=all_models)

    loop = asyncio.get_event_loop()
    loop.create_task(check_sessions())

    async with ClientSession(
        headers={"Authorization": f"Bot {config.token}"}
    ) as session:
        resp = await session.get("https://discord.com/api/v10/gateway/bot")
        data = await resp.json()
        total_shards = config.max_shards or data.get("shards")
        max_concurrency = data.get("session_start_limit").get("max_concurrency")


async def get_shard_id() -> int | None:
    shards = await Shard.find().to_list()
    if len(shards) == 0:
        return 0

    shard_ids = [x.shard_id for x in shards]
    missing_shards = sorted(set(range(0, total_shards)).difference(shard_ids))

    if len(missing_shards) == 0:
        return

    return missing_shards[0]


async def requires_authorization(
    authorization: str = Header(description="Authorization Token"),
):
    config = load_config()
    if authorization != config.secret:
        raise HTTPException(status_code=403, detail="Invalid Token")


@api.get(
    "/connect",
    responses={
        200: {"model": ConnectConfirmed},
        401: {"description": "No Shards Available"},
        403: {"description": "Invalid Token"},
    },
    dependencies=[Depends(requires_authorization)],
)
async def connect():
    global left_before_halt, next_halt_time

    if await Shard.count() >= total_shards:
        raise HTTPException(status_code=401, detail="No Shards Available")

    async with shard_lock:
        shard_id = await get_shard_id()

        session_id = ulid.new().str
        last_beat = datetime.now(tz=timezone.utc)

        sleep_duration = 0.0

        if not next_halt_time or next_halt_time < last_beat:
            next_halt_time = last_beat + timedelta(seconds=5)
            left_before_halt = 5
        if left_before_halt <= 0:
            left_before_halt = 5
            sleep_duration = 5.0
            last_beat = last_beat + timedelta(seconds=5)

        left_before_halt -= 1

        await Shard(
            shard_id=shard_id, session_id=session_id, last_beat=last_beat
        ).insert()

        return ConnectConfirmed(
            shard=shard_id,
            max_shards=total_shards,
            session_id=session_id,
            sleep_duration=sleep_duration,
        )


@api.get(
    "/beat",
    status_code=204,
    responses={
        401: {"description": "No Shards Available"},
        403: {"description": "Invalid Token"},
        404: {"description": "Session Not Found"},
    },
    dependencies=[Depends(requires_authorization)],
)
async def beat(session_id: str, guild_count: int = None, latency: float = None):
    config = load_config()
    shard = await Shard.find_one(Shard.session_id == session_id)
    if not shard:
        raise HTTPException(status_code=404, detail="Session Not Found")
    elif shard.shard_id >= total_shards:
        raise HTTPException(status_code=401, detail="No Shards Available")

    shard.last_beat = datetime.now(tz=timezone.utc)
    shard.guild_count = guild_count
    shard.latency = latency
    await shard.save()


@api.get(
    "/disconnect",
    status_code=204,
    responses={
        403: {"description": "Invalid Token"},
        404: {"description": "Session Not Found"},
    },
    dependencies=[Depends(requires_authorization)],
)
async def beat(token: str, session_id: str):
    shard = await Shard.find_one(Shard.session_id == session_id)
    if not shard:
        raise HTTPException(status_code=404, detail="Session Not Found")

    await shard.delete()
