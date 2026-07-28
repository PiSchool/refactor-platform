from __future__ import annotations

import re

import yaml

from app.config import REPO_ROOT


def _load_compose() -> dict:
    return yaml.safe_load(
        (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    )


def test_production_tree_has_no_retrieval_disable_switch() -> None:
    forbidden = "SKIP" + "_RAG_SETUP"
    paths = [
        REPO_ROOT / ".env.example",
        REPO_ROOT / "README.md",
        REPO_ROOT / "docker-compose.yml",
        *sorted((REPO_ROOT / "docs").glob("*.md")),
        *sorted((REPO_ROOT / "server" / "app").rglob("*.py")),
    ]
    for path in paths:
        assert forbidden not in path.read_text(encoding="utf-8"), path


def test_run_archive_contract_is_single_and_unversioned() -> None:
    from app.results.bundle import PluginRef, RunManifest

    assert "version" not in RunManifest.model_fields
    assert "version" not in PluginRef.model_fields

    obsolete = "leg" + "acy"
    active_paths = [
        REPO_ROOT / "server" / "app" / "results" / "bundle.py",
        REPO_ROOT / "server" / "app" / "results" / "export.py",
        REPO_ROOT / "server" / "app" / "results" / "import_run.py",
        REPO_ROOT / "server" / "app" / "api" / "runs.py",
        REPO_ROOT / "scripts" / "import_study_runs.py",
        REPO_ROOT / "web" / "lib" / "utils.ts",
    ]
    for path in active_paths:
        assert obsolete not in path.read_text(encoding="utf-8").lower(), path
    assert not (REPO_ROOT / "scripts" / f"import_{obsolete}_runs.py").exists()


def test_operator_stack_requires_distinct_retrieval_passwords() -> None:
    environment = _load_compose()["services"]["retrieval-db"]["environment"]
    assert environment["POSTGRES_PASSWORD"] == (
        "${RETRIEVAL_DB_PASSWORD:?set a retrieval writer password}"
    )
    assert environment["RETRIEVAL_DB_READER_PASSWORD"] == (
        "${RETRIEVAL_DB_READER_PASSWORD:?set a distinct read-only password}"
    )


def test_release_images_are_pinned_by_digest() -> None:
    compose = _load_compose()
    assert re.fullmatch(
        r"pgvector/pgvector:pg16@sha256:[0-9a-f]{64}",
        compose["services"]["retrieval-db"]["image"],
    )

    backend = (REPO_ROOT / "docker" / "backend.Dockerfile").read_text(
        encoding="utf-8"
    )
    frontend = (REPO_ROOT / "docker" / "frontend.Dockerfile").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^FROM ubuntu:22\.04@sha256:[0-9a-f]{64}$", backend, re.M)

    # Both dashboard stages must pin one digest. A build stage and a run stage on
    # different images would serve a bundle compiled against a different runtime.
    stages = re.findall(
        r"^FROM (node:\d+-slim@sha256:[0-9a-f]{64})(?: AS \w+)?$", frontend, re.M
    )
    assert len(stages) == 2 and len(set(stages)) == 1, stages

    # The dashboard is built with the same Node major the backend installs, so a
    # bump cannot land in one image and not the other. The major is asserted
    # rather than a fixed version: pinning an end-of-life release is what broke
    # the backend build when its package repository was withdrawn.
    installed = re.search(r"^ARG NODE_VERSION=(\d+)\.", backend, re.M)
    assert installed, "the backend image does not pin a Node version"
    assert stages[0].startswith(f"node:{installed.group(1)}-slim@"), stages[0]


def test_every_shipped_agent_cli_is_installed_in_the_backend_image() -> None:
    """An adapter that ships has to be runnable in the image that ships it.

    The manifest's `binary` is what the platform looks for on PATH before it
    lets a run start, so an adapter in `plugins/agents/` whose executable the
    image never installs would be offered and then refused on every stack.
    Installed is necessary but not sufficient: the image build also runs each
    declared CLI as the unprivileged user that agent sessions run as.
    """
    dockerfile = (REPO_ROOT / "docker" / "backend.Dockerfile").read_text(
        encoding="utf-8"
    )
    # Comments name the tools too; only installation instructions count.
    instructions = "\n".join(
        line for line in dockerfile.splitlines() if not line.lstrip().startswith("#")
    )
    declared = {}
    for manifest_path in sorted(
        (REPO_ROOT / "plugins" / "agents").glob("*/plugin.yaml")
    ):
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("binary"):
            declared[str(manifest["key"])] = str(manifest["binary"])
    assert declared, "no shipped agent adapter declares the executable it drives"
    for key, binary in declared.items():
        assert binary in instructions, (
            f"agent {key!r} ships but the backend image never installs {binary!r}"
        )


def test_base_frontend_has_a_healthcheck() -> None:
    healthcheck = _load_compose()["services"]["frontend"]["healthcheck"]
    command = " ".join(healthcheck["test"])
    assert "http://127.0.0.1:3000" in command
    assert healthcheck["retries"] >= 3


def test_ci_runs_the_same_checks_a_contributor_runs() -> None:
    """CI calls the Makefile targets rather than repeating their command lines.

    Duplicated invocations drift: a check then passes locally and fails here, or
    passes here and was never run locally at all.
    """
    text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "pull_request:" in text

    called: set[str] = set()
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            for line in str(step.get("run", "")).splitlines():
                words = line.split()
                if words and words[0] == "make":
                    called.update(w for w in words[1:] if w.isalpha())
    assert {"backend", "plugins", "web", "types", "build", "docs", "browser"} <= called
    for target in sorted(called):
        assert re.search(rf"^{target}:", makefile, re.M), f"no Makefile target {target!r}"

    # Retrieval is exercised against a real database, never a mock of one.
    backend = workflow["jobs"]["backend"]
    assert "RETRIEVAL_TEST_DATABASE_URL" in backend["env"]
    assert "pgvector" in backend["services"]["retrieval-db"]["image"]

    containers = " ".join(str(step.get("run", "")) for step in workflow["jobs"]["containers"]["steps"])
    assert "docker compose config" in containers
    assert "docker compose build" in containers