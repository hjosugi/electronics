#!/usr/bin/env python3
"""公開project graphのschema、根拠、必須blockerを検査する。"""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "docs" / "graph" / "project-graph.json"
GRAPH_HTML = ROOT / "docs" / "graph" / "index.html"
GRAPH_JS = ROOT / "docs" / "graph" / "graph.js"
GRAPH_MODEL = ROOT / "docs" / "graph" / "graph-model.mjs"
GRAPH_CSS = ROOT / "docs" / "assets" / "graph.css"
GRAPH_TEST = ROOT / "tests" / "project-graph-model.test.mjs"
KINDS = {"issue", "decision", "artifact", "evidence", "release", "gate"}
STATUSES = {"verified", "open", "blocked", "planned"}
STAGES = {"decision", "implementation", "verification", "publication"}
RELATIONS = {"defines", "implements", "validates", "blocked_by", "depends_on", "publishes", "may_change"}
CONFIDENCE = {"verified", "inferred"}
ALLOWED_HOSTS = {"github.com", "hjosugi.github.io"}
REQUIRED_ORDER_BLOCKERS = {
    "breadboard-evidence",
    "hotplug-evidence",
    "notebooklm-evidence",
    "production-pcb",
}


class GraphError(ValueError):
    pass


def mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GraphError(f"{label} はobjectである必要があります")
    return value


def sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GraphError(f"{label} はarrayである必要があります")
    return value


