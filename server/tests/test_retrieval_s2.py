"""S2 retrieval acceptance tests.

Runtime retrieval must be persistent, hybrid, pre-injected, observable, and
CPU-only. These tests intentionally go beyond the legacy workspace JSON index.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _python_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "auth.py").write_text(
        "class AuthService:\n"
        "    def validate_token(self, token):\n"
        "        return token in ACTIVE_SESSIONS\n\n"
        "ACTIVE_SESSIONS = set()\n",
        encoding="utf-8",
    )
    (root / "math_utils.py").write_text(
        "def add(a, b):\n    return a + b\n\n"
        "def multiply(a, b):\n    return a * b\n",
        encoding="utf-8",
    )
    (root / "node_modules").mkdir()
    (root / "node_modules" / "ignored.py").write_text(
        "def validate_token(): ...\n", encoding="utf-8"
    )
    return root


def test_ast_chunking_preserves_python_symbols_and_excludes_generated_trees(tmp_path):
    from app.retrieval.chunking import chunk_repository

    chunks, report = chunk_repository(_python_repo(tmp_path), "python", "ast")

    symbols = {chunk.symbol for chunk in chunks}
    assert "AuthService" in symbols
    assert "AuthService.validate_token" in symbols
    assert "multiply" in symbols
    assert all("node_modules" not in chunk.path for chunk in chunks)
    assert report.strategy == "ast" and report.fallback_files == 0


def test_ast_chunking_preserves_java_class_and_method_boundaries(tmp_path):
    from app.retrieval.chunking import chunk_repository

    (tmp_path / "TokenService.java").write_text(
        "package demo;\n"
        "class TokenService {\n"
        "  boolean validateToken(String token) { return token != null; }\n"
        "}\n",
        encoding="utf-8",
    )

    chunks, report = chunk_repository(tmp_path, "java", "ast")

    symbols = {chunk.symbol for chunk in chunks}
    assert "TokenService" in symbols
    assert "TokenService.validateToken" in symbols
    assert report.fallback_files == 0


def test_naive_chunking_is_deterministic_and_distinct_from_ast(tmp_path):
    from app.retrieval.chunking import chunk_repository

    root = _python_repo(tmp_path)
    first, _ = chunk_repository(root, "python", "naive", window_lines=3, overlap_lines=1)
    second, _ = chunk_repository(root, "python", "naive", window_lines=3, overlap_lines=1)
    ast_chunks, _ = chunk_repository(root, "python", "ast")

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert [chunk.chunk_id for chunk in first] != [chunk.chunk_id for chunk in ast_chunks]
    assert all(chunk.symbol.startswith("window:") for chunk in first)


def test_ast_chunking_bounds_large_definitions_for_cpu_inference(tmp_path):
    from app.retrieval.chunking import chunk_repository

    body = "class LargeService:\n" + "".join(
        f"    def operation_{index}(self):\n        return {index}\n"
        for index in range(500)
    )
    (tmp_path / "large.py").write_text(body, encoding="utf-8")

    chunks, _ = chunk_repository(tmp_path, "python", "ast")

    assert any(chunk.symbol.startswith("LargeService#part") for chunk in chunks)
    assert max(len(chunk.text) for chunk in chunks) <= 2_000


def _served_embedder(transport, **kwargs):
    from app.retrieval.backends import OllamaEmbedder

    return OllamaEmbedder(
        "nomic-embed-code", 3, "http://ollama:11434/", transport=transport, **kwargs
    )


def test_served_embeddings_are_batched_and_truncated():
    seen = []

    def transport(url, payload):
        seen.append((url, payload))
        return {"embeddings": [[0.1, 0.2, 0.3] for _ in payload["input"]]}

    vectors = _served_embedder(transport, batch_size=2, max_chars=4).embed_documents(
        ["aaaaaaaa", "bbbbbbbb", "cccccccc"]
    )

    assert len(vectors) == 3
    assert [len(payload["input"]) for _url, payload in seen] == [2, 1]
    assert seen[0][0] == "http://ollama:11434/api/embed"
    assert seen[0][1]["input"] == ["aaaa", "bbbb"]      # chunk cap applied
    assert seen[0][1]["options"] == {"num_ctx": 2048, "num_batch": 2048}


def test_served_embeddings_retry_then_fail_with_a_diagnosable_message(monkeypatch):
    from app.retrieval.errors import RetrievalUnavailable

    monkeypatch.setattr("app.retrieval.backends.time.sleep", lambda _seconds: None)
    calls = {"n": 0}

    def transport(_url, _payload):
        calls["n"] += 1
        raise OSError("connection refused")

    with pytest.raises(RetrievalUnavailable) as error:
        _served_embedder(transport, attempts=3).embed_queries(["find the token check"])

    assert calls["n"] == 3
    assert "ollama:11434" in str(error.value) and "nomic-embed-code" in str(error.value)


def test_bm25_and_rrf_promote_identifier_match_across_rankings():
    from app.retrieval.models import CodeChunk
    from app.retrieval.ranking import bm25_rank, reciprocal_rank_fusion

    chunks = [
        CodeChunk("a", "auth.py", 1, 3, "validate_token", "def validate_token(token): return token"),
        CodeChunk("b", "docs.py", 1, 2, "docs", "token validation is described here"),
        CodeChunk("c", "math.py", 1, 2, "multiply", "def multiply(a, b): return a * b"),
    ]
    lexical = bm25_rank(chunks, "validate_token session token", top_k=3)
    fused = reciprocal_rank_fusion([["b", "a", "c"], [hit.chunk_id for hit in lexical]])

    assert lexical[0].chunk_id == "a"
    assert fused[0].chunk_id == "a"
    assert fused[0].rrf_score > fused[-1].rrf_score


def test_query_plan_contains_broad_identifier_and_target_searches():
    from app.retrieval.ranking import plan_queries

    plan = plan_queries(
        "Move `validate_token` into auth/utils.py and update AuthService callers.",
        {"filePathBefore": "src/auth/service.py", "filePathAfter": "src/auth/utils.py"},
    )

    assert [query.kind for query in plan] == ["broad", "identifier", "target"]
    assert "validate_token" in plan[1].text
    assert "auth/utils.py" in plan[2].text


def test_index_identity_changes_for_source_commit_strategy_and_model():
    from app.retrieval.models import IndexIdentity

    base = IndexIdentity("refbench", "repo", "abc", "python", "ast", "model-a", 768, "v1")
    keys = {
        base.key,
        IndexIdentity("refbench", "repo", "def", "python", "ast", "model-a", 768, "v1").key,
        IndexIdentity("refbench", "repo", "abc", "python", "naive", "model-a", 768, "v1").key,
        IndexIdentity("refbench", "repo", "abc", "python", "ast", "model-b", 768, "v1").key,
        IndexIdentity(
            "refbench", "repo", "abc", "python", "ast", "model-a", 768, "v1",
            "task:different-query",
        ).key,
    }
    assert len(keys) == 5


def test_prefilter_is_bounded_and_preserves_explicit_target_file():
    from app.retrieval.models import CodeChunk, QuerySpec
    from app.retrieval.service import _prefilter_chunks

    chunks = [
        CodeChunk(
            str(index), f"module_{index}.py", 1, 2, f"symbol_{index}",
            f"def symbol_{index}(): return {index}\n", "python",
        )
        for index in range(300)
    ]
    selected = _prefilter_chunks(
        chunks,
        [QuerySpec("broad", "symbol refactor"), QuerySpec("identifier", "symbol_299")],
        {"filePathBefore": "module_299.py"},
        64,
    )

    assert len(selected) <= 64
    assert any(chunk.path == "module_299.py" for chunk in selected)


def test_read_only_pgvector_store_refuses_index_mutation():
    from app.retrieval.errors import RetrievalUnavailable
    from app.retrieval.models import IndexIdentity
    from app.retrieval.store import PostgresHybridStore

    store = PostgresHybridStore(
        "postgresql://reader:secret@retrieval-db/retrieval", 768, read_only=True
    )
    identity = IndexIdentity("b", "s", "r", "python", "ast", "m", 768, "v")
    with pytest.raises(RetrievalUnavailable, match="read-only"):
        store.replace(identity, [], [], {})


def test_mcp_config_contains_reader_but_never_writer_credential(tmp_path):
    from app.retrieval.config import RetrievalConfig
    from app.retrieval.service import _mcp_config

    writer = "postgresql://writer:writer-secret@db/retrieval"
    reader = "postgresql://reader:reader-secret@db/retrieval"
    config = RetrievalConfig(database_url=writer, reader_database_url=reader)

    document = _mcp_config(config, "index", tmp_path / "calls.jsonl")
    serialized = json.dumps(document)
    assert reader in serialized
    assert writer not in serialized
    assert document["mcpServers"]["codebase-retrieval"]["env"]["RETRIEVAL_READ_ONLY"] == "1"


def test_agent_environment_does_not_inherit_retrieval_database_urls(tmp_path, monkeypatch):
    from app.execution.taskloop import _agent_env

    monkeypatch.setenv("RETRIEVAL_DATABASE_URL", "postgresql://writer:secret@db/retrieval")
    monkeypatch.setenv("RETRIEVAL_READER_DATABASE_URL", "postgresql://reader:secret@db/retrieval")

    environment = _agent_env(None, tmp_path)

    assert "RETRIEVAL_DATABASE_URL" not in environment
    assert "RETRIEVAL_READER_DATABASE_URL" not in environment


class _FakeEmbedder:
    model_name = "cpu-test-model"
    dimension = 3
    device = "cpu"

    def embed_documents(self, texts):
        return [[float("validate" in text), float("multiply" in text), 1.0] for text in texts]

    def embed_queries(self, texts):
        return [[float("validate" in text), float("multiply" in text), 1.0] for text in texts]


class _FakeReranker:
    model_name = "cpu-test-reranker"
    device = "cpu"

    def rerank(self, query, documents):
        return [2.0 if "validate_token" in document else 0.1 for document in documents]


def test_service_reuses_exact_index_and_writes_preinjection_provenance(tmp_path):
    from app.retrieval.service import InMemoryHybridStore, RetrievalRequest, RetrievalService

    workspace = _python_repo(tmp_path / "repo")
    artifacts = tmp_path / "artifacts"
    store = InMemoryHybridStore()
    service = RetrievalService(store=store, embedder=_FakeEmbedder(), reranker=_FakeReranker())
    request = RetrievalRequest(
        benchmark="refbench",
        source="repositories/demo",
        revision="deadbeef",
        language="python",
        strategy="ast",
        instructions="Update validate_token and its callers.",
        params={"filePathBefore": "auth.py"},
        workspace=workspace,
        artifacts_dir=artifacts,
    )

    first = service.prepare(request)
    second = service.prepare(request)

    assert store.build_count == 1
    assert first.index_key == second.index_key
    assert first.pre_injected is True and first.hits
    assert "validate_token" in first.context
    provenance = json.loads((artifacts / "retrieval" / "provenance.json").read_text())
    assert provenance["indexKey"] == first.index_key
    assert provenance["embeddingModel"] and provenance["embeddingsServedBy"]
    assert provenance["preInjected"] is True
    assert (artifacts / "retrieval" / "context.md").read_text() == first.context


def test_service_fails_closed_when_semantic_backend_is_unavailable(tmp_path):
    from app.retrieval.errors import RetrievalUnavailable
    from app.retrieval.service import InMemoryHybridStore, RetrievalRequest, RetrievalService

    class _Broken(_FakeEmbedder):
        def embed_documents(self, texts):
            raise RuntimeError("model unavailable")

    request = RetrievalRequest(
        benchmark="refbench", source="repo", revision="abc", language="python",
        strategy="ast", instructions="validate token", params={},
        workspace=_python_repo(tmp_path / "repo"), artifacts_dir=tmp_path / "artifacts",
    )

    with pytest.raises(RetrievalUnavailable, match="model unavailable"):
        RetrievalService(InMemoryHybridStore(), _Broken(), _FakeReranker()).prepare(request)


def test_service_honors_operator_cancellation_before_indexing(tmp_path):
    from app.retrieval.errors import RetrievalCancelled
    from app.retrieval.service import InMemoryHybridStore, RetrievalRequest, RetrievalService

    request = RetrievalRequest(
        benchmark="refbench", source="repo", revision="abc", language="python",
        strategy="ast", instructions="validate token", params={},
        workspace=_python_repo(tmp_path / "repo"), artifacts_dir=tmp_path / "artifacts",
        cancelled=lambda: True,
    )

    with pytest.raises(RetrievalCancelled, match="cancelled"):
        RetrievalService(
            InMemoryHybridStore(), _FakeEmbedder(), _FakeReranker()
        ).prepare(request)


def test_retrieval_context_is_injected_before_setup_instructions(tmp_path):
    from app.catalog.sdk import SessionCtx, SetupProfile, TaskDef, WorkspaceSpec
    from app.execution.taskloop import _build_prompt

    class _Hooks:
        def build_prompt(self, task, ctx):
            return "TASK"

    class _Manifest:
        prompt = None       # this benchmark builds its prompt in Python

    class _Loaded:
        hooks = _Hooks()
        manifest = _Manifest()

    setup = SetupProfile("s2_rag_ast", "S2", "", retrieval="ast", prompt_block="TOOLS")
    task = TaskDef("t", "t", "python", WorkspaceSpec("snapshot", "repo"), "do", {})
    ctx = SessionCtx(
        run_id="r", run_task_id="rt", session_id="s", task=task, workspace=tmp_path,
        artifacts_dir=tmp_path, prompt_path=tmp_path / "prompt.md", config_dir=tmp_path / "home",
        model="m", setup=setup, requested_env={},
        extra={"retrieval_context": "## Retrieved code context\nMATCH"},
    )

    prompt = _build_prompt(_Loaded(), task, ctx, setup)
    assert prompt.index("TASK") < prompt.index("Retrieved code context") < prompt.index("TOOLS")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("setup_key", "strategy"),
    [("s2_rag_ast", "ast"), ("s2_rag_naive", "naive")],
)
async def test_s2_taskloop_persists_preinjection_without_requiring_tool_call(
    tmp_env, monkeypatch, setup_key, strategy,
):
    from sqlalchemy import select

    from app.db import engine as db_engine
    from app.db.models import RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub
    from app.retrieval.service import RetrievalResult, RetrievalService
    from tests.helpers import make_run, seed_catalog

    class _Prepared:
        def prepare(self, request):
            root = request.artifacts_dir / "retrieval"
            root.mkdir(parents=True, exist_ok=True)
            provenance = root / "provenance.json"
            invocations = root / "invocations.jsonl"
            provenance.write_text('{"preInjected": true}', encoding="utf-8")
            invocations.touch()
            return RetrievalResult(
                "index-key", request.strategy,
                "## Retrieved code context\n`target.py` is relevant.\n",
                [{"path": "target.py"}], [{"kind": "broad", "text": request.instructions}],
                True, None, provenance, invocations,
            )

    prepared = _Prepared()
    monkeypatch.setattr(RetrievalService, "from_environment", lambda *_: prepared)
    registry = await seed_catalog()
    hub.bind_loop(__import__("asyncio").get_running_loop())
    run_id = await make_run(setup_key)

    await execute_run(run_id, registry, hub, RunControl(run_id=run_id))

    async with db_engine.session_factory()() as session:
        run_task = (await session.execute(
            select(RunTask).where(RunTask.run_id == run_id)
        )).scalar_one()
        result = (await session.execute(
            select(TaskResult).where(TaskResult.run_task_id == run_task.id)
        )).scalar_one()
    assert run_task.status == "passed"
    assert result.metrics["retrievalPreInjected"] is True
    assert result.metrics["retrievalInvocations"] == 0
    assert result.metrics["setupExercised"] is True
    assert result.metrics["setupCompliance"] == "conformant"
    assert result.details["retrieval"]["strategy"] == strategy


@pytest.mark.asyncio
async def test_s2_taskloop_fails_closed_when_retrieval_is_unavailable(tmp_env, monkeypatch):
    from sqlalchemy import select

    from app.db import engine as db_engine
    from app.db.models import RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub
    from app.retrieval.errors import RetrievalUnavailable
    from app.retrieval.service import RetrievalService
    from tests.helpers import make_run, seed_catalog

    class _Unavailable:
        def prepare(self, _request):
            raise RetrievalUnavailable("pgvector is unavailable")

    monkeypatch.setattr(RetrievalService, "from_environment", lambda *_: _Unavailable())
    registry = await seed_catalog()
    hub.bind_loop(__import__("asyncio").get_running_loop())
    run_id = await make_run("s2_rag_ast")

    await execute_run(run_id, registry, hub, RunControl(run_id=run_id))

    async with db_engine.session_factory()() as session:
        run_task = (await session.execute(
            select(RunTask).where(RunTask.run_id == run_id)
        )).scalar_one()
        result = (await session.execute(
            select(TaskResult).where(TaskResult.run_task_id == run_task.id)
        )).scalar_one()
    assert run_task.status == "error"
    assert result.reason == "retrieval_unavailable"
    assert "pgvector is unavailable" in result.details["error"]


@pytest.mark.asyncio
async def test_s2_taskloop_stops_during_retrieval_preparation(tmp_env, monkeypatch):
    from sqlalchemy import select

    from app.db import engine as db_engine
    from app.db.models import Run, RunTask, TaskResult
    from app.execution.taskloop import RunControl, execute_run
    from app.realtime.hub import hub
    from app.retrieval.errors import RetrievalCancelled
    from app.retrieval.service import RetrievalService
    from tests.helpers import make_run, seed_catalog

    control = RunControl(run_id="pending")

    class _Cancelled:
        def prepare(self, _request):
            control.stop_event.set()
            raise RetrievalCancelled("operator stop")

    monkeypatch.setattr(RetrievalService, "from_environment", lambda *_: _Cancelled())
    registry = await seed_catalog()
    hub.bind_loop(__import__("asyncio").get_running_loop())
    run_id = await make_run("s2_rag_ast")
    control.run_id = run_id

    await execute_run(run_id, registry, hub, control)

    async with db_engine.session_factory()() as session:
        run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one()
        run_task = (await session.execute(
            select(RunTask).where(RunTask.run_id == run_id)
        )).scalar_one()
        result = (await session.execute(
            select(TaskResult).where(TaskResult.run_task_id == run_task.id)
        )).scalar_one()
    assert run.status == "stopped"
    assert run_task.status == "stopped"
    assert result.reason == "stopped"

def test_the_studys_embedding_model_is_not_refused_by_the_store():
    """3584 dimensions, which is what the study's code embedding model emits.

    The store rejected any dimension above 2000 — pgvector's limit for an HNSW
    index, not for storing a vector — so the study's own embedding model made
    `/api/health` answer `503 retrieval_unavailable` and no S2 run could start.
    Above that limit the vectors are stored and scanned exactly instead, which is
    how the published study searched them.
    """
    import pytest

    from app.retrieval.errors import RetrievalUnavailable
    from app.retrieval.store import (
        VECTOR_INDEX_LIMIT,
        VECTOR_STORAGE_LIMIT,
        PostgresHybridStore,
    )

    url = "postgresql://user:pass@host:5432/db"

    study = PostgresHybridStore(url, 3584)
    assert study.dimension == 3584
    assert study.approximate is False

    assert PostgresHybridStore(url, VECTOR_INDEX_LIMIT).approximate is True
    assert PostgresHybridStore(url, VECTOR_INDEX_LIMIT + 1).approximate is False

    with pytest.raises(RetrievalUnavailable, match="at most 16000 dimensions"):
        PostgresHybridStore(url, VECTOR_STORAGE_LIMIT + 1)
    with pytest.raises(RetrievalUnavailable):
        PostgresHybridStore(url, 0)
