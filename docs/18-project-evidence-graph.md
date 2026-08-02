# Issue依存・証拠graph

確認日: 2026-08-01

## 目的

[公開graph](graph/)は、設計判断、実装、検証、公開物を有向edgeで結び、現在止まっている理由を検索できるようにします。GitHub Pages上で完結し、追加サービス、CDN、外部JavaScript frameworkは使いません。

データの正本は[`project-graph.json`](graph/project-graph.json)、表示は[`index.html`](graph/index.html)と[`graph.js`](graph/graph.js)、検索・絞り込み規則は[`graph-model.mjs`](graph/graph-model.mjs)です。手書きの解説、表示、データ処理を分離し、自動処理がcuratedな関係を上書きしない構造にします。

## node

nodeは次を持ちます。

- `id`: 永続的な識別子
- `kind`: `issue`、`decision`、`artifact`、`evidence`、`release`、`gate`
- `status`: `verified`、`open`、`blocked`、`planned`
- `stage`: `decision`、`implementation`、`verification`、`publication`
- `url`: 詳細または証拠の公開URL
- `summary`: そのnodeが証明する範囲

`verified`はnodeの存在や記載済みの検査が確認済みという意味です。キーボード全体の安全性、人体適合、製造可能性を一括して保証しません。

## edge

edgeは向きに意味を持ちます。

| relation | 読み方 |
| --- | --- |
| `defines` | sourceの判断がtargetの構造を定義する |
| `implements` | sourceがtargetの判断を実装する |
| `validates` | sourceの証拠がtargetの限定された性質を検査する |
| `blocked_by` | sourceの完了がtargetの未完証拠で止まる |
| `depends_on` | sourceを成立させる前にtargetが必要 |
| `publishes` | sourceがtargetを公開する |
| `may_change` | sourceがtargetへ影響する可能性があるが未確定 |

全edgeに`confidence`と1件以上の`evidence`を要求します。

- `verified`: ADR、commit、Issue、CI、公開文書で関係を確認できる
- `inferred`: 設計上あり得るが、採用判断や実測がまだない

`inferred`を実線のverified edgeへ格上げする場合、先にADRまたはIssueへ根拠を残します。

## 発注blockerの読み方

`order-ready` nodeから`blocked_by`を辿ると、少なくとも次が未完です。

- Issue #10の2 × 2実配線
- Issue #11の活線挿抜
- Issue #12のNotebookLM引用smoke test
- 製造用PCBとGerber/BOM/viewer

CI successやv0.4.0 releaseは、それらの代用ではありません。

## 検査

```bash
make check-project-graph
python3 scripts/check-project-graph.py --self-test
```

検査はschema、enum、ID重複、dangling edge、self-loop、根拠URL、発注gateの必須blockerを確認します。Node.jsがある環境では、既定表示、issue status、relation、confidence、全文検索のmodel test 5件も実行します。表示側はJSONを読み取るだけで、状態を推測して書き換えません。

## 更新規則

1. 正本JSONへnodeまたはedgeを追加する。
2. verified edgeには公開根拠URLを付ける。
3. 推測なら`inferred`のまま注記と再検討条件を書く。
4. `make validate`を実行する。
5. Issueの解除条件とgraphのstatusが一致するか確認する。

未解決の関係を見つけてもgraph内だけで完了扱いせず、再現手順と解除条件をGitHub Issueへ追加します。
