"""Deterministic semantic and fixed-window source chunkers for Python/Java."""
from __future__ import annotations

import ast
import hashlib
import sys
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Iterable

from app.retrieval.models import ChunkingReport, CodeChunk

#: Identity of the chunking *algorithm*. Bump by hand when the cutting rules
#: change; `chunker_version()` extends it with the parsers, which decide the
#: cuts just as much as this file does.
CHUNKER_ALGORITHM = "cpu-s2-v3"


@lru_cache(maxsize=1)
def chunker_version() -> str:
    """The algorithm, plus the versions of the parsers that implement it.

    This string is part of the index identity, so whatever it does not capture
    is free to change under a cached index. Python definitions are cut with the
    standard library's `ast`, whose output tracks the interpreter, and Java with
    tree-sitter; upgrading either can move a boundary and therefore change what
    a chunk contains. Pinning them in the image is not enough on its own — the
    identity has to notice when a pin moves, or an index built by one parser is
    silently reused by another.

    A parser that is not installed is recorded as absent rather than skipped: a
    deployment without tree-sitter chunks Java by falling back to windows, which
    is a different index and must not share an identity with a parsed one.
    """
    parts = [CHUNKER_ALGORITHM, f"py{sys.version_info.major}.{sys.version_info.minor}"]
    for module, label in (("tree_sitter", "ts"), ("tree_sitter_java", "tsj")):
        try:
            parts.append(f"{label}{version(module.replace('_', '-'))}")
        except PackageNotFoundError:
            parts.append(f"{label}-absent")
    return "+".join(parts)


#: Kept for callers that import the constant; resolves through the function so
#: the parser versions are always included.
CHUNKER_VERSION = chunker_version()
_LANGUAGE_EXTENSIONS = {"python": {".py"}, "java": {".java"}}
_EXCLUDED_PARTS = {
    ".git", ".hg", ".idea", ".mypy_cache", ".pytest_cache", ".tox", ".venv",
    "__pycache__", "build", "dist", "node_modules", "target", "vendor",
}
_MAX_FILE_BYTES = 2_000_000
_MAX_AST_CHUNK_LINES = 60
_AST_CHUNK_OVERLAP = 8
_MAX_AST_CHUNK_CHARS = 2_000


def _chunk_id(strategy: str, path: str, start: int, end: int, symbol: str, text: str) -> str:
    payload = f"{strategy}\0{path}\0{start}\0{end}\0{symbol}\0{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _make_chunk(
    strategy: str, rel: str, start: int, end: int, symbol: str,
    lines: list[str], language: str,
) -> CodeChunk:
    text = "".join(lines[max(start - 1, 0):end]).rstrip() + "\n"
    return CodeChunk(_chunk_id(strategy, rel, start, end, symbol, text), rel,
                     start, end, symbol, text, language)


