# [sim] ファームウェアロジック検証 (QMK Unit Testing + 実機)
Labels: simulation,firmware

## やること
- QMK Unit Testingで行/列方向切替、全キー、未使用位置、抜線時のキー解放を検証
- 実物Pico + ブレッドボードで2x2 duplex matrixを組み、スキャンコードを実測。ホットプラグ挙動や実配線の癖はソフトウェアテストでは分からない

## 完了条件
- QMKテストが自動実行できる
- 2x2実験系で全キー検出、抜線時の解放、ゴーストなしを確認
- スキャンコードと試験結果を`firmware/`、`docs/`へコミット
