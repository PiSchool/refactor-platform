"""Turning this CLI's own output into what the dashboard reads."""
from __future__ import annotations

import json
from pathlib import Path

from app.catalog.sdk import SessionInfo


def read(events_path: Path | None) -> SessionInfo:
    info = SessionInfo(model="none")
    lines = []
    if events_path and events_path.is_file():
        lines = events_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "assistant.message":
            info.response_text = str(event.get("data", {}).get("content", ""))
    info.readable_transcript = info.response_text
    return info
