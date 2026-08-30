"""The platform-defined setups: six that can be launched, and `s3_cao`, which
exists so the study's multi-agent runs can be imported and reviewed. Plugins
declare compatibility only; they never define setups.
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

_RAG_PROMPT = """
## Code retrieval

Relevant repository context is included with this task. Verify it against the
workspace before editing. If you need more context, use the read-only
`search_codebase`, `search_file`, or `list_indexed_files` tools.
""".strip()

_EVAL_PROMPT = """
## Mandatory self-check

Before your final response, you MUST run `bash eval.sh` at least once. A session
that never invokes this command is invalid for this setup. Use the reported
stage, reason, and guidance to fix failures and re-run until it prints PASS or
you exhaust the allowed attempts. Do not read or modify `eval.sh` itself.
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
    "s2_rag_naive": SetupProfile(key="s2_rag_naive", name="Single agent + naive RAG",
                                 description="Single agent with hybrid retrieval over fixed line windows.",
                                 retrieval="naive", prompt_block=_RAG_PROMPT),
    "s2_rag_ast": SetupProfile(key="s2_rag_ast", name="Single agent + AST RAG",
                               description="Single agent with hybrid retrieval over AST definitions.",
                               retrieval="ast", prompt_block=_RAG_PROMPT),
    "s3": SetupProfile(key="s3", name="Native sub-agents",
                       description="Single session; the agent may spawn native sub-agents.",
                       subagents=True, prompt_block=_S3_PROMPT),
}

ARCHIVE_SETUPS: dict[str, SetupProfile] = {
    "s3_cao": SetupProfile(
        key="s3_cao",
        name="CAO multi-agent",
        description="Historical CLI Agent Orchestrator study setup; import and review only.",
        archived_only=True,
    ),
}


def get_setup(key: str) -> SetupProfile:
    if key not in SETUPS:
        raise KeyError(f"unknown setup: {key}")
    return SETUPS[key]
