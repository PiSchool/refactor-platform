"""Real stdio MCP handshake and tool-call integration (opt-in)."""
from __future__ import annotations

import json
import os
import sys
import uuid

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retrieval_mcp_server_lists_and_calls_read_only_tools(tmp_path):
    database_url = os.getenv("RETRIEVAL_TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("RETRIEVAL_TEST_DATABASE_URL is not configured")

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from app.retrieval.models import CodeChunk, IndexIdentity
    from app.retrieval.store import PostgresHybridStore
    from fixtures.embedder import HashEmbedder

    # Embeddings come from the product's own RETRIEVAL_EMBEDDER hook, which
    # tests/conftest.py points at a deterministic embedder. Everything else in
    # this test is real: PostgreSQL with pgvector, the MCP protocol over stdio,
    # and the read-only search tools the agent's CLI calls.
    embedder = HashEmbedder()
    model, dimension = embedder.model_name, embedder.dimension
    cache_dir = tmp_path / "models"
    chunk = CodeChunk(
        f"mcp-{uuid.uuid4().hex}",
        "auth.py",
        1,
        2,
        "validate_token",
        "def validate_token(token): return bool(token)\n",
        "python",
    )
    identity = IndexIdentity(
        "fixture", f"mcp-{uuid.uuid4().hex}", "deadbeef", "python", "ast",
        model, dimension, "mcp-test-v1",
    )
    PostgresHybridStore(database_url, dimension).replace(
        identity,
        [chunk],
        embedder.embed_documents([chunk.document]),
        {},
    )

    invocations = tmp_path / "mcp-invocations.jsonl"
    env = {
        **os.environ,
        "RETRIEVAL_DATABASE_URL": database_url,
        "RETRIEVAL_INDEX_KEY": identity.key,
        "RETRIEVAL_MODEL_CACHE_DIR": str(cache_dir),
        "RETRIEVAL_INVOCATIONS_PATH": str(invocations),
        "RETRIEVAL_READ_ONLY": "1",
    }
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.retrieval.mcp_server"],
        env=env,
    )

    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == {"search_codebase", "search_file", "list_indexed_files"}
            result = await session.call_tool(
                "search_codebase", {"query": "validate_token authentication", "top_k": 2}
            )

    assert result.isError is False
    payload: list[dict] = []
    for item in result.content:
        value = json.loads(item.text)
        if isinstance(value, list):
            payload.extend(value)
        elif isinstance(value, dict) and isinstance(value.get("result"), list):
            payload.extend(value["result"])
        elif isinstance(value, dict):
            payload.append(value)
    assert payload and payload[0]["path"]
    rows = [json.loads(line) for line in invocations.read_text().splitlines() if line]
    assert rows[-1]["tool"] == "search_codebase"