"""Tells a locally executed run apart from published, imported history.

An archived run is either an imported bundle (its config carries the source
run it was exported from) or one of the archive-only setups such runs may
reference. Their evidence cannot be produced again on this machine, so every
destructive or re-executing path has to treat them as read-only.
"""
from __future__ import annotations

from app.execution.setups import ARCHIVE_SETUPS


def is_archived_run(config: dict | None, setup_key: str) -> bool:
    provenance = (config or {}).get("import")
    return (
        setup_key in ARCHIVE_SETUPS
        or (
            isinstance(provenance, dict)
            and isinstance(provenance.get("sourceRunId"), str)
        )
    )
