#!/usr/bin/env python3
"""Every relative link, anchor and image in the documentation must resolve.

A dead link is the cheapest documentation defect to introduce and the most
expensive for a reader: renaming a file or a heading breaks every reference to
it silently. This is what `make docs` runs.

    python3 scripts/check_docs.py [--quiet]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "docs" / "figures"

#: markdown files that are published; generated corpora are not documentation
SKIP_DIRS = {".git", "node_modules", ".next", ".venv", "__pycache__", "data", ".e2e"}

IMAGES = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"}

LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML_SRC = re.compile(r"(?:src|srcset)\s*=\s*\"([^\"]+)\"")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$", re.M)
EXPLICIT_ANCHOR = re.compile(r"<a\s+(?:name|id)\s*=\s*\"([^\"]+)\"", re.I)


def markdown_files() -> list[Path]:
    found = []
    for path in ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        found.append(path)
    return sorted(found)


def slug(heading: str) -> str:
    """GitHub's heading slug: the rule that decides whether an anchor resolves."""
    text = re.sub(r"`([^`]*)`", r"\1", heading)              # code spans
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)     # links keep their text
    text = re.sub(r"[*_~]", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    found = {slug(title) for _, title in HEADING.findall(text)}
    found |= set(EXPLICIT_ANCHOR.findall(text))
    return found


def targets(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    found = LINK.findall(text)
    for value in HTML_SRC.findall(text):
        found.extend(part.strip().split(" ")[0] for part in value.split(","))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="print only problems")
    args = parser.parse_args(argv)

    files = markdown_files()
    anchor_cache: dict[Path, set[str]] = {}
    problems: list[str] = []
    referenced: set[Path] = set()
    links = 0

    for path in files:
        here = path.parent
        for target in targets(path):
            if target.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            links += 1
            file_part, _, anchor = target.partition("#")
            if not file_part:
                destination = path
            else:
                destination = (here / file_part).resolve()
                if destination.is_dir():
                    index = destination / "README.md"
                    destination = index if index.is_file() else destination
                if not destination.exists():
                    problems.append(f"{path.relative_to(ROOT)} -> {target} (no such file)")
                    continue
                if destination.suffix in IMAGES:
                    referenced.add(destination)
            if anchor and destination.suffix == ".md":
                if destination not in anchor_cache:
                    anchor_cache[destination] = anchors(destination)
                if anchor.lower() not in anchor_cache[destination]:
                    problems.append(
                        f"{path.relative_to(ROOT)} -> {target} (no heading with that anchor)"
                    )

    # Only images: the directory also holds the data a figure was computed from.
    unreferenced = sorted(
        p.relative_to(ROOT).as_posix()
        for p in FIGURES.glob("*")
        if p.is_file() and p.suffix in IMAGES and p not in referenced
    ) if FIGURES.is_dir() else []
    problems.extend(f"{name} is not referenced by any document" for name in unreferenced)

    if not args.quiet:
        print(f"{len(files)} documents, {links} relative references, "
              f"{len(referenced)} figures referenced")
    for problem in problems:
        print(f"  {problem}")
    if problems:
        print(f"\n{len(problems)} problem(s)")
        return 1
    if not args.quiet:
        print("every reference resolves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
