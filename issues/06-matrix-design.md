# [hw] Japanese duplex matrix 設計
Labels: hardware

## 背景
1 MCU で左右全キーを賄うため duplex matrix で信号線を半減する。行と列を双方向にスキャンするのでダイオードの向きが半分ずつ逆になる。

## やること
- 36 キー案: 片側 3x3 duplex (= 最大 18 キー/片側)、中央ケーブルは GND + 信号 6 本
- 42 キー案: 片側 4x3 duplex (= 最大 24 キー/片側)、GND + 信号 7 本
- ダイオード極性の表を作り回路図に反映
- 左右で row/col を共有しない (Cheapino v2 が ghosting 対策で左右分離した経緯を踏襲)
- 右側は完全パッシブ: スイッチ + ダイオードのみ。MCU も電源も置かない
- GPIO 割当表を作る (RP2040 は GPIO が豊富なので余裕を確認する程度)

## 完了条件
- 回路図が ERC pass
- GPIO 割当表とダイオード極性表が docs/ にある
