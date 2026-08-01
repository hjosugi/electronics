# [docs] NotebookLM 資料整備 + 発注準備
Labels: docs

## やること
- `notebooklm/split-keyboard-hotplug-safety.md`をNotebookLMへ登録し、一次資料は`docs/07-sources.md`と`docs/notebooklm-sources.md`から必要なページ/PDFを個別追加する
- `make notebooklm`と`make verify`で統合資料が生成元と一致することを確認する
- 設計判断は docs/adr/ に 1 決定 1 ファイルで残し、それも NotebookLM のソースに追加して自分の決定を検索可能にする
- 回路確定後: KiBot (または kicad-cli) で gerber 生成 → JLCPCB へ発注 (最小 5 枚)。発注チェックリストを docs/ に作る

## 完了条件
- NotebookLM notebook が稼働している
- 発注チェックリスト完成
