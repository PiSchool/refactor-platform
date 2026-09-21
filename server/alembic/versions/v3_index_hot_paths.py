"""Index the columns the scheduler and the run views actually filter on.

Revision ID: v3_index_hot_paths
Revises: v2_drop_plugin_version

Only the primary keys and two unique constraints were indexed, so every query
that is not a lookup by id scanned its table. That is invisible on a handful of
runs and not invisible at the retention cap: 400 runs of 100 tasks is 40,000
`run_task` rows, and the run views, the exporter and the retention pass all join
through `run_task.run_id`, which no index covered.

`run(status, queued_at)` is the worker's own question, asked every time it looks
for something to do: the oldest queued run. As a composite it is answered from
the index instead of by sorting the table.

Neither PostgreSQL nor SQLite indexes a foreign key for you, so the remaining
three are the foreign keys that carry joins rather than every foreign key.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "v3_index_hot_paths"
down_revision = "v2_drop_plugin_version"
branch_labels = None
depends_on = None

# (name, table, columns)
_INDEXES = (
    ("ix_run_status_queued_at", "run", ["status", "queued_at"]),
    ("ix_run_task_run_id", "run_task", ["run_id"]),
    ("ix_run_task_task_id", "run_task", ["task_id"]),
    ("ix_agent_session_run_task_id", "agent_session", ["run_task_id"]),
)


def _existing(table: str) -> set[str]:
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    # Guarded, because a database created from the models already carries these:
    # the models declare them too, so the two paths agree.
    for name, table, columns in _INDEXES:
        if name not in _existing(table):
            op.create_index(name, table, columns)


def downgrade() -> None:
    for name, table, _ in _INDEXES:
        if name in _existing(table):
            op.drop_index(name, table_name=table)
