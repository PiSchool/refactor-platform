"""FastAPI application assembly and startup sequence."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db import engine as db_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    settings.mirrors_dir.mkdir(parents=True, exist_ok=True)

    # Sweep away staging left by an import interrupted before its atomic
    # rename. Done before any DB/catalog work so a crashed import can never
    # leak a half-extracted run directory into a later session.
    from app.results.import_run import cleanup_abandoned_imports, cleanup_uncommitted_imports

    cleanup_abandoned_imports()

    await db_engine.migrate()
    await cleanup_uncommitted_imports()

    # Late imports keep module import light for tests that only need the DB.
    from app.catalog.loader import discover
    from app.catalog.sync import sync_catalog
    from app.catalog.bootstrap import start_background_bootstrap
    from app.execution.worker import Worker
    from app.realtime.hub import hub

    registry = discover(settings.plugins_dir)
    app.state.registry = registry
    async with db_engine.session_factory()() as session:
        await sync_catalog(registry, session)
        await session.commit()

    hub.bind_loop(asyncio.get_running_loop())
    worker = Worker(registry=registry, hub=hub)
    app.state.worker = worker
    await worker.start()
    start_background_bootstrap(registry)

    from app.api import wire_routes

    wire_routes(app)
    try:
        yield
    finally:
        await worker.stop_worker()
        await db_engine.dispose()


def create_app() -> FastAPI:
    return FastAPI(title="Refactor Platform", lifespan=lifespan)


app = create_app()
