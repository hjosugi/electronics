const GRAPH_URL = new URL("project-graph.json", import.meta.url);
const SVG_NS = "http://www.w3.org/2000/svg";
const STAGES = ["decision", "implementation", "verification", "publication"];
const STAGE_LABELS = {
  decision: "DECISION",
  implementation: "IMPLEMENTATION",
  verification: "VERIFICATION",
  publication: "PUBLICATION",
};
const X_BY_STAGE = {
  decision: 40,
  implementation: 340,
  verification: 640,
  publication: 940,
};
const NODE_WIDTH = 240;
const NODE_HEIGHT = 80;
const ROW_GAP = 118;
const TOP_OFFSET = 76;

const elements = {
  form: document.querySelector("#graph-controls"),
  search: document.querySelector("#graph-search"),
  kind: document.querySelector("#kind-filter"),
  status: document.querySelector("#status-filter"),
  relation: document.querySelector("#relation-filter"),
  confidence: document.querySelector("#confidence-filter"),
  reset: document.querySelector("#reset-filters"),
  summary: document.querySelector("#graph-summary"),
  svg: document.querySelector("#project-graph"),
  edgeLayer: document.querySelector("#edge-layer"),
  nodeLayer: document.querySelector("#node-layer"),
  detailTitle: document.querySelector("#detail-title"),
  detail: document.querySelector("#detail-content"),
  edgeTable: document.querySelector("#edge-table-body"),
};

let graphData;
let selected = null;

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
  return element;
}

function optionFor(value) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = value;
  return option;
}

function populateFilters(data) {
  const kinds = [...new Set(data.nodes.map((node) => node.kind))].sort();
  const statuses = [...new Set(data.nodes.map((node) => node.status))].sort();
  const relations = [...new Set(data.edges.map((edge) => edge.relation))].sort();
  kinds.forEach((value) => elements.kind.append(optionFor(value)));
  statuses.forEach((value) => elements.status.append(optionFor(value)));
  relations.forEach((value) => elements.relation.append(optionFor(value)));
}

function searchableNode(node) {
  return [node.id, node.label, node.kind, node.status, node.stage, node.summary]
    .join(" ")
    .toLocaleLowerCase("ja");
}

function searchableEdge(edge, nodesById) {
  return [
    edge.id,
    edge.relation,
    edge.confidence,
    edge.note,
    nodesById.get(edge.source)?.label,
    nodesById.get(edge.target)?.label,
  ]
    .join(" ")
    .toLocaleLowerCase("ja");
}

function currentView(data) {
  const term = elements.search.value.trim().toLocaleLowerCase("ja");
  const nodesById = new Map(data.nodes.map((node) => [node.id, node]));
  const nodeMatches = new Set(
    data.nodes
      .filter((node) => !elements.kind.value || node.kind === elements.kind.value)
      .filter((node) => !elements.status.value || node.status === elements.status.value)
      .filter((node) => !term || searchableNode(node).includes(term))
      .map((node) => node.id),
  );

  if (term) {
    for (const edge of data.edges) {
      if (!searchableEdge(edge, nodesById).includes(term)) continue;
      const source = nodesById.get(edge.source);
      const target = nodesById.get(edge.target);
      for (const node of [source, target]) {
        if (!node) continue;
        if (elements.kind.value && node.kind !== elements.kind.value) continue;
        if (elements.status.value && node.status !== elements.status.value) continue;
        nodeMatches.add(node.id);
      }
    }
  }

  const edges = data.edges
    .filter((edge) => !elements.relation.value || edge.relation === elements.relation.value)
    .filter((edge) => !elements.confidence.value || edge.confidence === elements.confidence.value)
    .filter((edge) => nodeMatches.has(edge.source) && nodeMatches.has(edge.target));

  if (elements.relation.value || elements.confidence.value) {
    const connected = new Set(edges.flatMap((edge) => [edge.source, edge.target]));
    return {
      nodes: data.nodes.filter((node) => nodeMatches.has(node.id) && connected.has(node.id)),
      edges,
    };
  }
  return {nodes: data.nodes.filter((node) => nodeMatches.has(node.id)), edges};
}

