#!/usr/bin/env python3
"""統合Markdown内の相対リンクを出力ディレクトリ基準へ変換する。"""

from __future__ import annotations

import argparse
import posixpath
import re
from pathlib import Path

LINK_PATTERN = re.compile(r"]\(([^)]+)\)")
SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def rewrite_target(target: str, source: Path, output_directory: Path) -> str:
    if not target or target.startswith(("#", "/")) or SCHEME_PATTERN.match(target):
        return target

    path_part, fragment_separator, fragment = target.partition("#")
    path_part, query_separator, query = path_part.partition("?")
    resolved = (source.parent / path_part).resolve()
    rewritten = posixpath.relpath(
        resolved.as_posix(),
        output_directory.resolve().as_posix(),
    )
    suffix = f"{query_separator}{query}"
    if fragment_separator:
        suffix += f"#{fragment}"
    return f"{rewritten}{suffix}"


def rewrite_markdown(source: Path, output_directory: Path) -> str:
    text = source.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        target = match.group(1)
        return f"]({rewrite_target(target, source, output_directory)})"

    return LINK_PATTERN.sub(replace, text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    print(rewrite_markdown(args.source.resolve(), args.output_directory.resolve()), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
