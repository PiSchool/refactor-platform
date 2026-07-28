from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[2] / "scripts" / "import_study_runs.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("study_archive_importer", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cao_study_setup_is_registered_as_archive_only():
    from app.execution.setups import ARCHIVE_SETUPS, SETUPS

    assert "s3_cao" not in SETUPS
    setup = ARCHIVE_SETUPS["s3_cao"]
    assert setup.archived_only is True


def test_restart_archive_detection_uses_current_provenance():
    from app.results.provenance import is_archived_run

    assert is_archived_run({"imported": True}, "s1") is False
    assert is_archived_run({"import": {"sourceRunId": "source"}}, "s1") is True
    assert is_archived_run({}, "s3_cao") is True
    assert is_archived_run({}, "s1") is False


def test_study_importer_emits_the_platform_bundle(tmp_path):
    importer = _load_script()
    task_key = "fixture/task-1#base"
    catalog = {
        "refbench": {task_key},
        "_agent": "copilot-cli",
        "_refbench_repo": {"task-1": "fixture"},
        "_tasks": {
            "refbench": {
                task_key: {
                    "taskKey": task_key,
                    "title": "Fixture task",
                    "params": {"operation": "extract_method"},
                },
            },
        },
        "_benchmarks": {
            "refbench": {
                "key": "refbench",
                "name": "RefactorBench",
                "language": "python",
            },
        },
        "_agents": {
            "copilot-cli": {
                "key": "copilot-cli",
                "name": "GitHub Copilot CLI",
            },
        },
        "_setups": {
            "s1": {"key": "s1", "name": "Single agent"},
        },
    }
    info = {
        "benchmark": "refbench",
        "setup": "s1",
        "mode": "base",
        "model": "openrouter/free",
        "title": "Published fixture run",
        "studyRunId": "benchmark_pipeline_20260724_165300",
        "blockMd": "### Published fixture run\n\n| Task | Result |\n|---|---|\n| task-1 | true |\n",
        "sourceCsv": "fixture.csv",
    }
    rows = [{"Task": "task-1", "Project": "fixture", "Result": "true", "Input": "12"}]
    (tmp_path / "fixture.csv").write_text("Task,Result\ntask-1,true\n", encoding="utf-8")

    summary, skipped = importer.build_summary(info, rows, catalog, catalog["_agent"])
    extras = importer.source_artifacts(info, tmp_path)
    blob = importer.make_zip(summary, extras)

    assert skipped == 0
    archive_path = tmp_path / "study.zip"
    archive_path.write_bytes(blob)
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == {
            "manifest.json",
            "summary.json",
            "results.csv",
            "artifacts/tasks/task-0000/study/source-table.md",
            "artifacts/tasks/task-0000/study/source.csv",
        }
        portable = json.loads(archive.read("summary.json"))
        manifest = json.loads(archive.read("manifest.json"))
        assert "version" not in manifest
        for ref_key in ("benchmark", "setup", "agentTool"):
            assert set(manifest[ref_key]) == {"key", "name"}
        for artifact in manifest["artifacts"]:
            payload = archive.read(artifact["path"])
            assert artifact["sizeBytes"] == len(payload)
            assert artifact["sha256"] == hashlib.sha256(payload).hexdigest()

    from app.results.bundle import RunManifest
    from app.results.import_run import ImportRejected, _classify, _validate_summary

    RunManifest.model_validate(manifest)
    _validate_summary(portable)
    placement = _classify(
        "artifacts/tasks/task-0000/study/source-table.md",
    )
    assert placement.rest == "study/source-table.md"
    with pytest.raises(ImportRejected, match="not in evidence catalog"):
        _classify("artifacts/tasks/task-0000/study/secrets.txt")
    assert portable["run"]["id"] == manifest["sourceRunId"]
    assert portable["run"]["counts"] == {
        "total": 1,
        "passed": 1,
        "failed": 0,
        "timedOut": 0,
        "pending": 0,
    }
    assert portable["tasks"][0]["id"] == "task-0000"
    assert portable["tasks"][0]["artifacts"] == [
        {
            "key": "study-source-table",
            "available": True,
            "mediaType": "text/markdown",
            "sizeBytes": len(info["blockMd"].encode("utf-8")),
        },
        {
            "key": "study-source-csv",
            "available": True,
            "mediaType": "text/csv",
            "sizeBytes": len((tmp_path / "fixture.csv").read_bytes()),
        },
    ]