function layoutNodes(nodes) {
  const positions = new Map();
  let maxRows = 1;
  for (const stage of STAGES) {
    const inStage = nodes
      .filter((node) => node.stage === stage)
      .sort((left, right) => left.label.localeCompare(right.label, "ja"));
    maxRows = Math.max(maxRows, inStage.length);
    inStage.forEach((node, index) => {
      positions.set(node.id, {x: X_BY_STAGE[stage], y: TOP_OFFSET + index * ROW_GAP});
    });
  }
  return {positions, height: Math.max(620, TOP_OFFSET + maxRows * ROW_GAP + 30)};
}

function pathBetween(source, target) {
  const sourceX = source.x + NODE_WIDTH;
  const sourceY = source.y + NODE_HEIGHT / 2;
  const targetX = target.x;
  const targetY = target.y + NODE_HEIGHT / 2;
  if (targetX > sourceX) {
    const bend = Math.max(50, (targetX - sourceX) / 2);
    return `M ${sourceX} ${sourceY} C ${sourceX + bend} ${sourceY}, ${targetX - bend} ${targetY}, ${targetX} ${targetY}`;
  }
  const startX = source.x + NODE_WIDTH / 2;
  const endX = target.x + NODE_WIDTH / 2;
  const arcY = Math.max(source.y, target.y) + NODE_HEIGHT + 24;
  return `M ${startX} ${source.y + NODE_HEIGHT} C ${startX} ${arcY}, ${endX} ${arcY}, ${endX} ${target.y + NODE_HEIGHT}`;
}

function shortLabel(label) {
  return label.length > 28 ? `${label.slice(0, 27)}…` : label;
}

function selectItem(type, id) {
  selected = {type, id};
  render(graphData);
}

function interactive(element, type, id, label) {
  element.setAttribute("tabindex", "0");
  element.setAttribute("role", "button");
  element.setAttribute("aria-label", label);
  element.addEventListener("click", () => selectItem(type, id));
  element.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    selectItem(type, id);
  });
}

function renderStageLabels() {
  for (const stage of STAGES) {
    const label = svgElement("text", {
      x: X_BY_STAGE[stage],
      y: 34,
      class: "graph-stage-label",
    });
    label.textContent = STAGE_LABELS[stage];
    elements.nodeLayer.append(label);
  }
}

function renderEdges(edges, positions) {
  for (const edge of edges) {
    const source = positions.get(edge.source);
    const target = positions.get(edge.target);
    if (!source || !target) continue;
    const pathData = pathBetween(source, target);
    const classes = [
      "graph-edge",
      `relation-${edge.relation.replaceAll("_", "-")}`,
      `confidence-${edge.confidence}`,
    ];
    if (selected?.type === "edge" && selected.id === edge.id) classes.push("is-selected");

    const visible = svgElement("path", {
      d: pathData,
      class: classes.join(" "),
      "data-edge-id": edge.id,
    });
    const hit = svgElement("path", {
      d: pathData,
      class: "graph-edge-hit",
      "data-edge-id": edge.id,
    });
    interactive(hit, "edge", edge.id, `${edge.source} ${edge.relation} ${edge.target}`);
    elements.edgeLayer.append(visible, hit);
  }
}

function renderNodes(nodes, positions) {
  for (const node of nodes) {
    const position = positions.get(node.id);
    if (!position) continue;
    const classes = ["graph-node", `status-${node.status}`];
    if (selected?.type === "node" && selected.id === node.id) classes.push("is-selected");
    const group = svgElement("g", {
      class: classes.join(" "),
      transform: `translate(${position.x} ${position.y})`,
      "data-node-id": node.id,
    });
    group.append(svgElement("rect"));

    const label = svgElement("text", {x: 16, y: 31, class: "graph-node-label"});
    label.textContent = shortLabel(node.label);
    const meta = svgElement("text", {x: 16, y: 58, class: "graph-node-meta"});
    meta.textContent = `${node.kind.toUpperCase()} · ${node.status.toUpperCase()}`;
    group.append(label, meta);
    interactive(group, "node", node.id, `${node.label}、${node.status}`);
    elements.nodeLayer.append(group);
  }
}

function appendDefinition(list, term, description) {
  const dt = document.createElement("dt");
  dt.textContent = term;
  const dd = document.createElement("dd");
  if (description instanceof Node) dd.append(description);
  else dd.textContent = description;
  list.append(dt, dd);
}

function linkFor(url, label) {
  const link = document.createElement("a");
  link.href = url;
  link.textContent = label;
  return link;
}

