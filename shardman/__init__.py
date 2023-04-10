import asyncio
from datetime import datetime, timedelta, timezone

import ulid
from beanie import init_beanie
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from shardman.config import load_config
from shardman.models import Shard, all_models
from shardman.responses import ConnectConfirmed

api = FastAPI(title="Shardman")

shard_lock = asyncio.Lock()


async def check_sessions():
    config = load_config()
    td = timedelta(seconds=config.max_seconds)
    while True:
        async for shard in Shard.find(Shard.valid_session == True):
            if shard.last_beat + td <= datetime.now(tz=timezone.utc):
                shard.valid_session = False
        await asyncio.sleep(10)


@api.on_event("startup")
async def startup():
    config = load_config()
    client = AsyncIOMotorClient(config.mongodb)
    await init_beanie(database=client[config.database], document_models=all_models)

    loop = asyncio.get_event_loop()
    loop.create_task(check_sessions())


async def get_shard_id() -> int | None:
    config = load_config()

    shards = await Shard.find().to_list()
    if len(shards) == 0:
        return 0

    shard_ids = [x.shard_id for x in shards]
    missing_shards = sorted(set(range(0, config.max_shards)).difference(shard_ids))

    if len(missing_shards) == 0:
        return

    return missing_shards[0]


@api.get(
    "/connect",
    responses={
        200: {"model": ConnectConfirmed},
        401: {"description": "Too Many Shards"},
        403: {"description": "Invalid Token"},
    },
)
async def connect(token: str):
    config = load_config()
    if token != config.secret:
        raise HTTPException(status_code=403, detail="Invalid Token")
    elif await Shard.find_all(Shard.valid_session == True).count() >= config.max_shards:
        raise HTTPException(status_code=401, detail="Too Many Shards")

    async with shard_lock:
        shard_id = await get_shard_id()

    session_id = ulid.new().str
    last_beat = datetime.now(tz=timezone.utc)

    await Shard(shard_id=shard_id, session_id=session_id, last_beat=last_beat).insert()

    return ConnectConfirmed(shard=shard_id, max_shards=config.max_shards, session_id=session_id)


@api.get(
    "/beat",
    status_code=204,
    responses={
        401: {"description": "Too Many Shards"},
        403: {"description": "Invalid Token"},
        404: {"description": "Session Not Found"},
    },
)
async def beat(token: str, session_id: str):
    config = load_config()
    if token != config.secret:
        raise HTTPException(status_code=403, detail="Invalid Token")

    shard = await Shard.find_one(Shard.session_id == session_id, valid=True)
    if not shard:
        raise HTTPException(status_code=404, detail="Session Not Found")
    elif shard.shard_id >= config.max_shards:
        raise HTTPException(status_code=401, detail="Too Many Shards")

    shard.last_beat = datetime.now(tz=timezone.utc)
    await shard.save()
