"""The four platform-defined setups. Plugins declare compatibility only;
they never define setups.
"""
from __future__ import annotations

from app.catalog.sdk import SetupProfile

_S3_PROMPT = """
## Sub-agent orchestration (this run enables native sub-agents)

You are the supervisor. Delegate rather than doing everything yourself: you
MUST spawn at least one sub-agent with the `task` tool before finishing —
e.g. one to analyze the repository and locate the relevant code, one to make
the change, and one to validate it. Coordinate their results, then finish.
""".strip()

_LSP_PROMPT = """
## Language server available (this run enables LSP)

A language server is configured for this workspace. Use LSP-backed navigation
and inspection while solving the task rather than plain text search: trigger at
least one concrete action — go-to-definition, find-references, hover, or
diagnostics — before you finish. Include the operation and its arguments in the
same command; do not run a bare `/lsp`.
""".strip()

_EVAL_PROMPT = """
## Self-check tool available

A script `eval.sh` is present in your working directory. Run `bash eval.sh`
at any point to check your work against the benchmark's automated checks; it
prints PASS or a FAILED stage with guidance. Iterate — fix and re-run — until
it prints PASS or you have exhausted your attempts. Do not read or modify
`eval.sh` itself.
""".strip()

SETUPS: dict[str, SetupProfile] = {
    "s1": SetupProfile(key="s1", name="Single agent",
                       description="One agent session, no extras."),
    "s1_lsp": SetupProfile(key="s1_lsp", name="Single agent + LSP",
                           description="Single agent with a language server available.",
                           lsp=True, prompt_block=_LSP_PROMPT),
    "s1_eval": SetupProfile(key="s1_eval", name="Single agent + eval tool",
                            description="Single agent with an in-session self-check tool.",
                            eval_tool=True, prompt_block=_EVAL_PROMPT),
    "s3": SetupProfile(key="s3", name="Native sub-agents",
                       description="Single session; the agent may spawn native sub-agents.",
                       subagents=True, prompt_block=_S3_PROMPT),
}


def get_setup(key: str) -> SetupProfile:
    if key not in SETUPS:
        raise KeyError(f"unknown setup: {key}")
    return SETUPS[key]
