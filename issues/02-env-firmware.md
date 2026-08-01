# [env] QMK ファームウェア環境構築
Labels: env,firmware

## 背景
1 MCU 構成なので split transport (serial/I2C) は不要。ただし Japanese duplex matrix は QMK 標準のマトリクススキャンで表現できないため custom matrix を書く。Cheapino のコードが参考実装。ただし Cheapino firmware は本家 QMK 未マージで、tompi/qmk_firmware の cheapino branch にある点に注意。

## やること
- QMK本体を完全なcommit SHAへ固定する
- CachyOSでは`sudo pacman -S qmk`または`nix shell nixpkgs#qmk`を使う
- tompi/qmk_firmware (cheapino branch) の keyboards/cheapino を読む。特に行/列を双方向スキャンする matrix 実装
- RP2040用の3 × 12 custom matrixと36キーkeymapを作る
- ローカルとGitHub ActionsでビルドしてUF2が出ることを確認

## 完了条件
- 自作keyboard定義のUF2が固定QMK commitからローカルでビルドできる
- CIでも同じ定義をビルドし、UF2 artifactを取得できる
