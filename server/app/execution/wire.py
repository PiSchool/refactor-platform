"""Which request format an agent CLI needs, and whether the provider answers it.

Agent CLIs do not agree on how to talk to a model. Copilot, Aider, opencode and
Junie send chat completions; Codex sends OpenAI Responses requests; Claude Code
sends Anthropic Messages requests. An endpoint that implements only one of those
cannot drive the others, and the failure used to surface inside the agent as a
`404` the operator had to decode.

An adapter declares what it speaks (`wire` on its plugin class, defaulting to
chat completions) and a provider declares what it answers (`protocols` in
`config.yaml`). A pairing that cannot work is refused before the run starts, with
the protocol named.
"""
from __future__ import annotations

CHAT_COMPLETIONS = "chat_completions"

LABELS = {
    CHAT_COMPLETIONS: "OpenAI chat-completions API",
    "responses": "OpenAI Responses API",
    "anthropic_messages": "Anthropic Messages API",
}


def required_protocol(impl) -> str:
    """The request format this adapter's CLI sends."""
    return str(getattr(impl, "wire", CHAT_COMPLETIONS) or CHAT_COMPLETIONS)


def describe(protocol: str) -> str:
    return LABELS.get(protocol, protocol)


def refusal(agent_name: str, impl, provider) -> str:
    """Why this agent cannot run against this provider, or an empty string."""
    needed = required_protocol(impl)
    if provider.speaks(needed):
        return ""
    answered = ", ".join(describe(name) for name in provider.protocols) or "nothing"
    return (
        f"{agent_name} sends requests in the {describe(needed)}, which "
        f"{provider.label} does not answer; it answers {answered}. "
        f"Select a provider that implements it, or an agent that speaks one it does."
    )
