#!/usr/bin/env python3
"""発注ready状態を、未完項目を成功扱いせずに検査する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "production" / "order-readiness.json"


class ContractError(ValueError):
    pass


def require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{name} はobjectである必要があります")
    return value


def require_bool(mapping: dict[str, Any], key: str, section: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ContractError(f"{section}.{key} はbooleanである必要があります")
    return value


def repository_file(value: Any, field: str, *, suffix: str | None = None) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ContractError(f"{field} はnullまたは空でない相対pathである必要があります")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ContractError(f"{field} はrepository内の相対pathに限定します")
    if suffix is not None and relative.suffix != suffix:
        raise ContractError(f"{field} は{suffix}で終わる必要があります")
    return ROOT / relative


def inspect(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    if manifest.get("schema_version") != 1:
        raise ContractError("schema_version は1である必要があります")

    review_date = manifest.get("review_date")
    if not isinstance(review_date, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", review_date) is None:
        raise ContractError("review_date はYYYY-MM-DD形式である必要があります")

    design_ref = manifest.get("design_ref")
    if design_ref is not None and (
        not isinstance(design_ref, str) or re.fullmatch(r"[0-9a-f]{40}", design_ref) is None
    ):
        raise ContractError("design_ref はnullまたは完全な40桁commit SHAである必要があります")

    pcb_path = repository_file(manifest.get("pcb_path"), "pcb_path", suffix=".kicad_pcb")
    fabricator = require_mapping(manifest.get("fabricator"), "fabricator")
    notebooklm = require_mapping(manifest.get("notebooklm"), "notebooklm")
    verification = require_mapping(manifest.get("verification"), "verification")
    artifacts = require_mapping(manifest.get("artifacts"), "artifacts")

    candidate = fabricator.get("candidate")
    if candidate is not None and (not isinstance(candidate, str) or not candidate.strip()):
        raise ContractError("fabricator.candidate はnullまたは空でない文字列である必要があります")

    checks: list[tuple[str, bool]] = []
    errors: list[str] = []

    def add_file_check(label: str, value: Any, field: str, *, suffix: str | None = None) -> None:
        path = repository_file(value, field, suffix=suffix)
        checks.append((label, path is not None and path.is_file()))
        if path is not None and not path.is_file():
            errors.append(f"{field} が存在しません: {path.relative_to(ROOT)}")

    checks.append(("製造対象commitを固定", design_ref is not None))
    checks.append(("製造用KiCad PCBを指定", pcb_path is not None and pcb_path.is_file()))
    if pcb_path is not None and not pcb_path.is_file():
        errors.append(f"pcb_path が存在しません: {pcb_path.relative_to(ROOT)}")

    add_file_check("NotebookLM統合資料", notebooklm.get("bundle_path"), "notebooklm.bundle_path")
    add_file_check("NotebookLMソース一覧", notebooklm.get("source_list_path"), "notebooklm.source_list_path")
    checks.append(("NotebookLM notebookを作成", require_bool(notebooklm, "notebook_created", "notebooklm")))
    checks.append(("NotebookLM引用smoke test", require_bool(notebooklm, "citation_smoke_test", "notebooklm")))

    for key, label in (
        ("final_erc", "最終回路図ERC"),
        ("final_drc", "最終PCB DRC"),
        ("issue_10_physical", "Issue #10 実配線matrix"),
        ("issue_11_hotplug", "Issue #11 活線挿抜"),
        ("gerber_viewer_review", "Gerber/Excellon viewer確認"),
        ("bom_review", "BOM注文型番・代替確認"),
    ):
        checks.append((label, require_bool(verification, key, "verification")))

    for key, label, suffix in (
        ("gerber_zip", "Gerber + Excellon ZIP", ".zip"),
        ("drill_map", "drill map", None),
        ("schematic_pdf", "回路図PDF", ".pdf"),
        ("pcb_pdf", "PCB PDF", ".pdf"),
        ("bom", "BOM", None),
    ):
        add_file_check(label, artifacts.get(key), f"artifacts.{key}", suffix=suffix)

    position = repository_file(artifacts.get("position_file"), "artifacts.position_file")
    if position is not None and not position.is_file():
        errors.append(f"artifacts.position_file が存在しません: {position.relative_to(ROOT)}")

    checks.append(("発注見積の設定を確認", require_bool(fabricator, "quote_reviewed", "fabricator")))
    order_submitted = require_bool(fabricator, "order_submitted", "fabricator")
    if order_submitted and any(not passed for _, passed in checks):
        errors.append("未完gateがある状態でorder_submitted=trueにはできません")

    blockers = [label for label, passed in checks if not passed]
    return blockers, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="machine-readable JSONを出力")
    parser.add_argument("--require-ready", action="store_true", help="blockerがあれば終了コード2")
    args = parser.parse_args()

    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        manifest = require_mapping(data, "manifest")
        blockers, errors = inspect(manifest)
    except (OSError, json.JSONDecodeError, ContractError) as error:
        print(f"発注ready manifestが不正です: {error}", file=sys.stderr)
        return 1

    result = {
        "ready": not blockers and not errors,
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "blocker_count": len(blockers),
        "blockers": blockers,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        verdict = "READY" if result["ready"] else "NOT READY"
        print(f"発注判定: {verdict}（blocker {len(blockers)}件）")
        for blocker in blockers:
            print(f"[BLOCKED] {blocker}")
        for error in errors:
            print(f"[ERROR] {error}")

    if errors:
        return 1
    if args.require_ready and blockers:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
