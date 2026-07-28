"""Create the normalized platform schema.

Revision ID: v1_initial
Revises:
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "v1_initial"
down_revision = None
branch_labels = None
depends_on = None


def _json_document():
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "benchmark",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("manifest", _json_document(), nullable=False),
        sa.Column("data_state", sa.String(length=16), nullable=False),
        sa.Column("data_detail", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "agent_tool",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("manifest", _json_document(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "runtime_setting",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", _json_document(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "task",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("benchmark_id", sa.String(length=36), nullable=False),
        sa.Column("task_key", sa.String(length=300), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("workspace", _json_document(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("params", _json_document(), nullable=False),
        sa.ForeignKeyConstraint(["benchmark_id"], ["benchmark.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("benchmark_id", "task_key"),
    )
    op.create_table(
        "run",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("benchmark_id", sa.String(length=36), nullable=False),
        sa.Column("agent_tool_id", sa.String(length=36), nullable=False),
        sa.Column("setup_key", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("config", _json_document(), nullable=False),
        sa.Column("task_timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_tool_id"], ["agent_tool.id"]),
        sa.ForeignKeyConstraint(["benchmark_id"], ["benchmark.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "run_task",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("workspace_path", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agent_session",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_task_id", sa.String(length=36), nullable=False),
        sa.Column("pid", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("terminal_path", sa.Text(), nullable=True),
        sa.Column("events_path", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_task_id"], ["run_task.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "task_result",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_task_id", sa.String(length=36), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("agent_seconds", sa.Float(), nullable=False),
        sa.Column("evaluate_seconds", sa.Float(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("tokens_input", sa.Integer(), nullable=False),
        sa.Column("tokens_output", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("metrics", _json_document(), nullable=False),
        sa.Column("details", _json_document(), nullable=False),
        sa.Column("prompt_path", sa.Text(), nullable=True),
        sa.Column("response_path", sa.Text(), nullable=True),
        sa.Column("diff_path", sa.Text(), nullable=True),
        sa.Column("terminal_path", sa.Text(), nullable=True),
        sa.Column("events_path", sa.Text(), nullable=True),
        sa.Column("eval_dir", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_task_id"], ["run_task.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_task_id"),
    )


def downgrade() -> None:
    op.drop_table("task_result")
    op.drop_table("agent_session")
    op.drop_table("run_task")
    op.drop_table("run")
    op.drop_table("task")
    op.drop_table("runtime_setting")
    op.drop_table("agent_tool")
    op.drop_table("benchmark")