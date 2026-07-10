"""In-process pub/sub for event-driven SSE/WS fan-out. No DB polling.

Topics: "run:<id>" (status/task/metrics), "session:<id>" (events),
"terminal:<id>" (raw bytes). Publishers are the worker/task-loop; subscribers
are SSE/WS endpoints.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, AsyncIterator


class Hub:
    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def publish(self, topic: str, event: str, data: Any) -> None:
        payload = (event, data)
        for q in list(self._subs.get(topic, ())):
            q.put_nowait(payload)

    def publish_threadsafe(self, topic: str, event: str, data: Any) -> None:
        """Publish from a worker thread (PTY reader) into the event loop."""
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self.publish, topic, event, data)

    async def subscribe(self, topic: str) -> AsyncIterator[tuple[str, Any]]:
        q: asyncio.Queue = asyncio.Queue()
        self._subs[topic].add(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subs[topic].discard(q)


hub = Hub()
