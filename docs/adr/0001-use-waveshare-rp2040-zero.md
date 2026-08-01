# ADR 0001: 初号機はWaveshare RP2040-Zeroモジュールを使う

- 状態: Accepted
- 決定日: 2026-07-31
- 対応Issue: [#8](https://github.com/hjosugi/electronics/issues/8)
- 適用範囲: 初号機（v0.1）の左側コントローラ

## 文脈

初号機は、1 MCU、8P8C、右側完全パッシブ方式です。左側にはUSBデバイス、キーマトリクス走査、QMKファームウェアを担当するMCUが必要です。

候補は次の2案でした。

1. RP2040-Zero完成モジュールをキャリア基板へ載せる
2. 素のRP2040、SPI flash、電源、クロック、USB-Cを左基板へ直接実装する

初号機の目的は、Japanese duplex matrixと中央接続の安全設計を検証することです。MCU周辺回路の新規設計まで同時に抱えると、USB、電源、実装不良、キーマトリクスの問題を切り分けにくくなります。

## 決定

初号機は、正規流通の**Waveshare RP2040-Zero**を採用します。ヘッダ実装品または同等の着脱構造を使い、故障時にモジュールを交換できる設計を優先します。

モジュールは左側だけに置きます。USB-Cも左側モジュールのPC接続専用です。中央8P8Cへ`VUSB`、`VSYS`、`5V`、`3V3`、`RAW`を接続しません。

## 根拠

### 初号機の実装リスクを減らせる

[Waveshare公式Wiki](https://www.waveshare.com/wiki/RP2040-Zero)によると、RP2040-ZeroにはRP2040、2 MB flash、USB Type-C、電源回路、BOOT/RESETボタンが実装済みです。キャスタレーション端子とピンヘッダ用端子があり、キャリア基板へ組み込めます。

素のRP2040には不揮発性flashが内蔵されません。[QMKのRP2040資料](https://docs.qmk.fm/platformdev_rp2040)も、外付けSPI flashに対応する第2段ブートローダーの選択が必要であることを説明しています。完成モジュールなら、この周辺回路を初号機の新規設計対象から外せます。

### QMKでRP2040を使える

[QMK公式RP2040サポート](https://docs.qmk.fm/platformdev_rp2040)にはGPIO、USBブート、`GENERIC_RP_RP2040`ボード、PIO/SIOドライバの設定が記載されています。今回の1 MCU方式ではQMK split transportを使わず、GPIOをJapanese duplex matrixへ割り当てます。

実際の`BOARD`、flash設定、BOOT/RESET設定はIssue #2のUF2ビルドで確定します。このADRはファームウェア設定の成功を先取りしません。

### GPIO数に余裕がある

Waveshareは、RP2040-Zeroについて29 GPIOのうち20本をピンヘッダから、残りをはんだパッドから引き出せると説明しています。36キー案の左右合計マトリクス信号は最大12本、42キー案は最大14本を見込むため、USBや基板上LEDなどの予約ピンを除外しても割り当て候補を検討できます。

これは概算です。最終的なGPIO割り当てと予約ピンはIssue #6で回路図、モジュールpinout、QMK設定を突き合わせて確定します。

## 電源に関する注意

Waveshare公式Wikiは、RP2040-Zeroの`VSYS`と`VUSB`が直接接続されており、外部電源を`VSYS`へ接続する場合は逆流防止ダイオードが必要と注意しています。

初号機では次を必須とします。

- PCからの給電は左側RP2040-ZeroのUSB-Cだけにする
- `VSYS`や`VUSB`へ別電源を同時接続しない
- 中央8P8Cへ電源を出さない
- 右側はスイッチとダイオードだけのパッシブ構成を維持する

RP2040のGPIOは5 V tolerantではありません。外部コネクタへ出るGPIOの保護、直列抵抗、ESD対策はIssue #7と#9で確定します。

## 影響

### 利点

- QFN、SPI flash、USB-C、電源回路の初回実装を省略できる
- BOOT/RESETボタンを使ってUF2を書き込みやすい
- 故障時にモジュール単位で交換できる
- 回路不良とキーマトリクス／ファームウェア不良を切り分けやすい

### 欠点

- 素のRP2040より基板が厚くなり、ケース高さが増える
- モジュール外形と端子位置にPCBレイアウトが拘束される
- 非正規クローンではflash、USB-C、電源回路が異なる可能性がある
- モジュールの供給終了や改版に備え、注文先と実物寸法を固定する必要がある

## 採用しなかった案

### 素のRP2040を直載せする

薄型化と部品配置の自由度は高くなりますが、初号機では採用しません。v2で再検討する場合は、Raspberry Pi公式の[Hardware design with RP2040](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf)と[Minimal-KiCAD](https://pip.raspberrypi.com/categories/814-rp2040)を正本にし、電源、decoupling、外付けflash、クロック、USB差動配線、BOOT回路を個別に検証します。

### Raspberry Pi Picoを載せる

公式リファレンスとしては優れていますが、初号機の小型左基板には外形が大きく、RP2040-Zeroを優先します。Picoはブレッドボード上のファームウェア検証用として利用できます。

## 実装条件

後続Issueでは次を守ります。

1. Waveshareの外形図と実物を照合してからKiCadフットプリントを確定する
2. 注文記録にメーカー、製品名、購入先、改版、実測寸法を残す
3. USB-C開口、BOOT/RESET操作、モジュール交換に必要なケース隙間を確保する
4. QMK UF2を実際にビルドし、RP2040-Zero実機へ書き込むまでIssue #2をcloseしない
5. GPIO割り当てはIssue #6、8P8C保護はIssue #7、波形評価はIssue #9で確定する

## 再検討条件

次のいずれかが成立した場合、新しいADRで置き換えを検討します。

- モジュール高さがケース要件を満たさない
- 必要GPIOを安全に割り当てられない
- 正規品を継続調達できない
- v2で薄型化または量産性を優先する
- RP2040以外へ移行する合理的な要件が確定する
