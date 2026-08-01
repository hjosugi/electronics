# [sim] ファームウェアロジック検証 (QMK Unit Testing + 実機)
Labels: simulation,firmware

## やること
- QMK Unit Testingで行/列方向切替、全キー、未使用位置、抜線時のキー解放を検証
- 実物Pico + ブレッドボードで2x2 duplex matrixを組み、スキャンコードを実測。ホットプラグ挙動や実配線の癖はソフトウェアテストでは分からない

## 完了条件
- QMKテストが自動実行できる
- 2x2実験系で全キー検出、抜線時の解放、ゴーストなしを確認
- スキャンコードと試験結果を`firmware/`、`docs/`へコミット

## 進捗
- [x] QMK native GoogleTestで全36位置、方向切替、抜線、ghost pathを自動実行
- [x] 理想ダイオード最悪条件でphantomを出さない保守的filterを実装
- [ ] 2 × 2ブレッドボードで8キー、組合せ、抜線、再接続を実測
- [ ] 実測結果、基板/部品/電源/UF2 SHAを記録
