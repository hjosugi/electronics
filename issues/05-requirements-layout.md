# [hw] 要件確定: キー数・レイアウト・スイッチ
Labels: hardware,decision

## 決めること
- キー数: 36 (3x5+3) か 42 (3x6+3)
- スイッチ: Choc v1 / Choc v2 / MX (ソケットの互換性とキーピッチに影響。Cheapino は 19.00mm ピッチ)
- column stagger の量
- ロータリーエンコーダの有無 (Cheapino は右側に 1 個)

## 完了条件
- KLE (keyboard-layout-editor) または ergogen でレイアウトを確定し docs/ に JSON を保存
- 決定理由を docs/adr/ に記録
