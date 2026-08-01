# [ci] ERC/DRC + 製造出力の GitHub Actions
Labels: ci

## 背景
回路変更のたびに手動チェックしない。`kicad-cli`でERC/DRCを実行し、回路が安定した後にKiBotでGerber/BOM/PDFを自動生成する。KiBotの採用バージョンとKiCad 10対応状況は実装時に公式文書で再確認する。

## やること
- 同梱 `.github/workflows/hardware-ci.yml` のファイル名を実プロジェクト名に合わせる
- `kicad-cli sch erc` / `kicad-cli pcb drc` に `--exit-code-violations` を付け、violation で CI を fail させる
- 回路が安定してきたら KiBot (INTI-CMNB/KiBot, GitHub Action あり) を追加し gerber・interactive BoM・PDF 図面を artifact 化

## 完了条件
- PR で ERC/DRC が自動実行され、violation で赤くなる
