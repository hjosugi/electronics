# 検証処理の並列化と性能

`make validate`と`make validate-hardware`は、互いに独立した検査を同時実行します。高速化のために検査を省略せず、各プロセスのログを一時ファイルへ分離してから決まった順序で表示します。

## 並列化の境界

[`scripts/run-validation.sh`](../scripts/run-validation.sh)は次を並列実行します。

- NotebookLM統合Markdownの再生成差分
- 36キーレイアウトの再生成差分、値域、不変条件
- ドキュメントCSSの必須変数、タイポグラフィ直書き、インラインstyle
- Markdownローカルリンク
- Bash構文、ShellCheck、Issue形式、`git diff --check`
- ngspiceモデル
- KiCad ERC/DRC一式（`validate-hardware`のみ）

[`scripts/check-spice.sh`](../scripts/check-spice.sh)は4回路を並列実行し、成功時は測定値だけを表示します。失敗時は該当回路の完全なngspiceログを表示します。

KiCadの通常検査とnegative testは、KiCad CLIのインスタンスロック競合を避けるため、[`scripts/check-kicad-suite.sh`](../scripts/check-kicad-suite.sh)の中で順番に実行します。KiCad一式は、他の検査とは並列に動きます。

## 2026年8月1日の測定

Nix storeのKiCad 10.0.5、ngspice 45、ShellCheck 0.11.0を使い、ウォームキャッシュで`validate-hardware`相当の全検査を各3回実行しました。この測定値はレイアウト/CSS検査を追加する前の基準値であり、追加後の性能値としては扱いません。

| 実装 | 1回目 | 2回目 | 3回目 | 中央値 |
|---|---:|---:|---:|---:|
| 完全直列 | 5,487 ms | 5,485 ms | 4,587 ms | 5,485 ms |
| 並列ランナー | 3,181 ms | 3,097 ms | 2,722 ms | 3,097 ms |

中央値では約44%短縮しました。この値は当該ホストと負荷状況での参考値であり、GitHub Actionsや別CPUで同じ比率になる保証はありません。

## CIの無駄な実行を減らす

`starter-ci`と`hardware-ci`にはref単位の`concurrency`を設定しています。同じブランチへ新しいcommitがpushされた場合、古い実行をキャンセルし、最新commitの検証を優先します。

性能変更後も、次のコマンドが合格することを必須とします。

```bash
make validate-hardware
```
