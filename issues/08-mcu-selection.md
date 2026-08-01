# [hw] MCU まわり: RP2040-Zero モジュール vs 素 RP2040
Labels: hardware,decision

## 選択肢
- 案A: RP2040-Zero モジュールをソケット実装 (Cheapino 方式)。USB-C 付き・実装難度最低・故障時に交換可能
- 案B: 素の RP2040 + SPI flash + 水晶 + USB-C を自分で載せる。基板は薄く綺麗だが部品点数・実装難度・設計リスクが上がる

## 方針
初号機は案A を推奨。案B は v2 で挑戦する。案B に進む場合は Raspberry Pi 公式の "Hardware design with RP2040" を必読資料にする。

## 完了条件
- 採用案と理由を docs/adr/ に記録
