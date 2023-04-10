import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import ulid
from aiohttp import ClientSession
from beanie import init_beanie
from fastapi import FastAPI, HTTPException
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

    async with ClientSession(headers={"Authorization": f"Bot {config.token}"}) as session:
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


@api.get(
    "/connect",
    responses={
        200: {"model": ConnectConfirmed},
        401: {"description": "No Shards Available"},
        403: {"description": "Invalid Token"},
    },
)
async def connect(token: str):
    global left_before_halt, next_halt_time
    config = load_config()
    if token != config.secret:
        raise HTTPException(status_code=403, detail="Invalid Token")
    elif await Shard.count() >= total_shards:
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

        await Shard(shard_id=shard_id, session_id=session_id, last_beat=last_beat).insert()

        return ConnectConfirmed(
            shard=shard_id, max_shards=total_shards, session_id=session_id, sleep_duration=sleep_duration
        )

@api.get(
    "/connect_all",
    status_code=201,
    responses={
        403: {"description": "Invalid Token"},
    },
)
async def connect_all(token: str):
    """Connects all shards at once, respecting the max concurrency limit."""
    config = load_config()
    if token != config.secret:
        raise HTTPException(status_code=403, detail="Invalid Token")

    shard_buckets = defaultdict(list)
    for shard_id in range(total_shards):
        bucket = str(shard_id % max_concurrency)
        shard_buckets[bucket].append(shard_id)

    tasks = []

    async def connect_shard(shard_id: int):
        async with shard_lock:
            session_id = ulid.new().str
            last_beat = datetime.now(tz=timezone.utc)

            shard = Shard(shard_id=shard_id, session_id=session_id, last_beat=last_beat)
            await shard.insert()
            return shard

    for bucket in shard_buckets.values():
        for shard_id in bucket:
            start = time.monotonic()
            tasks.append(asyncio.create_task(connect_shard(shard_id)))

            if max_concurrency == 1:
                # todo: when you can determine when a shard has actually connected, use that for the sleep duration instead of this

                await asyncio.sleep(5.1 - (time.monotonic() - start))

    shards = await asyncio.gather(*tasks)
    return {"detail": "All shards connected", "shards": [ConnectConfirmed(shard=x.shard_id, max_shards=total_shards, session_id=x.session_id, sleep_duration=0.0) for x in shards]}

@api.get(
    "/beat",
    status_code=204,
    responses={
        401: {"description": "No Shards Available"},
        403: {"description": "Invalid Token"},
        404: {"description": "Session Not Found"},
    },
)
async def beat(token: str, session_id: str):
    config = load_config()
    if token != config.secret:
        raise HTTPException(status_code=403, detail="Invalid Token")

    shard = await Shard.find_one(Shard.session_id == session_id)
    if not shard:
        raise HTTPException(status_code=404, detail="Session Not Found")
    elif shard.shard_id >= config.max_shards:
        raise HTTPException(status_code=401, detail="No Shards Available")

    shard.last_beat = datetime.now(tz=timezone.utc)
    await shard.save()


@api.get(
    "/disconnect",
    status_code=204,
    responses={
        403: {"description": "Invalid Token"},
        404: {"description": "Session Not Found"},
    },
)
async def beat(token: str, session_id: str):
    config = load_config()
    if token != config.secret:
        raise HTTPException(status_code=403, detail="Invalid Token")

    shard = await Shard.find_one(Shard.session_id == session_id)
    if not shard:
        raise HTTPException(status_code=404, detail="Session Not Found")

    await shard.delete()
