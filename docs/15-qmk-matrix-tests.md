# QMK duplex matrix自動テストと2 × 2実機計画

確認日: 2026-08-01

## 現在の判定

QMKのnative GoogleTestを使う自動テストは合格しました。完成基板と2 × 2ブレッドボード試験は未実施なので、Issue #10はopenのままです。

| 検証 | 状態 | 証拠 |
| --- | --- | --- |
| 全36論理位置 | 合格 | 各位置を1個ずつ押し、対応bitだけが立つ |
| GPIO方向切替 | 合格 | 各相の前に6線input、出力Low 1本、settle後だけread |
| 非曖昧な同時押し | 合格 | 左右4キーで余分な位置なし |
| 右側抜線 | 合格 | 左キーを維持し、右キーを全解放 |
| 3-edge ghost path | 合格 | phantom候補を検出し、曖昧な半分を前状態へ固定 |
| 2 × 2実配線 | 未実施 | RP2040、ダイオード、470 Ω、ケーブルが必要 |

実行コマンドは固定QMK checkoutに対する通常ビルドと共通です。

```bash
QMK_HOME=/path/to/qmk_firmware make build-qmk
```

`build-qmk.sh`は`qmk test-c -t electronics_splitkb36`、`qmk lint`、RP2040 UF2 compileの順に実行します。test discoveryのためにテスト3ファイルだけをQMK checkoutへ一時コピーし、終了時に削除します。既存の同名keyboard/testがある場合は上書きせず停止します。

## テストモデル

テストと実機は[`duplex_matrix.c`](../firmware/qmk/keyboards/electronics/splitkb36/duplex_matrix.c)を共有します。GPIO関数だけをcallbackにし、テスト側は12本のpinと押下ダイオードを有向グラフとして模擬します。

- Bank A: `row -> column`
- Bank B: `column -> row`
- input pinから現在のoutput-low pinへ有向経路があればLow
- 右側をdisconnectするとGP6–GP11にLow経路を作らない

3本の押下が`R0 -> C0 -> R1 -> C1`のような交互経路を作ると、理想ダイオードモデルでは未押下の`R0 -> C1`もLowになります。reverse方向も同じです。raw scanだけから3実押下と4実押下を完全には区別できないため、firmwareは該当半分の6 logical columnsを前回状態に保ちます。反対側は通常どおり更新します。

これはphantom keyを出さない保守策ですが、曖昧な形の正当な3キー目・4キー目も一時的に認識しません。電圧降下で実機にghostが出ない場合でも、この制限は初号firmwareに残ります。実測後に解除または絞り込む場合は、同じ自動テストと新しい実測証拠が必要です。

論理matrixは3 × 12の全位置を36キーが使うため、未使用位置はありません。全座標を1回ずつ走査するテストが、欠落と重複を同時に検出します。

## 2 × 2 duplex実験系

PC直結で故障条件を作らず、電流制限付き3.3 V/5 V電源または保護したUSB hubを使います。中央リンクの通電挿抜評価はIssue #11の治具ができるまで行いません。

最小配線は2 row + 2 column、Bank A/B各4キーの計8キーです。

| 信号 | RP2040 | 直列抵抗 | 用途 |
| --- | --- | ---: | --- |
| R0 | GP0 | 470 Ω | row 0 |
| R1 | GP1 | 470 Ω | row 1 |
| C0 | GP3 | 470 Ω | column 0 |
| C1 | GP4 | 470 Ω | column 1 |

Bank Aは`row - switch - diode A -> K - column`、Bank Bは`column - switch - diode A -> K - row`です。実装前後に無通電導通とダイオード極性を確認します。

### 実施項目

1. 電流上限を低く設定し、無押下時電流と3V3を記録する。
2. 8キーを1個ずつ押し、期待するHID keyだけが出ることを確認する。
3. Bank A/Bを含む2キー組合せを全数確認する。
4. `R0 -> C0 -> R1 -> C1`とreverseの3-key pathを作り、phantomがHIDへ出ないことを確認する。
5. 右側相当キーを押したまま4信号を同時に開放し、key-upが出て押下残りがないことを確認する。
6. 再接続後にUSB再列挙やMCU resetなしで全キーが戻ることを確認する。

### 記録テンプレート

| 項目 | 記録 |
| --- | --- |
| main / firmware commit | 未実施 |
| UF2 SHA-256 | 未実施 |
| RP2040 board / revision | 未実施 |
| diode / resistor lot | 未実施 |
| 電源 / current limit | 未実施 |
| 8 single keys | 未実施 |
| 2-key combinations | 未実施 |
| ghost paths | 未実施 |
| disconnect / reconnect | 未実施 |
| oscilloscope captures | 未実施 |

実測欄が埋まり、結果をcommitするまでIssue #10をcloseしません。
