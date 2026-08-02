# [docs] Issue依存・証拠graphをPagesへ追加
Labels: docs,repo

## 背景

回路、firmware、実機試験、製造gate、releaseの依存関係が文書とIssueに分散している。GitHub Pagesだけで、何が何をblock、validate、publishするかを追えるようにする。

## やること

- `docs/graph/project-graph.json`を正本にする
- nodeへ種別、状態、stage、URL、要約を持たせる
- directed edgeへ関係種別、確度、根拠URL、注記を持たせる
- verifiedとinferredを視覚的に区別する
- search、node kind、status、edge relation、confidenceで絞り込めるPages画面を作る
- 外部CDNやweb frameworkを使わない
- schema、endpoint、evidence、重複、self-loopをCI検査する
- docs CSS tokenを共用する

## 完了条件

- Issue #1/#10/#11/#12/#16、主要ADR、CI証拠、releaseの関係が表示される
- 「今なぜ発注できないか」をblocker edgeから辿れる
- edgeの根拠と確度を詳細panelで確認できる
- `make validate`とPages workflowがgreen
- live Pagesで匿名read-backできる

## 安全境界

graphは進捗可視化であり、実機未完を合格に変えない。CI、simulation、実測、製造readyを別nodeとして扱う。