function renderNodeDetail(node, data) {
  elements.detailTitle.textContent = node.label;
  const list = document.createElement("dl");
  appendDefinition(list, "kind", node.kind);
  appendDefinition(list, "status", node.status);
  appendDefinition(list, "stage", node.stage);
  appendDefinition(list, "summary", node.summary);
  appendDefinition(list, "source", linkFor(node.url, "公開ソースを開く"));
  const related = data.edges.filter((edge) => edge.source === node.id || edge.target === node.id);
  appendDefinition(list, "visible edges", String(related.length));
  elements.detail.replaceChildren(list);
}

function renderEdgeDetail(edge, nodesById) {
  const source = nodesById.get(edge.source);
  const target = nodesById.get(edge.target);
  elements.detailTitle.textContent = `${source?.label ?? edge.source} → ${target?.label ?? edge.target}`;
  const list = document.createElement("dl");
  appendDefinition(list, "relation", edge.relation);
  appendDefinition(list, "confidence", edge.confidence);
  appendDefinition(list, "note", edge.note);
  const evidence = document.createElement("ol");
  evidence.className = "evidence-list";
  edge.evidence.forEach((url, index) => {
    const item = document.createElement("li");
    item.append(linkFor(url, `根拠 ${index + 1}`));
    evidence.append(item);
  });
  appendDefinition(list, "evidence", evidence);
  elements.detail.replaceChildren(list);
}

function renderDetail(data, view) {
  const nodesById = new Map(data.nodes.map((node) => [node.id, node]));
  if (selected?.type === "node") {
    const node = view.nodes.find((candidate) => candidate.id === selected.id);
    if (node) {
      renderNodeDetail(node, view);
      return;
    }
  }
  if (selected?.type === "edge") {
    const edge = view.edges.find((candidate) => candidate.id === selected.id);
    if (edge) {
      renderEdgeDetail(edge, nodesById);
      return;
    }
  }
  selected = null;
  elements.detailTitle.textContent = "nodeまたはedgeの詳細";
  const message = document.createElement("p");
  message.textContent = "graph上の項目を選択してください。根拠URL、確度、注記をここに表示します。";
  elements.detail.replaceChildren(message);
}

function renderEdgeTable(edges, nodesById) {
  elements.edgeTable.replaceChildren();
  if (!edges.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 4;
    cell.className = "empty-row";
    cell.textContent = "条件に一致するedgeはありません。";
    row.append(cell);
    elements.edgeTable.append(row);
    return;
  }
  for (const edge of edges) {
    const row = document.createElement("tr");
    for (const value of [
      nodesById.get(edge.source)?.label ?? edge.source,
      edge.relation,
      nodesById.get(edge.target)?.label ?? edge.target,
      edge.confidence,
    ]) {
      const cell = document.createElement("td");
      if (value === edge.relation) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "edge-table-button";
        button.textContent = value;
        button.addEventListener("click", () => selectItem("edge", edge.id));
        cell.append(button);
      } else {
        cell.textContent = value;
      }
      row.append(cell);
    }
    elements.edgeTable.append(row);
  }
}

function render(data) {
  const view = currentView(data);
  const {positions, height} = layoutNodes(view.nodes);
  elements.svg.setAttribute("viewBox", `0 0 1220 ${height}`);
  elements.edgeLayer.replaceChildren();
  elements.nodeLayer.replaceChildren();
  renderStageLabels();
  renderEdges(view.edges, positions);
  renderNodes(view.nodes, positions);

  const nodesById = new Map(data.nodes.map((node) => [node.id, node]));
  renderEdgeTable(view.edges, nodesById);
  renderDetail(data, view);
  const inferredCount = view.edges.filter((edge) => edge.confidence === "inferred").length;
  elements.summary.textContent =
    `node ${view.nodes.length} / ${data.nodes.length}、edge ${view.edges.length} / ${data.edges.length}、inferred ${inferredCount}`;
}

function scheduleRender() {
  window.requestAnimationFrame(() => render(graphData));
}

async function loadGraph() {
  try {
    const response = await fetch(GRAPH_URL, {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    graphData = await response.json();
    populateFilters(graphData);
    render(graphData);
  } catch (error) {
    elements.summary.textContent = `graphを読み込めませんでした: ${error.message}`;
  }
}

elements.form.addEventListener("input", scheduleRender);
elements.form.addEventListener("change", scheduleRender);
elements.form.addEventListener("reset", () => {
  selected = null;
  window.setTimeout(scheduleRender, 0);
});

loadGraph();
