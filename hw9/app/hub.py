from __future__ import annotations
import asyncio
import contextlib
import json
from typing import Dict, Optional
from fastapi import WebSocket
import aio_pika
import os


class Connection:
    def __init__(
        self,
        ws: WebSocket,
        user_id: str
    ):
        self.ws = ws
        self.user_id = user_id
        self.id = id(ws)
        self._send_task: Optional[asyncio.Task] = None
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=200)

    async def _connect(self) -> None:
        self._send_task = asyncio.create_task(self._sender())

    async def _disconnect(self) -> None:
        if self._send_task:
            self._send_task.cancel()
        with contextlib.suppress(Exception):
            await self._send_task
        with contextlib.suppress(Exception):
            await self.ws.close()

    async def _sender(self) -> None:
        try:
            while True:
                message = await self._queue.get()
                with contextlib.suppress(Exception):
                    await self.ws.send_text(message)
        except asyncio.CancelledError:
            pass


class LocalHub:
    def __init__(self):
        self._by_user: Dict[str, Dict[int, Connection]] = {}
        self._lock = asyncio.Lock()
        self._channel: Optional[aio_pika.abc.AbstractRobustChannel] = None
        self._connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self._exchange: Optional[aio_pika.abc.AbstractRobustExchange] = None
        self._queue: Optional[aio_pika.abc.AbstractQueue] = None
        self._event_dispatcher_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        connection = await aio_pika.connect_robust(os.getenv('RABIT_URL'))
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            os.getenv('RABBIT_EXCHANGE'),
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        queue = await channel.declare_queue(os.getenv('RABBIT_QUEUE'), durable=True)
        await queue.bind(exchange, routing_key=os.getenv('RABBIT_ROUTING_KEY'))
        self._connection = connection
        self._channel = channel
        self._exchange = exchange
        self._queue = queue
        self._event_dispatcher_task = asyncio.create_task(self._event_dispatcher())

    async def stop(self) -> None:
        if self._event_dispatcher_task:
            self._event_dispatcher_task.cancel()
            with contextlib.suppress(Exception):
                await self._event_dispatcher_task
        async with self._lock:
            conns = [conn for _ in self._by_user.values() for conn in _.values()]
        for conn in conns:
            await self.disconnect(conn)
        if self._channel:
            with contextlib.suppress(Exception):
                await self._channel.close()
        if self._connection:
            with contextlib.suppress(Exception):
                await self._connection.close()

    async def connect(self, conn: Connection) -> None:
        await conn._connect()
        async with self._lock:
            self._by_user.setdefault(conn.user_id, {})[conn.id] = conn

    async def disconnect(self, conn: Connection) -> None:
        await conn._disconnect()
        async with self._lock:
            self._by_user.get(conn.user_id, {}).pop(conn.id, None)
            if not self._by_user.get(conn.user_id, {}):
                self._by_user.pop(conn.user_id, None)

    async def publish_to_user(self, user_id: str, message: dict) -> None:
        routing_key = os.getenv('RABBIT_ROUTING_KEY').replace('*', user_id)
        await self._exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode(), content_type='application/json'),
            routing_key=routing_key
        )

    async def _event_dispatcher(self) -> None:
        try:
            async with self._queue.iterator() as qiter:
                async for message in qiter:
                    async with message.process():
                        *_, user_id = message.routing_key.split('.')
                        payload = message.body.decode()
                        await self._fanout_user(user_id, payload)
        except asyncio.CancelledError:
            pass

    async def _fanout_user(self, user_id: str, message: str) -> None:
        async with self._lock:
            conns = list(self._by_user.get(user_id, {}).values())
        for conn in conns:
            try:
                conn._queue.put_nowait(message)
            except asyncio.QueueFull:
                pass
