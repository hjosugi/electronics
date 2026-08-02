import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";

import {filterGraph} from "../docs/graph/graph-model.mjs";

const graph = JSON.parse(
  await readFile(new URL("../docs/graph/project-graph.json", import.meta.url), "utf8"),
);

const ids = (items) => items.map((item) => item.id).sort();

test("既定表示は全nodeと全edgeを返す", () => {
  const view = filterGraph(graph);
  assert.equal(view.nodes.length, 19);
  assert.equal(view.edges.length, 17);
});

test("blocked issueだけを絞り込む", () => {
  const view = filterGraph(graph, {kind: "issue", status: "blocked"});
  assert.deepEqual(ids(view.nodes), ["issue-1", "issue-10", "issue-11", "issue-12"]);
  assert.deepEqual(view.edges, []);
});

test("blocked_byは関係するnodeだけを残す", () => {
  const view = filterGraph(graph, {relation: "blocked_by"});
  assert.equal(view.edges.length, 8);
  assert.deepEqual(ids(view.nodes), [
    "breadboard-evidence",
    "hotplug-evidence",
    "issue-10",
    "issue-11",
    "issue-12",
    "notebooklm-evidence",
    "order-ready",
    "production-pcb",
  ]);
});

test("inferredは未検証edgeと接続nodeだけを返す", () => {
  const view = filterGraph(graph, {confidence: "inferred"});
  assert.deepEqual(ids(view.edges), ["e06", "e16", "e17"]);
  assert.deepEqual(ids(view.nodes), [
    "breadboard-evidence",
    "firmware-v031",
    "issue-1",
    "issue-16",
    "production-pcb",
  ]);
});

test("検索はnodeとedgeの両方を対象にする", () => {
  const view = filterGraph(graph, {search: "100回"});
  assert.deepEqual(ids(view.nodes), ["hotplug-evidence", "issue-11", "order-ready"]);
  assert.deepEqual(ids(view.edges), ["e07", "e11"]);
});
