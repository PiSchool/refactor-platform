"""In-process pub/sub for event-driven SSE/WS fan-out. No DB polling.

Topics: "run:<id>" (status/task/metrics), "session:<id>" (events),
"terminal:<id>" (raw bytes). Publishers are the worker/task-loop; subscribers
are SSE/WS endpoints.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator


@dataclass(frozen=True)
class TerminalChunk:
    """A persisted byte range in a session terminal log."""

    offset: int
    data: bytes


class Hub:
    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        if self._loop is not loop:
            self._subs.clear()
        self._loop = loop

    def publish(self, topic: str, event: str, data: Any) -> None:
        payload = (event, data)
        for q in list(self._subs.get(topic, ())):
            q.put_nowait(payload)

    def publish_threadsafe(self, topic: str, event: str, data: Any) -> None:
        """Publish from a worker thread (PTY reader) into the event loop."""
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        try:
            loop.call_soon_threadsafe(self.publish, topic, event, data)
        except RuntimeError:
            # Shutdown may close the loop between is_closed() and scheduling.
            return

    @asynccontextmanager
    async def listen(self, topic: str):
        """Register a queue for a scoped subscription with deterministic cleanup."""
        q: asyncio.Queue = asyncio.Queue()
        self._subs[topic].add(q)
        try:
            yield q
        finally:
            self._subs[topic].discard(q)

    async def subscribe(self, topic: str) -> AsyncIterator[tuple[str, Any]]:
        async with self.listen(topic) as q:
            while True:
                yield await q.get()


hub = Hub()
