/**
 * project graphの検索・絞り込みモデル。
 *
 * DOMから分離し、GitHub PagesとNode標準テストで同じ規則を使う。
 */

export function searchableNode(node) {
  return [node.id, node.label, node.kind, node.status, node.stage, node.summary]
    .join(" ")
    .toLocaleLowerCase("ja");
}

export function searchableEdge(edge, nodesById) {
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

export function filterGraph(data, filters = {}) {
  const term = (filters.search ?? "").trim().toLocaleLowerCase("ja");
  const kind = filters.kind ?? "";
  const status = filters.status ?? "";
  const relation = filters.relation ?? "";
  const confidence = filters.confidence ?? "";
  const nodesById = new Map(data.nodes.map((node) => [node.id, node]));
  const nodeMatches = new Set(
    data.nodes
      .filter((node) => !kind || node.kind === kind)
      .filter((node) => !status || node.status === status)
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
        if (kind && node.kind !== kind) continue;
        if (status && node.status !== status) continue;
        nodeMatches.add(node.id);
      }
    }
  }

  const edges = data.edges
    .filter((edge) => !relation || edge.relation === relation)
    .filter((edge) => !confidence || edge.confidence === confidence)
    .filter((edge) => nodeMatches.has(edge.source) && nodeMatches.has(edge.target));

  if (relation || confidence) {
    const connected = new Set(edges.flatMap((edge) => [edge.source, edge.target]));
    return {
      nodes: data.nodes.filter((node) => nodeMatches.has(node.id) && connected.has(node.id)),
      edges,
    };
  }
  return {nodes: data.nodes.filter((node) => nodeMatches.has(node.id)), edges};
}
