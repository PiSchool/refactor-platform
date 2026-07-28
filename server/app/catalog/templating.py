"""Render a template over one task's fields.

Used for a prompt, for the path of an artifact a benchmark asks the agent to
write, and for anything else whose text depends on the task. `{{ params.x }}`
reads the task's own fields.

Re-exported by `app.catalog.sdk`, which is the only module a plugin imports.
"""
from __future__ import annotations

from jinja2 import Environment

_env = Environment(autoescape=False, keep_trailing_newline=True)


def render(template: str, task) -> str:
    return _env.from_string(template or "").render(task=task, params=task.params)
