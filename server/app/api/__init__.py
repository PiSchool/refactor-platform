"""Router wiring. Called from main.lifespan after the worker/registry exist."""
from __future__ import annotations

from fastapi import FastAPI


def wire_routes(app: FastAPI) -> None:
    from app.api import catalog, config, models, overview, prompts, runs, sessions, settings, system
    from app.realtime import sse, ws_terminal

    app.include_router(overview.router)
    app.include_router(runs.router)
    app.include_router(catalog.router)
    app.include_router(config.router)
    app.include_router(models.router)
    app.include_router(prompts.router)
    app.include_router(sessions.router)
    app.include_router(settings.router)
    app.include_router(system.router)
    app.include_router(sse.router)
    app.include_router(ws_terminal.router)
