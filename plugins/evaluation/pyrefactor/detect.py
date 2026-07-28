"""Structural comparison of Python sources before and after an agent's change.

Java has RefactoringMiner; Python has no comparable detector, so a Python task
could only ever be judged by its tests — a rewrite that passes the tests scored
the same as the refactoring that was asked for. This module compares the two
parse trees and names the transformation that took place.

A definition is described by its parent, argument names, and the normalized
dump of its body with docstrings and positions removed. Two definitions with
the same body are the same code: if the name changed it is a rename, if the
parent changed it is a move, if a new definition appeared and an existing one
now calls it and shrank, it is an extraction.

Vocabulary follows RefactoringMiner so results from Java and Python benchmarks
read the same way.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass

EXTRACT = "Extract Method"
INLINE = "Inline Method"
RENAME = "Rename Method"
MOVE = "Move Method"
MOVE_RENAME = "Move & Rename Method"
SIGNATURE = "Change Method Signature"
SYNTAX_ERROR = "Syntax Error"

# What this detector can name. A syntax error is a parse failure, not a
# refactoring, so it is not something a task can ask for.
KINDS = (EXTRACT, INLINE, RENAME, MOVE, MOVE_RENAME, SIGNATURE)


@dataclass(frozen=True)
class Definition:
    path: str
    name: str
    parent: str
    args: tuple[str, ...]
    body: str
    statements: int
    calls: frozenset[str]
    lineno: int

    @property
    def qualname(self) -> str:
        owner = f"{self.parent}." if self.parent else ""
        return f"{self.path}::{owner}{self.name}"

    @property
    def location(self) -> str:
        return f"{self.path}::{self.parent}" if self.parent else self.path


@dataclass(frozen=True)
class Finding:
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"{self.kind}: {self.detail}"


def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        return body[1:]
    return body


def _calls(node: ast.AST) -> frozenset[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return frozenset(names)


def _body_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Dump of the body alone: the definition's own name is deliberately absent
    so a rename does not change it."""
    body = _strip_docstring(list(node.body))
    module = ast.Module(body=body, type_ignores=[])
    return ast.dump(module, annotate_fields=False, include_attributes=False)


def _statement_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Every statement in the definition, nested ones included.

    Counting only top-level statements missed real cases: inlining a helper
    into a branch of an `if` chain leaves the caller with the same single
    top-level statement while its body clearly grew.
    """
    return sum(1 for stmt in _strip_docstring(list(node.body))
               for node_in_stmt in ast.walk(stmt) if isinstance(node_in_stmt, ast.stmt))


def definitions(path: str, source: str) -> dict[str, Definition]:
    """Every function and method in one file, keyed by qualified name."""
    tree = ast.parse(source)
    found: dict[str, Definition] = {}

    def visit(node: ast.AST, parent: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                spec = child.args
                args = tuple(
                    a.arg for a in
                    [*spec.posonlyargs, *spec.args, *spec.kwonlyargs]
                ) + tuple(
                    a.arg for a in (spec.vararg, spec.kwarg) if a is not None
                )
                definition = Definition(
                    path=path, name=child.name, parent=parent, args=args,
                    body=_body_signature(child),
                    statements=_statement_count(child),
                    calls=_calls(child), lineno=child.lineno,
                )
                found[definition.qualname] = definition
                visit(child, parent)  # nested defs keep the enclosing owner
            elif isinstance(child, ast.ClassDef):
                owner = f"{parent}.{child.name}" if parent else child.name
                visit(child, owner)

    visit(tree, "")
    return found


def _collect(sources: dict[str, str]) -> tuple[dict[str, Definition], list[Finding]]:
    defs: dict[str, Definition] = {}
    problems: list[Finding] = []
    for path, source in sources.items():
        if not source.strip():
            continue
        try:
            defs.update(definitions(path, source))
        except SyntaxError as exc:
            problems.append(Finding(SYNTAX_ERROR, f"{path}: line {exc.lineno}: {exc.msg}"))
    return defs, problems


def detect(before: dict[str, str], after: dict[str, str]) -> list[Finding]:
    """Refactorings visible between two snapshots of the same files."""
    old, _ = _collect(before)
    new, problems = _collect(after)
    findings: list[Finding] = list(problems)

    removed = {k: v for k, v in old.items() if k not in new}
    added = {k: v for k, v in new.items() if k not in old}
    common = {k: (old[k], new[k]) for k in old if k in new}

    claimed_removed: set[str] = set()
    claimed_added: set[str] = set()

    # Same body under a different name, a different owner, or both.
    for old_key, old_def in removed.items():
        for new_key, new_def in added.items():
            if new_key in claimed_added or not old_def.body or old_def.body != new_def.body:
                continue
            same_name = old_def.name == new_def.name
            same_owner = (old_def.parent, old_def.path) == (new_def.parent, new_def.path)
            if same_name and same_owner:
                continue
            kind = (MOVE if same_name else RENAME if same_owner else MOVE_RENAME)
            findings.append(Finding(kind, f"{old_def.qualname} -> {new_def.qualname}"))
            claimed_removed.add(old_key)
            claimed_added.add(new_key)
            break

    # A definition that appeared, is called by a definition that shrank.
    for new_key, new_def in added.items():
        if new_key in claimed_added:
            continue
        for _, (old_caller, new_caller) in common.items():
            if new_def.name not in new_caller.calls or new_def.name in old_caller.calls:
                continue
            if new_caller.statements >= old_caller.statements:
                continue
            findings.append(Finding(
                EXTRACT, f"{new_caller.qualname} -> {new_def.qualname} "
                         f"({old_caller.statements} to {new_caller.statements} statements)"))
            claimed_added.add(new_key)
            break

    # A definition that disappeared, whose caller grew and no longer calls it.
    for old_key, old_def in removed.items():
        if old_key in claimed_removed:
            continue
        for _, (old_caller, new_caller) in common.items():
            if old_def.name not in old_caller.calls or old_def.name in new_caller.calls:
                continue
            if new_caller.statements <= old_caller.statements:
                continue
            findings.append(Finding(
                INLINE, f"{old_def.qualname} into {new_caller.qualname}"))
            claimed_removed.add(old_key)
            break

    for key, (old_def, new_def) in common.items():
        if old_def.args != new_def.args:
            findings.append(Finding(
                SIGNATURE,
                f"{key}({', '.join(old_def.args)}) -> ({', '.join(new_def.args)})"))

    return findings


def normalize_kind(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def matches(findings: list[Finding], expected: list[str]) -> list[str]:
    """Expected kinds that were detected, compared name-insensitively."""
    detected = {normalize_kind(f.kind) for f in findings}
    return [e for e in expected if normalize_kind(e) in detected]
