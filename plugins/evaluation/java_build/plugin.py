"""Compile a Java project and run its own test suite.

The verdict a Java refactoring has to survive: the project still builds and its
tests still pass. A compile failure, a test failure and a timeout are reported
as three different things, because they mean three different things.

The JDK comes from the task, since the corpus spans a decade of release targets;
a project that rejects it is retried once with the fallback.
"""
from __future__ import annotations

import os
import shlex
from pathlib import Path

from app.catalog.sdk import (
    EvalContext,
    EvaluationPlugin,
    MetricOption,
    MetricSpec,
    StageResult,
    counts,
    counts_message,
    is_compile_failure,
    run_in_workspace,
)


class Plugin(EvaluationPlugin):
    key = "java_build"
    reason = "compile_test_failed"

    spec = MetricSpec(
        title="Java build and test",
        summary=("Compiles the project and runs its own suite with the JDK the task declares. "
                 "Distinguishes a compile failure, a test failure and a timeout."),
        requires="a JDK and the project's build tool (Maven or Gradle)",
        options=(
            MetricOption(key="command_from", label="Build command", type="reference", default="",
                         help="Task field holding the command; falls back to `mvn -q -B test`."),
            MetricOption(key="jdk_from", label="JDK major version", type="reference", default="",
                         help="Task field holding the JDK the project needs; falls back to 17."),
            MetricOption(key="fallback_jdk", label="Fallback JDK", type="integer", default=17,
                         help="Retried with this JDK when the first one rejects the project's "
                              "--release target."),
            MetricOption(key="maven_local_repo", label="Maven local repository", type="string",
                         default="/tmp/rp-m2",
                         help="Kept out of the build user's home so concurrent tasks cannot share "
                              "a half-written cache."),
            MetricOption(key="timeout_seconds", label="Timeout", type="integer", default=0,
                         unit="seconds",
                         help="0 means no limit; the task's own timeout still applies."),
        ),
        outputs=("testsPassed", "testsTotal", "timedOut"),
        mutates_workspace=True,
    )

    def availability(self) -> tuple[bool, str]:
        if java_home("17") or java_home("21"):
            return True, ""
        return False, "no JDK found under /usr/lib/jvm or /opt/java"

    def measure(self, ctx: EvalContext, config: dict) -> StageResult:
        command = ctx.reference(config.get("command_from", "")) or "mvn -q -B test"
        major = normalize_major(ctx.reference(config.get("jdk_from", "")) or "17")
        fallback = normalize_major(config.get("fallback_jdk", 17))
        local_repo = config.get("maven_local_repo", "/tmp/rp-m2")
        configured_timeout = float(config.get("timeout_seconds", 0) or 0)
        timeout = configured_timeout if configured_timeout > 0 else None

        # A command the shell cannot even parse is a defect in the benchmark data,
        # not a broken refactoring. Say so, rather than blaming the agent.
        try:
            shlex.split(command)
        except ValueError as exc:
            return StageResult(ok=False, reason="malformed_build_command",
                               message=f"Benchmark data supplied an unrunnable build command ({exc}).",
                               log=command)

        outcome = _build(ctx, command, major, local_repo, timeout)
        if (
            not outcome.ok
            and not outcome.timed_out
            and major != fallback
            and "release version" in outcome.output
            and "not supported" in outcome.output
        ):
            outcome = _build(ctx, command, fallback, local_repo, timeout)

        log, ok, timed_out = outcome.output, outcome.ok, outcome.timed_out
        parsed = counts(log)
        if parsed is not None:
            message = counts_message(log, ok)
        elif ok:
            message = "Build+test passed."
        elif timed_out:
            message = f"Build+test exceeded the {configured_timeout:g}s time limit."
        elif is_compile_failure(log):            # javac died; no tests ever ran
            message = "Compilation failed; no tests ran."
        else:
            message = "Build failed."
        return StageResult(
            ok=ok,
            reason="" if ok else ("build_timed_out" if timed_out else self.reason),
            message=message,
            log=log[-20000:],
            outputs={
                **({"testsPassed": parsed[0], "testsTotal": parsed[1]} if parsed else {}),
                "timedOut": timed_out,
            },
        )


def normalize_major(major: str) -> str:
    """The dataset writes Java 8 as both '1.8' and '8'."""
    value = str(major or "").strip()
    return value.split(".")[-1] if value.startswith("1.") else value


def java_home(major: str) -> str | None:
    major = normalize_major(major)
    env = os.getenv(f"JDK_{major}_HOME")
    if env and Path(env).is_dir():
        return env
    for base in ("/usr/lib/jvm", "/opt/java"):
        root = Path(base)
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if major in entry.name and (entry / "bin" / "java").is_file():
                return str(entry)
    return None


def without_gradle_daemon(command: str) -> str:
    """Gradle keeps a daemon alive after the build unless told not to.

    The daemon outlives the task, holds memory and its JVM children are never
    reaped, so a build command that uses Gradle is run with `--no-daemon` unless
    the task already says otherwise.
    """
    words = command.split()
    invokes_gradle = any(
        word.endswith("gradlew") or word.endswith("gradle") or word == "./gradlew"
        for word in words
    )
    if not invokes_gradle or "--no-daemon" in words or "--daemon" in words:
        return command
    for index, word in enumerate(words):
        if word.endswith("gradlew") or word.endswith("gradle"):
            words.insert(index + 1, "--no-daemon")
            break
    return " ".join(words)


def _build(ctx: EvalContext, command: str, major: str, local_repo: str, timeout: float | None):
    env: dict[str, str] = {}
    home = java_home(major)
    if home:
        env["JAVA_HOME"] = home
        env["PATH"] = f"{home}/bin:" + os.environ.get("PATH", "")

    if "mvn" in command and "maven.repo.local" not in command:
        command = command.replace("mvn ", f"mvn -Dmaven.repo.local={local_repo} ", 1)
    command = without_gradle_daemon(command)

    return run_in_workspace(ctx.workspace, command, env=env, timeout=timeout,
                            writable=(local_repo,))
