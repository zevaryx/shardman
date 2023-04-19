import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import WebSocket
from pydantic import BaseModel

from shardman.models import Shard
from shardman.state import StateManager


class OpCode(Enum):
    Connect = 0
    Hearbeat = 1
    Ack = 2
    Disconnect = 3
    UnknownError = 4000
    InvalidData = 4002
    InvalidSession = 4009


class Event(BaseModel):
    op: OpCode
    """Event OpCode"""
    d: Any
    """Event Data"""
    sid: str
    """Session ID"""


class Response(BaseModel):
    op: OpCode
    """Event OpCode"""
    d: Any
    """Event Data"""


class SocketManager:
    def __init__(self, state: StateManager):
        self.state = state
        """Global state manager"""
        self.sockets: dict[str, WebSocket] = defaultdict(WebSocket)
        """Dictionary of Session ID to WebSocket connection"""
        self._tasks: list[asyncio.Task] = []

    async def _handle_event(self, websocket: WebSocket, event: Event, shard: Shard) -> bool:
        if event.op == OpCode.Hearbeat:
            shard.last_beat = datetime.now(tz=timezone.utc)
            shard.guild_count = event.d.get("guild_count")
            shard.latency = event.d.get("latency")
            shard.extra = event.d.get("extra", {})
            await shard.save()
            r = Response(op=OpCode.Ack, d=None)
            await websocket.send_json(r.json())
        elif event.op == OpCode.Disconnect:
            await shard.delete()
            await websocket.close(reason="Client requested disconnect")
            return False

        return True

    async def listen(self, websocket: WebSocket) -> None:
        """Listen for client packets"""
        # Track consecutive invalid packets
        invalid_packets = 0
        running = True
        while running:
            data = await websocket.receive_json()
            try:
                event = Event(**data)
                invalid_packets = 0
                shard = await Shard.find_one(Shard.session_id == event.sid)
                if not shard:
                    await websocket.close(code=OpCode.InvalidSession, reason="Session Not Found")
                    running = False
                elif shard.shard_id >= self.state.total_shards:
                    await websocket.close(code=OpCode.InvalidSession, reason="No Shards Available")
                    running = False
                else:
                    running = self._handle_event(websocket, event, shard)

            except Exception:
                invalid_packets += 1
                r = Response(op=OpCode.InvalidData, d={"detail": "Invalid data packet"})
                await websocket.send_json(r.json())
                if invalid_packets >= 5:
                    await websocket.close(code=OpCode.InvalidData, reason="Too many invalid packets")
                    running = False
        try:
            await websocket.close(reason="Server closed connection")
        finally:
            del self.sockets[event.sid]

    async def send_event(self, session_id: str, event: Event) -> None:
        websocket = self.sockets.get(session_id)
        if websocket is None:
            raise ValueError("Invalid session ID")
        await websocket.send_json(event.json())
        if event.op == OpCode.Disconnect:
            await websocket.close()

    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """Connect a new websocket client"""
        self.sockets[session_id] = websocket
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.listen(websocket))
        self._tasks.append(task)
