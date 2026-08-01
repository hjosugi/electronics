#!/usr/bin/env python3
"""ドキュメントページのCSSトークンとインラインstyle禁止を検査する。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = REPO_ROOT / "docs/assets/document.css"
HTML_PATH = REPO_ROOT / "docs/index.html"

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
    css = CSS_PATH.read_text(encoding="utf-8")
    html = HTML_PATH.read_text(encoding="utf-8")
    errors: list[str] = []

    defined = set(re.findall(r"^\s*(--[a-z0-9-]+)\s*:", css, flags=re.MULTILINE))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", css))
    missing = sorted(REQUIRED_VARIABLES - defined)
    undefined = sorted(used - defined)
    if missing:
        errors.append(f"必須CSS変数がありません: {', '.join(missing)}")
    if undefined:
        errors.append(f"未定義CSS変数を参照しています: {', '.join(undefined)}")

    for line_number, line in enumerate(css.splitlines(), start=1):
        for property_name, variable_prefix in TOKENIZED_PROPERTIES.items():
            match = re.match(rf"^\s*{property_name}\s*:\s*([^;]+);", line)
            if match and f"var({variable_prefix}" not in match.group(1):
                errors.append(
                    f"{CSS_PATH.relative_to(REPO_ROOT)}:{line_number}: "
                    f"{property_name}は{variable_prefix}変数を使ってください"
                )

    if "<style" in html.lower() or re.search(r"\sstyle\s*=", html, flags=re.IGNORECASE):
        errors.append("docs/index.htmlでは<style>またはstyle属性を使わないでください")
    if 'href="assets/document.css"' not in html:
        errors.append("docs/index.htmlが共通document.cssを読み込んでいません")
    for target in re.findall(r'href="([^"]+)"', html):
        if target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        local_target = (HTML_PATH.parent / target).resolve()
        if not local_target.exists():
            errors.append(f"docs/index.htmlのローカルリンクがありません: {target}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "ドキュメントCSS検証に合格しました"
        f"（必須変数: {len(REQUIRED_VARIABLES)}、タイポグラフィ直書きなし）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
