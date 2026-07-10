"""Verify: compile + test a Java project. Per-task JDK selection with a
JDK-21 → 17 fallback for old --release targets, isolated Maven repo.
"""
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from app.catalog.sdk import EvalContext, StageResult
from app.evaluation.presets._util import counts_message, is_compile_failure, resolve, test_counts
from app.execution.sandbox import build_user, chown_tree, demote_kwargs

MUTATES_WORKSPACE = True


def _normalize_major(major: str) -> str:
    """The dataset writes Java 8 as both '1.8' and '8'."""
    v = str(major or "").strip()
    return v.split(".")[-1] if v.startswith("1.") else v


def _java_home(major: str) -> str | None:
    major = _normalize_major(major)
    env = os.getenv(f"JDK_{major}_HOME")
    if env and Path(env).is_dir():
        return env
    for base in ("/usr/lib/jvm", "/opt/java"):
        p = Path(base)
        if not p.is_dir():
            continue
        for d in sorted(p.iterdir()):
            if major in d.name and (d / "bin" / "java").is_file():
                return str(d)
    return None


def _demote(workspace: Path, local_repo: str, env: dict) -> dict:
    """Run the build as the shared unprivileged user (see execution.sandbox).

    Returns subprocess kwargs; mutates `env` (HOME must be writable by the
    build user, or Maven/Gradle cannot create their caches).
    """
    pw = build_user()
    if pw is None:
        return {}
    chown_tree(pw, workspace, local_repo, pw.pw_dir)
    env["HOME"] = pw.pw_dir
    return demote_kwargs(pw)


def _build(ctx: EvalContext, command: str, major: str, local_repo: str):
    env = dict(os.environ)
    jh = _java_home(major)
    if jh:
        env["JAVA_HOME"] = jh
        env["PATH"] = f"{jh}/bin:" + env.get("PATH", "")
    # Suites compare accented text; an unset locale gives Java an ASCII default
    # charset (ANSI_X3.4-1968) and they fail on an unmodified checkout.
    env.setdefault("LANG", "C.UTF-8")
    env.setdefault("LC_ALL", "C.UTF-8")
    # ponytail: java.io.tmpdir is left at its default — suites assert on it, and
    # the sequential queue + unprivileged build user already prevent collisions
    # over shared /tmp paths.

    cmd = command
    if "mvn" in cmd and "maven.repo.local" not in cmd:
        cmd = cmd.replace("mvn ", f"mvn -Dmaven.repo.local={local_repo} ", 1)

    kwargs = _demote(ctx.workspace, local_repo, env)
    proc = subprocess.run(cmd, shell=True, cwd=str(ctx.workspace), env=env,
                          capture_output=True, text=True, **kwargs)
    return proc.returncode == 0, (proc.stdout + proc.stderr)


def run(ctx: EvalContext, config: dict) -> StageResult:
    command = resolve(ctx, config.get("command_from", "")) or "mvn -q -B test"
    major = _normalize_major(resolve(ctx, config.get("jdk_from", "")) or "17")
    fallback = _normalize_major(config.get("fallback_jdk", 17))
    local_repo = config.get("maven_local_repo", "/tmp/rp-m2")

    # A command the shell cannot even parse is a defect in the benchmark data,
    # not a broken refactoring. Say so, rather than blaming the agent.
    try:
        shlex.split(command)
    except ValueError as exc:
        return StageResult(name="java_build", ok=False, reason="malformed_build_command",
                           message=f"Benchmark data supplied an unrunnable build command ({exc}).",
                           log=command)

    ok, log = _build(ctx, command, major, local_repo)
    if not ok and major != fallback and "release version" in log and "not supported" in log:
        ok, log = _build(ctx, command, fallback, local_repo)
    counts = test_counts(log)
    if counts is not None:
        message = counts_message(log, ok)
    elif ok:
        message = "Build+test passed."
    elif is_compile_failure(log):            # javac died; no tests ever ran
        message = "Compilation failed; no tests ran."
    else:
        message = "Build failed."
    return StageResult(name="java_build", ok=ok,
                       reason="" if ok else "compile_test_failed",
                       message=message,
                       log=log[-20000:],
                       outputs={"testsPassed": counts[0], "testsTotal": counts[1]} if counts else {})
