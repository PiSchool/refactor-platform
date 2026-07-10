"""Evaluate a benchmark's `passed` expression over stage-pass booleans.

Grammar: stage names, `and`, `or`, `not`, parentheses. Uses Python's parser
restricted to boolean ops on known names — no attribute access, calls, etc.
"""
from __future__ import annotations

import ast


def evaluate(expr: str, stage_pass: dict[str, bool]) -> bool:
    if not expr.strip():
        # default: all verify stages must pass
        return all(stage_pass.values()) if stage_pass else False
    tree = ast.parse(expr, mode="eval")
    return bool(_eval(tree.body, stage_pass))


def _eval(node: ast.AST, env: dict[str, bool]) -> bool:
    if isinstance(node, ast.BoolOp):
        vals = [_eval(v, env) for v in node.values]
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval(node.operand, env)
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise ValueError(f"unknown stage in passed expression: {node.id}")
        return bool(env[node.id])
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    raise ValueError(f"unsupported expression node: {ast.dump(node)}")
