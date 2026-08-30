"""Execution-setup capability validation and post-run conformance evidence.

Benchmark correctness and setup conformance are deliberately independent: a
task can pass its tests while the model ignored the LSP, eval tool, or native
sub-agent mechanism. Research exports must preserve both facts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.catalog.sdk import SessionInfo, SetupProfile


class SetupUnavailable(RuntimeError):
    """The requested setup cannot be provided; never silently degrade to S1."""


@dataclass(frozen=True)
class SetupAssessment:
    status: str
    conformant: bool
    expected: tuple[str, ...]
    observed: dict[str, int | bool]
    unexpected: tuple[str, ...] = ()

    @property
    def exercised(self) -> bool | None:
        if not self.expected:
            return None
        return self.conformant


def required_agent_capabilities(setup: SetupProfile) -> tuple[str, ...]:
    required: list[str] = []
    if setup.lsp:
        required.append("lsp")
    if setup.eval_tool:
        required.append("eval_tool")
    if setup.subagents:
        required.append("subagents")
    if setup.retrieval:
        required.append("retrieval")
    return tuple(required)


def missing_agent_capabilities(
    setup: SetupProfile, capabilities: dict[str, bool] | None,
) -> tuple[str, ...]:
    available = capabilities or {}
    return tuple(
        capability
        for capability in required_agent_capabilities(setup)
        if not available.get(capability, False)
    )


def ensure_agent_compatible(
    setup: SetupProfile, capabilities: dict[str, bool] | None,
) -> None:
    missing = missing_agent_capabilities(setup, capabilities)
    if missing:
        raise SetupUnavailable(
            f"agent does not support setup {setup.key}; missing capabilities: "
            f"{', '.join(missing)}"
        )


def assess_setup(
    setup: SetupProfile,
    info: SessionInfo,
    session_ctx: Any | None = None,
    *,
    eval_attempts: int = 0,
) -> SetupAssessment:
    retrieval_meta = session_ctx.extra.get("retrieval", {}) if session_ctx else {}
    observed: dict[str, int | bool] = {
        "lsp": info.lsp_actions,
        "eval_tool": max(info.eval_tool_invocations, eval_attempts),
        "subagents": info.subagent_invocations,
        "retrieval": bool(retrieval_meta.get("preInjected")),
    }
    expected = required_agent_capabilities(setup)
    unexpected = tuple(
        mechanism
        for mechanism, value in observed.items()
        if mechanism not in expected and bool(value)
    )
    if unexpected:
        return SetupAssessment(
            status="unexpected_capability_use",
            conformant=False,
            expected=expected,
            observed=observed,
            unexpected=unexpected,
        )
    if any(not bool(observed[mechanism]) for mechanism in expected):
        return SetupAssessment(
            status="setup_not_exercised",
            conformant=False,
            expected=expected,
            observed=observed,
        )
    return SetupAssessment(
        status="conformant",
        conformant=True,
        expected=expected,
        observed=observed,
    )
