# Architecture Decision Records

設計判断は、結論だけでなく前提、代替案、影響、再検討条件を残すため、1決定につき1ファイルで記録します。

## 状態

- `Proposed`: 検討中。回路や発注の前提にしない
- `Accepted`: 採用済み。後続設計はこの判断を前提にする
- `Superseded`: 後続ADRで置き換え済み
- `Rejected`: 検討したが採用しない

## 一覧

| ADR | 状態 | 判断 |
|---|---|---|
| [0001](0001-use-waveshare-rp2040-zero.md) | Accepted | 初号機はWaveshare RP2040-Zeroモジュールを使う |
| [0002](0002-use-36-key-choc-v1-layout.md) | Accepted | 初号機は調整可能な36キーChoc v1レイアウトとする |
| [0003](0003-use-470-ohm-and-dual-ended-tvs.md) | Accepted | 右matrix信号へ470 Ωと両端TPD4E05U06DQAを使う |

ADRを変更するときは本文を書き換えて履歴を消さず、新しいADRから置き換え元を参照します。
