#!/usr/bin/env python3
"""ドキュメントページのCSSトークンとインラインstyle禁止を検査する。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSS_PATHS = (
    REPO_ROOT / "docs/assets/document.css",
    REPO_ROOT / "docs/assets/graph.css",
)
HTML_PATHS = (
    REPO_ROOT / "docs/index.html",
    REPO_ROOT / "docs/graph/index.html",
)

REQUIRED_VARIABLES = {
    "--font-family-sans",
    "--font-family-mono",
    "--font-size-xs",
    "--font-size-sm",
    "--font-size-body",
    "--font-size-lead",
    "--font-size-h3",
    "--font-size-h2",
    "--font-size-h1",
    "--font-size-code",
    "--font-size-metric",
    "--line-height-tight",
    "--line-height-heading",
    "--line-height-body",
    "--line-height-code",
    "--font-weight-regular",
    "--font-weight-medium",
    "--font-weight-semibold",
    "--font-weight-bold",
    "--letter-spacing-heading",
    "--letter-spacing-label",
}

TOKENIZED_PROPERTIES = {
    "font-size": "--font-size-",
    "font-family": "--font-family-",
    "line-height": "--line-height-",
    "font-weight": "--font-weight-",
    "letter-spacing": "--letter-spacing-",
}


def main() -> int:
    css_sources = {path: path.read_text(encoding="utf-8") for path in CSS_PATHS}
    html_sources = {path: path.read_text(encoding="utf-8") for path in HTML_PATHS}
    errors: list[str] = []

    combined_css = "\n".join(css_sources.values())
    defined = set(re.findall(r"^\s*(--[a-z0-9-]+)\s*:", combined_css, flags=re.MULTILINE))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", combined_css))
    missing = sorted(REQUIRED_VARIABLES - defined)
    undefined = sorted(used - defined)
    if missing:
        errors.append(f"必須CSS変数がありません: {', '.join(missing)}")
    if undefined:
        errors.append(f"未定義CSS変数を参照しています: {', '.join(undefined)}")

    for css_path, css in css_sources.items():
        for line_number, line in enumerate(css.splitlines(), start=1):
            for property_name, variable_prefix in TOKENIZED_PROPERTIES.items():
                match = re.match(rf"^\s*{property_name}\s*:\s*([^;]+);", line)
                if match and f"var({variable_prefix}" not in match.group(1):
                    errors.append(
                        f"{css_path.relative_to(REPO_ROOT)}:{line_number}: "
                        f"{property_name}は{variable_prefix}変数を使ってください"
                    )

    for html_path, html in html_sources.items():
        relative_html = html_path.relative_to(REPO_ROOT)
        if "<style" in html.lower() or re.search(r"\sstyle\s*=", html, flags=re.IGNORECASE):
            errors.append(f"{relative_html}では<style>またはstyle属性を使わないでください")
        if re.search(r'href="(?:\.\./)?assets/document\.css"', html) is None:
            errors.append(f"{relative_html}が共通document.cssを読み込んでいません")
        for target in re.findall(r'(?:href|src)="([^"]+)"', html):
            if target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            local_target = (html_path.parent / target).resolve()
            if not local_target.exists():
                errors.append(f"{relative_html}のローカル参照がありません: {target}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "ドキュメントCSS検証に合格しました"
        f"（CSS {len(CSS_PATHS)}、HTML {len(HTML_PATHS)}、"
        f"必須変数: {len(REQUIRED_VARIABLES)}、タイポグラフィ直書きなし）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
