"""Jinja2 rendering of prompt/artifact templates over task fields."""
from __future__ import annotations

from jinja2 import Environment

_env = Environment(autoescape=False, keep_trailing_newline=True)


def render(template: str, task) -> str:
    return _env.from_string(template or "").render(task=task, params=task.params)
