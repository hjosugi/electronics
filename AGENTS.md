# AGENTS.md

## 対象

このリポジトリは、1 MCU、8P8C、右側完全パッシブ方式の分割キーボードを設計・検証するための公開プロジェクトです。

## 作業ルール

- コメント、CLIメッセージ、Issue、公開ノートは原則として日本語で書く。
- 電気定格と安全性は、MCU・コネクタ・保護部品の一次資料を優先する。
- `VCC/5V/3V3/RAW`を中央コネクタへ追加しない。必要なら別アーキテクチャとしてIssueで合意する。
- 「シミュレーションが通った」「電源線がない」だけで、活線挿抜、ESD、誤配線、PoE誤接続に安全とは表現しない。
- PCのUSBポートを使って短絡試験をしない。電流制限付き電源と専用治具を使う。
- 第三者のフットプリント、回路、ファームウェアを取り込む前にライセンスと由来を記録する。
- 変更後は`make validate`を実行する。KiCadファイル追加後はERC/DRCも実行する。
- Issueの完了条件を満たしていない状態でcloseしない。

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
