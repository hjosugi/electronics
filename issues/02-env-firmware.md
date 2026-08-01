# [env] QMK ファームウェア環境構築
Labels: env,firmware

## 背景
1 MCU 構成なので split transport (serial/I2C) は不要。ただし Japanese duplex matrix は QMK 標準のマトリクススキャンで表現できないため custom matrix を書く。Cheapino のコードが参考実装。ただし Cheapino firmware は本家 QMK 未マージで、tompi/qmk_firmware の cheapino branch にある点に注意。

## やること
- `sudo pacman -S qmk` → `qmk setup`
- tompi/qmk_firmware (cheapino branch) の keyboards/cheapino を読む。特に行/列を双方向スキャンする matrix 実装
- `qmk new-keyboard` で雛形作成。MCU は RP2040 を直接指定
- ビルドして uf2 が出ることを確認

## 完了条件
- 自作 keyboard 定義の uf2 がローカルでビルドできる
