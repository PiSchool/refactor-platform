"""Normalized schema — the single source of truth for structured state.

Large artifacts live on disk and are referenced by relative-path pointers.
Benchmark-specific values live in JSON columns so the schema never changes
per benchmark.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


def new_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Benchmark(Base):
    __tablename__ = "benchmark"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    manifest: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    data_state: Mapped[str] = mapped_column(String(16), nullable=False, default="missing")
    data_detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    tasks: Mapped[list["Task"]] = relationship(back_populates="benchmark")


class AgentTool(Base):
    __tablename__ = "agent_tool"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    manifest: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Task(Base):
    __tablename__ = "task"
    __table_args__ = (UniqueConstraint("benchmark_id", "task_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    benchmark_id: Mapped[str] = mapped_column(ForeignKey("benchmark.id"), nullable=False)
    task_key: Mapped[str] = mapped_column(String(300), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    workspace: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    params: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)

    benchmark: Mapped[Benchmark] = relationship(back_populates="tasks")


class Run(Base):
    __tablename__ = "run"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    benchmark_id: Mapped[str] = mapped_column(ForeignKey("benchmark.id"), nullable=False)
    agent_tool_id: Mapped[str] = mapped_column(ForeignKey("agent_tool.id"), nullable=False)
    setup_key: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    config: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    task_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=1800)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    run_tasks: Mapped[list["RunTask"]] = relationship(back_populates="run", cascade="all, delete-orphan")

    # The worker asks for the oldest queued run every time it looks for work.
    __table_args__ = (Index("ix_run_status_queued_at", "status", "queued_at"),)


class RunTask(Base):
    __tablename__ = "run_task"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("run.id"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("task.id"), nullable=False, index=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    workspace_path: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    run: Mapped[Run] = relationship(back_populates="run_tasks")
    task: Mapped[Task] = relationship()
    result: Mapped["TaskResult | None"] = relationship(back_populates="run_task", uselist=False, cascade="all, delete-orphan")
    sessions: Mapped[list["AgentSession"]] = relationship(back_populates="run_task", cascade="all, delete-orphan")


class TaskResult(Base):
    __tablename__ = "task_result"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_task_id: Mapped[str] = mapped_column(ForeignKey("run_task.id"), unique=True, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    agent_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evaluate_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tokens_input: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    metrics: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    details: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    prompt_path: Mapped[str | None] = mapped_column(Text)
    response_path: Mapped[str | None] = mapped_column(Text)
    diff_path: Mapped[str | None] = mapped_column(Text)
    terminal_path: Mapped[str | None] = mapped_column(Text)
    events_path: Mapped[str | None] = mapped_column(Text)
    eval_dir: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    run_task: Mapped[RunTask] = relationship(back_populates="result")


class AgentSession(Base):
    __tablename__ = "agent_session"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_task_id: Mapped[str] = mapped_column(ForeignKey("run_task.id"), nullable=False, index=True)
    pid: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    terminal_path: Mapped[str | None] = mapped_column(Text)
    events_path: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    run_task: Mapped[RunTask] = relationship(back_populates="sessions")


class RuntimeSetting(Base):
    __tablename__ = "runtime_setting"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON_DOCUMENT, nullable=False)
