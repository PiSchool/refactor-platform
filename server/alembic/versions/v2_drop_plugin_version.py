"""Drop the plugin-declared version columns.

Revision ID: v2_drop_plugin_version
Revises: v1_initial

A manifest declared a `version` for the plugin, and a finished task recorded it
as `agentVersion`. Nothing kept it in step with the installed CLI, so an exported
run could name a version that had not run: the Copilot plugin declared 1.0.68
while the image shipped 1.0.75. The version is now read from the command itself
at the moment it is needed, and these stored copies have no reader left.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "v2_drop_plugin_version"
down_revision = "v1_initial"
branch_labels = None
depends_on = None

_TABLES = ("benchmark", "agent_tool")


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    # Guarded, because a database created from the models before it was stamped
    # never had the column; dropping it unconditionally fails there.
    # Batch mode, because SQLite cannot drop a column in place and the test and
    # e2e databases are SQLite.
    for table in _TABLES:
        if "version" not in _columns(table):
            continue
        with op.batch_alter_table(table) as batch:
            batch.drop_column("version")


def downgrade() -> None:
    for table in _TABLES:
        if "version" in _columns(table):
            continue
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column(
                "version", sa.String(length=32), nullable=False, server_default="1.0.0",
            ))