def _make_semantic_chunks(
    rel: str, start: int, end: int, symbol: str, lines: list[str], language: str,
) -> list[CodeChunk]:
    full = _make_chunk("ast", rel, start, end, symbol, lines, language)
    if end - start + 1 <= _MAX_AST_CHUNK_LINES and len(full.text) <= _MAX_AST_CHUNK_CHARS:
        return [full]
    chunks: list[CodeChunk] = []
    cursor = start
    part = 1
    while cursor <= end:
        part_end = min(end, cursor + _MAX_AST_CHUNK_LINES - 1)
        chunk = _make_chunk(
            "ast", rel, cursor, part_end, f"{symbol}#part{part}", lines, language
        )
        while len(chunk.text) > _MAX_AST_CHUNK_CHARS and part_end > cursor:
            part_end = max(cursor, part_end - max(1, (part_end - cursor) // 3))
            chunk = _make_chunk(
                "ast", rel, cursor, part_end, f"{symbol}#part{part}", lines, language
            )
        if len(chunk.text) > _MAX_AST_CHUNK_CHARS:
            text = chunk.text[:_MAX_AST_CHUNK_CHARS]
            chunk = CodeChunk(
                _chunk_id("ast", rel, cursor, part_end, chunk.symbol, text),
                rel, cursor, part_end, chunk.symbol, text, language,
            )
        chunks.append(chunk)
        if part_end >= end:
            break
        cursor = max(cursor + 1, part_end - _AST_CHUNK_OVERLAP + 1)
        part += 1
    return chunks


def _source_files(root: Path, language: str) -> Iterable[Path]:
    extensions = _LANGUAGE_EXTENSIONS.get(language.lower(), set())
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        try:
            rel_parts = path.relative_to(root).parts
            if any(part in _EXCLUDED_PARTS for part in rel_parts):
                continue
            if path.stat().st_size > _MAX_FILE_BYTES:
                continue
        except (OSError, ValueError):
            continue
        yield path


def repository_digest(root: Path, language: str) -> str:
    """Content identity for snapshot workspaces, independent of mtimes."""
    digest = hashlib.sha256()
    for path in _source_files(root, language):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _python_chunks(path: Path, root: Path) -> list[CodeChunk]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    rel = path.relative_to(root).as_posix()
    chunks: list[CodeChunk] = []

    def walk(nodes: list[ast.stmt], prefix: str = "") -> None:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbol = f"{prefix}.{node.name}" if prefix else node.name
                chunks.extend(_make_semantic_chunks(
                    rel, node.lineno, node.end_lineno or node.lineno,
                    symbol, lines, "python",
                ))
            elif isinstance(node, ast.ClassDef):
                symbol = f"{prefix}.{node.name}" if prefix else node.name
                chunks.extend(_make_semantic_chunks(
                    rel, node.lineno, node.end_lineno or node.lineno,
                    symbol, lines, "python",
                ))
                walk(node.body, symbol)

    walk(tree.body)
    if not chunks and lines:
        chunks.append(_make_chunk("ast", rel, 1, len(lines), f"module:{rel}", lines, "python"))
    return chunks


def _java_parser():
    from tree_sitter import Language, Parser
    import tree_sitter_java

    language = Language(tree_sitter_java.language())
    try:
        return Parser(language)
    except TypeError:  # compatibility with older tree-sitter bindings
        parser = Parser()
        parser.set_language(language)
        return parser


def _java_chunks(path: Path, root: Path) -> list[CodeChunk]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    rel = path.relative_to(root).as_posix()
    tree = _java_parser().parse(raw)
    chunks: list[CodeChunk] = []
    class_types = {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration"}
    method_types = {"method_declaration", "constructor_declaration"}

    def node_name(node) -> str:
        named = node.child_by_field_name("name")
        return raw[named.start_byte:named.end_byte].decode("utf-8", errors="replace") if named else "anonymous"

    def walk(node, class_prefix: str = "") -> None:
        next_prefix = class_prefix
        if node.type in class_types:
            name = node_name(node)
            next_prefix = f"{class_prefix}.{name}" if class_prefix else name
            chunks.extend(_make_semantic_chunks(
                rel, node.start_point[0] + 1, node.end_point[0] + 1,
                next_prefix, lines, "java",
            ))
        elif node.type in method_types:
            name = node_name(node)
            symbol = f"{class_prefix}.{name}" if class_prefix else name
            chunks.extend(_make_semantic_chunks(
                rel, node.start_point[0] + 1, node.end_point[0] + 1,
                symbol, lines, "java",
            ))
        for child in node.named_children:
            walk(child, next_prefix)

    walk(tree.root_node)
    if not chunks and lines:
        chunks.append(_make_chunk("ast", rel, 1, len(lines), f"file:{rel}", lines, "java"))
    return chunks


def _window_chunks(
    path: Path, root: Path, language: str, window_lines: int, overlap_lines: int,
) -> list[CodeChunk]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    if not lines:
        return []
    rel = path.relative_to(root).as_posix()
    step = max(1, window_lines - overlap_lines)
    chunks = []
    for start_index in range(0, len(lines), step):
        end_index = min(start_index + window_lines, len(lines))
        start, end = start_index + 1, end_index
        chunks.append(_make_chunk("naive", rel, start, end, f"window:{start}-{end}", lines, language))
        if end_index == len(lines):
            break
    return chunks


def chunk_repository(
    root: Path, language: str, strategy: str, *,
    window_lines: int = 80, overlap_lines: int = 20,
) -> tuple[list[CodeChunk], ChunkingReport]:
    if strategy not in {"ast", "naive"}:
        raise ValueError(f"unknown retrieval strategy: {strategy}")
    if window_lines < 1 or overlap_lines < 0 or overlap_lines >= window_lines:
        raise ValueError("window_lines must be positive and overlap smaller than the window")
    files = list(_source_files(root, language))
    chunks: list[CodeChunk] = []
    fallback = 0
    indexed = 0
    for path in files:
        try:
            if strategy == "naive":
                found = _window_chunks(path, root, language, window_lines, overlap_lines)
            elif language.lower() == "python":
                found = _python_chunks(path, root)
            elif language.lower() == "java":
                found = _java_chunks(path, root)
            else:
                found = _window_chunks(path, root, language, window_lines, overlap_lines)
                fallback += 1
        except (OSError, SyntaxError, UnicodeError, RuntimeError, ImportError):
            found = _window_chunks(path, root, language, window_lines, overlap_lines)
            fallback += 1
        if found:
            indexed += 1
            chunks.extend(found)
    chunks.sort(key=lambda chunk: (chunk.path, chunk.start_line, chunk.end_line, chunk.symbol))
    report = ChunkingReport(strategy, len(files), indexed, len(chunks), fallback,
                            max(0, len(files) - indexed))
    return chunks, report