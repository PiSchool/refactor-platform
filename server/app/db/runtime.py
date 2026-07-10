"""Runtime settings: operator overrides of the config.yaml defaults.

Kept separate from `app.config` because these live in the DB and change at
runtime, whereas config.yaml/env are read once at process start.
"""
from __future__ import annotations

from typing import TypeVar

from sqlalchemy import select

from app.db import engine as db_engine
from app.db.models import RuntimeSetting

T = TypeVar("T")


async def runtime_value(key: str, default: T) -> T:
    async with db_engine.session_factory()() as s:
        row = (await s.execute(select(RuntimeSetting).where(RuntimeSetting.key == key))).scalar_one_or_none()
    if row is None or row.value is None:
        return default
    try:
        return type(default)(row.value) if default is not None else row.value
    except (TypeError, ValueError):
        return default