def text_field(item: dict[str, Any], key: str, label: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GraphError(f"{label}.{key} は空でない文字列である必要があります")
    return value


def public_url(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise GraphError(f"{label} はURL文字列である必要があります")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise GraphError(f"{label} は許可した公開HTTPS URLではありません: {value}")
    return value


def validate(data: dict[str, Any]) -> tuple[int, int]:
    if data.get("schema_version") != 1:
        raise GraphError("schema_version は1である必要があります")
    review_date = data.get("review_date")
    if not isinstance(review_date, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", review_date) is None:
        raise GraphError("review_date はYYYY-MM-DD形式である必要があります")
    text_field(data, "title", "graph")

    nodes = sequence(data.get("nodes"), "nodes")
    edges = sequence(data.get("edges"), "edges")
    if not nodes or not edges:
        raise GraphError("nodesとedgesは1件以上必要です")

    node_ids: set[str] = set()
    node_status: dict[str, str] = {}
    for index, raw_node in enumerate(nodes):
        node = mapping(raw_node, f"nodes[{index}]")
        label = f"nodes[{index}]"
        node_id = text_field(node, "id", label)
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", node_id):
            raise GraphError(f"{label}.id が不正です: {node_id}")
        if node_id in node_ids:
            raise GraphError(f"node idが重複しています: {node_id}")
        node_ids.add(node_id)
        text_field(node, "label", label)
        text_field(node, "summary", label)
        kind = text_field(node, "kind", label)
        status = text_field(node, "status", label)
        stage = text_field(node, "stage", label)
        if kind not in KINDS:
            raise GraphError(f"{label}.kind が不正です: {kind}")
        if status not in STATUSES:
            raise GraphError(f"{label}.status が不正です: {status}")
        if stage not in STAGES:
            raise GraphError(f"{label}.stage が不正です: {stage}")
        public_url(node.get("url"), f"{label}.url")
        node_status[node_id] = status

    edge_ids: set[str] = set()
    order_blockers: set[str] = set()
    for index, raw_edge in enumerate(edges):
        edge = mapping(raw_edge, f"edges[{index}]")
        label = f"edges[{index}]"
        edge_id = text_field(edge, "id", label)
        if edge_id in edge_ids:
            raise GraphError(f"edge idが重複しています: {edge_id}")
        edge_ids.add(edge_id)
        source = text_field(edge, "source", label)
        target = text_field(edge, "target", label)
        if source not in node_ids or target not in node_ids:
            raise GraphError(f"{edge_id} は存在しないnodeを参照しています: {source} -> {target}")
        if source == target:
            raise GraphError(f"{edge_id} はself-loopです")
        relation = text_field(edge, "relation", label)
        confidence = text_field(edge, "confidence", label)
        if relation not in RELATIONS:
            raise GraphError(f"{edge_id}.relation が不正です: {relation}")
        if confidence not in CONFIDENCE:
            raise GraphError(f"{edge_id}.confidence が不正です: {confidence}")
        text_field(edge, "note", label)
        evidence = sequence(edge.get("evidence"), f"{edge_id}.evidence")
        if not evidence:
            raise GraphError(f"{edge_id}.evidence は1件以上必要です")
        for evidence_index, url in enumerate(evidence):
            public_url(url, f"{edge_id}.evidence[{evidence_index}]")
        if confidence == "verified" and relation == "validates" and node_status[source] != "verified":
            raise GraphError(f"{edge_id}: verified validates edgeのsourceはverifiedである必要があります")
        if source == "order-ready" and relation == "blocked_by":
            order_blockers.add(target)

    missing = sorted(REQUIRED_ORDER_BLOCKERS - order_blockers)
    if missing:
        raise GraphError(f"order-readyの必須blocker edgeがありません: {', '.join(missing)}")
    return len(nodes), len(edges)


def self_test(data: dict[str, Any]) -> None:
    fixtures: list[tuple[str, dict[str, Any]]] = []

    duplicate = copy.deepcopy(data)
    duplicate["nodes"].append(copy.deepcopy(duplicate["nodes"][0]))
    fixtures.append(("duplicate node", duplicate))

    dangling = copy.deepcopy(data)
    dangling["edges"][0]["target"] = "missing-node"
    fixtures.append(("dangling edge", dangling))

    self_loop = copy.deepcopy(data)
    self_loop["edges"][0]["target"] = self_loop["edges"][0]["source"]
    fixtures.append(("self-loop", self_loop))

    no_evidence = copy.deepcopy(data)
    no_evidence["edges"][0]["evidence"] = []
    fixtures.append(("missing evidence", no_evidence))

    for label, fixture in fixtures:
        try:
            validate(fixture)
        except GraphError:
            continue
        raise GraphError(f"negative fixtureを拒否できませんでした: {label}")


def validate_site() -> str:
    for path in (GRAPH_HTML, GRAPH_JS, GRAPH_MODEL, GRAPH_CSS, GRAPH_TEST):
        if not path.is_file():
            raise GraphError(f"graph site fileがありません: {path.relative_to(ROOT)}")
    html = GRAPH_HTML.read_text(encoding="utf-8")
    javascript = GRAPH_JS.read_text(encoding="utf-8")
    if 'src="graph.js"' not in html or 'href="../assets/graph.css"' not in html:
        raise GraphError("graph HTMLがlocal JS/CSSを読み込んでいません")
    if "project-graph.json" not in javascript:
        raise GraphError("graph.jsが正本JSONを参照していません")
    if 'from "./graph-model.mjs"' not in javascript:
        raise GraphError("graph.jsが共通filter modelを参照していません")
    for script_path in (GRAPH_JS, GRAPH_MODEL):
        script = script_path.read_text(encoding="utf-8")
        for forbidden in ("innerHTML", "eval(", "new Function(", "document.write("):
            if forbidden in script:
                raise GraphError(f"{script_path.name}で禁止APIを使っています: {forbidden}")
    node = shutil.which("node")
    if node is None:
        return "node syntax checkは環境にないためskip"
    for script_path in (GRAPH_JS, GRAPH_MODEL):
        result = subprocess.run(
            [node, "--check", str(script_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GraphError(f"{script_path.name} syntax error: {result.stderr.strip()}")
    result = subprocess.run(
        [node, "--test", str(GRAPH_TEST)],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise GraphError(f"graph model test error:\n{result.stdout}{result.stderr}")
    return "node syntax + filter model test 5件済み"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true", help="negative fixtureも検査")
    args = parser.parse_args()
    try:
        data = mapping(json.loads(GRAPH_PATH.read_text(encoding="utf-8")), "graph")
        node_count, edge_count = validate(data)
        site_status = validate_site()
        if args.self_test:
            self_test(data)
    except (OSError, json.JSONDecodeError, GraphError) as error:
        print(f"project graph検証に失敗しました: {error}", file=sys.stderr)
        return 1

    suffix = "、negative fixture 4件" if args.self_test else ""
    print(
        f"project graph検証に合格しました"
        f"（node {node_count}、edge {edge_count}{suffix}、{site_status}）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
