"""FastAPI application assembly and startup sequence."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db import engine as db_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    settings.mirrors_dir.mkdir(parents=True, exist_ok=True)
    await db_engine.migrate()

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

    worker = Worker(registry=registry, hub=hub)
    app.state.worker = worker
    await worker.start()
    start_background_bootstrap(registry)

    from app.api import wire_routes

    wire_routes(app)
    yield
    await worker.stop_worker()
    await db_engine.dispose()


def create_app() -> FastAPI:
    return FastAPI(title="Refactor Platform", lifespan=lifespan)


app = create_app()
