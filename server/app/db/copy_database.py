"""Verified one-time copy of platform rows from SQLite to PostgreSQL."""
from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.engine import upgrade_connection_to_head
from app.db.models import Base


TABLE_ORDER = (
    "benchmark",
    "agent_tool",
    "runtime_setting",
    "task",
    "run",
    "run_task",
    "agent_session",
    "task_result",
)


class DatabaseCopyError(RuntimeError):
    pass


class DestinationConflict(DatabaseCopyError):
    pass


class CopyVerificationError(DatabaseCopyError):
    pass


@dataclass(frozen=True)
class TableFingerprint:
    count: int
    sha256: str


@dataclass(frozen=True)
class CopyReport:
    status: str
    tables: dict[str, TableFingerprint]


def _async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


def _sqlite_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.resolve()}"


def _destination_sqlite_path(url: str) -> Path | None:
    prefixes = ("sqlite+aiosqlite:///", "sqlite:///")
    for prefix in prefixes:
        if url.startswith(prefix):
            value = url.removeprefix(prefix).split("?", 1)[0]
            return Path(f"/{value.lstrip('/')}").resolve()
    return None


def _canonical(value: Any) -> Any:
    if isinstance(value, datetime):
        normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return normalized.isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bytes):
        return {"base64": base64.b64encode(value).decode("ascii")}
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    return value


async def _fingerprints(connection: AsyncConnection) -> dict[str, TableFingerprint]:
    fingerprints: dict[str, TableFingerprint] = {}
    for name in TABLE_ORDER:
        table = Base.metadata.tables[name]
        primary_key = list(table.primary_key.columns)
        result = await connection.stream(select(table).order_by(*primary_key))
        digest = hashlib.sha256()
        count = 0
        async for row in result.mappings():
            payload = json.dumps(
                _canonical(dict(row)),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            digest.update(len(payload).to_bytes(8, "big"))
            digest.update(payload)
            count += 1
        fingerprints[name] = TableFingerprint(count=count, sha256=digest.hexdigest())
    return fingerprints


def _portable_row(name: str, row: Mapping[str, Any]) -> dict[str, Any]:
    table = Base.metadata.tables[name]
    portable = dict(row)
    for column in table.columns:
        value = portable[column.name]
        if isinstance(value, datetime) and value.tzinfo is None:
            portable[column.name] = value.replace(tzinfo=timezone.utc)
    return portable


async def _differing_columns(
    source: AsyncConnection,
    destination: AsyncConnection,
    name: str,
) -> set[str]:
    table = Base.metadata.tables[name]
    primary_key = list(table.primary_key.columns)
    statement = select(table).order_by(*primary_key)
    source_rows = (await source.execute(statement)).mappings().all()
    destination_rows = (await destination.execute(statement)).mappings().all()
    if len(source_rows) != len(destination_rows):
        return {"row_count"}
    differing: set[str] = set()
    for source_row, destination_row in zip(source_rows, destination_rows, strict=True):
        for column in table.columns.keys():
            if _canonical(source_row[column]) != _canonical(destination_row[column]):
                differing.add(column)
    return differing


async def inspect_platform_database(database_url: str) -> dict[str, TableFingerprint]:
    """Return deterministic, cross-dialect fingerprints without changing rows."""
    engine = create_async_engine(_async_url(database_url), poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            return await _fingerprints(connection)
    finally:
        await engine.dispose()


async def _copy_table(
    source: AsyncConnection,
    destination: AsyncConnection,
    name: str,
) -> None:
    table = Base.metadata.tables[name]
    primary_key = list(table.primary_key.columns)
    result = await source.stream(select(table).order_by(*primary_key))
    batch: list[dict[str, Any]] = []
    async for row in result.mappings():
        batch.append(_portable_row(name, row))
        if len(batch) == 500:
            await destination.execute(table.insert(), batch)
            batch.clear()
    if batch:
        await destination.execute(table.insert(), batch)


async def copy_platform_database(
    source_path: Path,
    destination_url: str,
) -> CopyReport:
    """Copy all platform tables atomically, or prove an identical copy exists.

    The source is never modified. A non-empty destination is accepted only
    when every row fingerprint already matches the source exactly.
    """
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise DatabaseCopyError(f"source SQLite database does not exist: {source_path}")
    if not destination_url.strip():
        raise DatabaseCopyError("destination database URL is required")
    destination_sqlite_path = _destination_sqlite_path(destination_url)
    if destination_sqlite_path == source_path:
        raise DatabaseCopyError("source and destination databases must be different")

    source_engine = create_async_engine(_sqlite_url(source_path), poolclass=NullPool)
    destination_engine = create_async_engine(_async_url(destination_url), poolclass=NullPool)
    try:
        async with destination_engine.begin() as destination:
            await destination.run_sync(upgrade_connection_to_head)

        async with source_engine.connect() as source:
            await source.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                source_tables = await source.run_sync(
                    lambda connection: set(inspect(connection).get_table_names())
                )
                missing_tables = set(TABLE_ORDER) - source_tables
                if missing_tables:
                    raise DatabaseCopyError(
                        "source database is missing platform tables: "
                        + ", ".join(sorted(missing_tables))
                    )
                source_fingerprints = await _fingerprints(source)
                async with destination_engine.begin() as destination:
                    destination_fingerprints = await _fingerprints(destination)
                    destination_has_rows = any(
                        fingerprint.count for fingerprint in destination_fingerprints.values()
                    )
                    if destination_has_rows:
                        if destination_fingerprints == source_fingerprints:
                            return CopyReport("already_present", source_fingerprints)
                        raise DestinationConflict(
                            "destination platform data does not exactly match the source"
                        )

                    for name in TABLE_ORDER:
                        await _copy_table(source, destination, name)

                    copied_fingerprints = await _fingerprints(destination)
                    if copied_fingerprints != source_fingerprints:
                        mismatched_tables = [
                            name for name in TABLE_ORDER
                            if copied_fingerprints[name] != source_fingerprints[name]
                        ]
                        descriptions = []
                        for name in mismatched_tables:
                            columns = await _differing_columns(
                                source, destination, name
                            )
                            descriptions.append(
                                f"{name}({','.join(sorted(columns))})"
                            )
                        mismatched = ", ".join(descriptions)
                        raise CopyVerificationError(
                            "destination row verification failed for "
                            f"{mismatched}; transaction was rolled back"
                        )
                return CopyReport("copied", source_fingerprints)
            finally:
                await source.rollback()
    finally:
        await source_engine.dispose()
        await destination_engine.dispose()