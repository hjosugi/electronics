# RP2040 QMKファームウェア環境

## 結論

初号機用のQMK定義は、1個のWaveshare RP2040-Zeroから左右両方を直接走査します。右側にMCUはなく、中央8P8Cには6本のマトリクス信号とGNDだけを通します。QMKのsplit transport、VCC、VBUS、RAWは中央接続に使いません。

成果物は[`firmware/qmk/`](../firmware/qmk/)にあります。上流QMKは`qmk-version.env`の完全なcommit SHAへ固定し、ローカルとGitHub Actionsで同じソースからUF2を生成します。

## 論理マトリクス

各半分は3本のrowと3本のcolumnを双方向に走査するJapanese duplex matrixです。

| 半分 | row GPIO | column GPIO | QMK論理column |
| --- | --- | --- | --- |
| 左 | GP0, GP1, GP2 | GP3, GP4, GP5 | 0–5 |
| 右 | GP6, GP7, GP8 | GP9, GP10, GP11 | 6–11 |

QMKからは3 row × 12 column、合計36キーに見えます。Bank AはcolumnをLow出力にしてrowを読み、Bank BはrowをLow出力にしてcolumnを読みます。相を切り替えるたびに対象半分の6線を入力pull-upへ戻し、出力Lowは同時に1本だけ、切替後は1 µs待ちます。

RP2040のGPIOは5 V tolerantではありません。中央接続に電源を通さない設計でも、採用済みの470 Ω直列抵抗、ESD保護、GND、ケーブル規定を回路図どおり維持してください。

## 再現ビルド

QMK本体を固定commitへcheckoutし、QMK CLI 1.2.0を使います。CachyOSのホストへ恒久インストールしない場合はNix一時環境を利用できます。

```bash
source firmware/qmk/qmk-version.env
git clone https://github.com/qmk/qmk_firmware.git /tmp/qmk_firmware
git -C /tmp/qmk_firmware checkout "$QMK_REF"
git -C /tmp/qmk_firmware submodule update --init --recursive
nix shell nixpkgs#qmk -c ./scripts/build-qmk.sh /tmp/qmk_firmware
```

ビルドスクリプトはQMKのHEADを照合してから、keyboard定義を一時的なsymlinkで重ねます。生成物は`dist/qmk/`へコピーされますが、UF2はGitへcommitしません。PRでは`qmk-ci`が同じビルドを行い、14日間のActions artifactとして保存します。
コンパイル前には`qmk lint`も実行し、上流QMKのmetadata規約とのずれを拒否します。

### ローカル合格記録（2026-08-01）

| 項目 | 値 |
| --- | --- |
| QMK commit | `4ffb1ab16c443f2def5949d39b56057c0c88c88b` |
| QMK CLI | `1.2.0` |
| ARM GCC | `15.2.1 20251203` |
| UF2サイズ | 46,080 bytes |
| UF2 SHA-256 | `83fb62e0e4bc59dcc3bd4f0eb2a621056f9755e12020d2ce715ccac74f7c03d8` |

この記録は「ソースがRP2040向けにコンパイルできた」証拠です。GPIOの電圧、ダイオード極性、同時押し、抜線中の押下残り、活線挿抜安全性を証明するものではありません。

書き込み時はRP2040-ZeroをBOOTSELモードにし、表示された`RPI-RP2`ドライブへUF2をコピーします。基板がない現段階では書き込みと実キー検証をIssue #10の完了証拠にはしません。

## 静的検査

`make check-qmk`はネットワークやQMK checkoutなしで次を検査します。

- RP2040 / UF2 bootloader
- 3 × 12の全座標と36キー
- GP0–GP11の重複なし割り当て
- `CUSTOM_MATRIX = lite`
- 入力pull-upへの中立化と1 µs待ち
- QMK split transportおよび電源rail依存がないこと
- ローカルpinとCI pinが同じQMK commitであること

## 上流資料

- [QMK: Set Up Your Environment](https://docs.qmk.fm/newbs_getting_started)
- [QMK: RP2040 Driver](https://docs.qmk.fm/platformdev_rp2040)
- [QMK: Custom Matrix](https://docs.qmk.fm/custom_matrix)
- [QMK: Data Driven Configuration](https://docs.qmk.fm/reference_info_json)
- [Cheapino custom matrix（設計比較）](https://github.com/tompi/qmk_firmware/blob/cheapino/keyboards/cheapino/matrix.c)

Cheapinoの双方向走査は設計比較に使いましたが、本実装は現在のQMK `CUSTOM_MATRIX = lite` API、今回確定したGPIO割り当て、安全な中立状態に合わせて新規に記述しています。
