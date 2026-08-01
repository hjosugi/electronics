# 36キーJapanese duplex matrixと8P8C保護回路

確認日: 2026-08-01

この文書は、初号機の参照回路
[`hardware/split-keyboard/split-keyboard.kicad_sch`](../hardware/split-keyboard/split-keyboard.kicad_sch)
について、GPIO、ダイオード極性、中央ケーブル、保護部品、故障時の境界を定義します。
KiCad回路図とERCは製造前の設計証拠ですが、PCB配線、活線挿抜、ESD、誤接続に合格したことを意味しません。

## 結論

- 左右はそれぞれ独立した`3 row + 3 column`のJapanese duplex matrixとする
- 片側18キーを、向きの異なる9キーのBank AとBank Bへ分ける
- 左側のWaveshare RP2040-Zero 1個だけを使い、右側にMCUと電源を置かない
- 中央8P8Cは`GND 2本 + 右側matrix信号6本`だけとする
- 6本の信号にはMCU側で`470 Ω`を直列に入れる
- 8P8C入口には左右とも`TPD4E05U06DQA`を2個ずつ置く
- 専用ストレートケーブルだけを使い、`SPLIT ONLY / NO LAN`を基板とケースへ表示する
- Ethernet、PoE、電話設備、導通不明ケーブルへの接続は禁止する

中央ケーブルに電源がないため、TRRSで起き得るVCC–GNDの擦過短絡経路は存在しません。
一方、GPIO–GND、GPIO同士の競合、ESD、PoE電圧、コネクタGNDのインダクタンスは残るため、
「中央無給電」だけを根拠にホットプラグ安全とは断定しません。

## 回路の構成

```text
PC USB
  |
Waveshare RP2040-Zero (left only)
  |-- L_R0..L_R2 + L_C0..L_C2 ------ left 18-key duplex matrix
  |
  `-- R_R0..R_R2 + R_C0..R_C2
        |  470 ohm x 6, MCU side
        |  TPD4E05U06DQA x 2, left connector entry
        +-- 8P8C straight cable: GND x2 + signal x6 --+
                                                        |
                                  TPD4E05U06DQA x 2 ----+
                                                        |
                                     right 18-key duplex matrix
```

`J3`はRP2040-ZeroのGPIOだけを表す回路図上の抽象コネクタです。モジュールのUSB、5 V、
3V3、GNDを含む電源回路と実装フットプリントは、PCB設計時に公式回路図と実部品を照合して追加します。
電源ピンを省略した理由は、中央リンクへ電源を出さない境界を明瞭にするためであり、
モジュール全体の電源設計が完了したという意味ではありません。

## GPIO割り当て

[Waveshare公式RP2040-Zero回路図](https://files.waveshare.com/upload/4/4c/RP2040_Zero.pdf)で
GPIO0からGPIO11が外部へ出ていることを確認し、次の連続した12本を割り当てます。
オンボードRGBのGPIO16は使いません。

| RP2040-Zero | net | 用途 |
| ---: | --- | --- |
| GPIO0 | `L_R0` | 左row 0 |
| GPIO1 | `L_R1` | 左row 1 |
| GPIO2 | `L_R2` | 左row 2 |
| GPIO3 | `L_C0` | 左column 0 |
| GPIO4 | `L_C1` | 左column 1 |
| GPIO5 | `L_C2` | 左column 2 |
| GPIO6 | `R_R0_GPIO` | 470 ΩよりMCU側の右row 0 |
| GPIO7 | `R_R1_GPIO` | 470 ΩよりMCU側の右row 1 |
| GPIO8 | `R_R2_GPIO` | 470 ΩよりMCU側の右row 2 |
| GPIO9 | `R_C0_GPIO` | 470 ΩよりMCU側の右column 0 |
| GPIO10 | `R_C1_GPIO` | 470 ΩよりMCU側の右column 1 |
| GPIO11 | `R_C2_GPIO` | 470 ΩよりMCU側の右column 2 |

[RP2040データシート](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)では、
GPIOのdrive strengthは2/4/8/12 mAから選べますが、これは電流制限器ではありません。
IOVDD側とVSS側の全GPIO電流合計はそれぞれ50 mAが上限です。firmwareでは2 mA、slow slewを初期値とし、
走査方向を変える前に全6線を入力へ戻します。具体的な実装と同時押し試験はIssue #10で行います。

## 8P8Cピン割り当て

J1とJ2は同じ番号を同じnetへ接続し、T568A/Bのペア名を通信上の意味には使いません。

| 8P8C pin | net | 種類 |
| ---: | --- | --- |
| 1 | `GND` | 基準/ESDリターン |
| 2 | `R_R0` | 右matrix信号 |
| 3 | `R_R1` | 右matrix信号 |
| 4 | `R_R2` | 右matrix信号 |
| 5 | `R_C0` | 右matrix信号 |
| 6 | `R_C1` | 右matrix信号 |
| 7 | `R_C2` | 右matrix信号 |
| 8 | `GND` | 基準/ESDリターン |

両端をGNDにしたのは、基準線を2本確保し、一般的な10/100 crossoverでpin 1が入れ替わっても
pin 8のGNDが残るようにするためです。これはcrossoverを許容する設計ではありません。
任意の誤配線や断線ではGNDが失われるため、専用ストレートケーブル以外を使いません。

中央8ピンには`VCC`、`VBUS`、`VSYS`、`RAW`、`5V`、`3V3`を割り当てません。
この禁止条件は`make check-safety-schematic`がKiCad XML netlistから検査します。

## ダイオード極性と物理キーの対応

採用ダイオードはDiodes Incorporated `1N4148W-7-F`、SOD123です。
[メーカー資料 DS30086 Rev. 31-2](https://www.diodes.com/datasheet/download/1N4148W.pdf)では、
注文型番、カソードバンド、最大4 nsのreverse recovery、最大2 pFの容量が示されています。
KiCadシンボルはpin 1=`K`、pin 2=`A`です。

各キーは`source net - switch - A(pin 2) -> K(pin 1) - destination net`の順に接続します。
Bank AとBank Bでsource/destinationを逆にし、同じ6本を2方向に走査します。

| Bank | 対象キー（各半分） | diode電流方向 | 検出時のdrive/input |
| --- | --- | --- | --- |
| A | 物理matrix C0–C2、計9キー | `R0..R2 -> C0..C2` | columnをLow、rowをpull-up入力 |
| B | 物理matrix C3–C4 + thumb 0–2、計9キー | `C0..C2 -> R0..R2` | rowをLow、columnをpull-up入力 |

各半分の完全な対応は次です。右側は先頭の`L`を`R`に読み替え、同じ論理配置を使います。

| 物理キー | Bank | source（A側） | destination（K側） |
| --- | --- | --- | --- |
| `L-M-C0-R0` | A | `L_R0` | `L_C0` |
| `L-M-C0-R1` | A | `L_R1` | `L_C0` |
| `L-M-C0-R2` | A | `L_R2` | `L_C0` |
| `L-M-C1-R0` | A | `L_R0` | `L_C1` |
| `L-M-C1-R1` | A | `L_R1` | `L_C1` |
| `L-M-C1-R2` | A | `L_R2` | `L_C1` |
| `L-M-C2-R0` | A | `L_R0` | `L_C2` |
| `L-M-C2-R1` | A | `L_R1` | `L_C2` |
| `L-M-C2-R2` | A | `L_R2` | `L_C2` |
| `L-M-C3-R0` | B | `L_C0` | `L_R0` |
| `L-M-C3-R1` | B | `L_C0` | `L_R1` |
| `L-M-C3-R2` | B | `L_C0` | `L_R2` |
| `L-M-C4-R0` | B | `L_C1` | `L_R0` |
| `L-M-C4-R1` | B | `L_C1` | `L_R1` |
| `L-M-C4-R2` | B | `L_C1` | `L_R2` |
| `L-T0` | B | `L_C2` | `L_R0` |
| `L-T1` | B | `L_C2` | `L_R1` |
| `L-T2` | B | `L_C2` | `L_R2` |

[QMKのCustom Matrix](https://docs.qmk.fm/custom_matrix)は、`COL2ROW`と`ROW2COL`を同時に使う
不規則matrixをcustom scanの用途として挙げています。ファームウェアは`CUSTOM_MATRIX = lite`を第一候補にし、
Bank A、全線入力化、Bank B、全線入力化の順で走査します。

## 保護部品

| 機能 | 採用品/注文型番 | 実装 | 数量 | 採用根拠 |
| --- | --- | --- | ---: | --- |
| GPIO直列抵抗 | Panasonic `ERJ3EKF4700V` | 0603、470 Ω、1%、0.1 W | 6 | 3.3 V短絡モデルで6.666 mA、通常想定20.9 mW |
| ESDアレイ | TI `TPD4E05U06DQA` | USON-10、4 channel | 4 | 5.5 V VRWM、0.5 pF typ/channel、±12 kV contact部品定格 |
| matrix diode | Diodes Inc. `1N4148W-7-F` | SOD123 | 36 | 明確な注文型番と極性、4 ns、2 pF max |

[Panasonic製品ページ](https://industrial.panasonic.com/ww/products/pt/general-purpose-chip-resistors/models/ERJ3EKF4700V)
は`ERJ3EKF4700V`を470 Ω、1%、0603、0.100 Wとしています。

[TI TPD4E05U06 datasheet Rev. O](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf)は、
TPD4品のI/O容量を0.5 pF typical、reverse standoffを5.5 V、breakdownを6.5 V minimum、
IEC 61000-4-2を±12 kV contact/±15 kV airとしています。これらは部品単体の条件です。
10 V at 1 Aというクランプ例はRP2040のI/O絶対最大`IOVDD + 0.5 V`より高く、
直列抵抗、配線インダクタンス、GND return、放電源を含む基板全体の合格を保証しません。

TPD4は8P8C直後、470 ΩはMCU直前に配置します。右基板にもTVSを置きますが、TVSは受動部品であり、
右側へ電源を供給しません。右TVSの放電電流はケーブルGNDへ戻るため、短く太いGND配線と両GNDピンが必要です。

8P8Cジャックの注文型番とフットプリントは、ケース高さとPCB固定穴を決めるまでは確定しません。
回路図の`Connector:8P8C`は論理シンボルです。製造前に採用ジャックのpin numberingを図面と導通で照合します。

## 470 Ω選定シミュレーション

[`hardware/sim/rj45-protection-selection.cir`](../hardware/sim/rj45-protection-selection.cir)は、
220/330/470 Ωを同時に比較します。2 mの集中定数は、Belden 1583Eの
[最大mutual capacitance 56 pF/m、最大導体DCR 95 Ω/km](https://catalog.belden.com/techdata/EN/1583E_techdata.pdf)
を参考に、ケーブル120 pF、接点込み1 Ωとしました。RP2040の5 pFはデータシートの
I/O timingで使われるnominal loadを比較用負荷として採用した値であり、入力容量の最大値ではありません。
両端TVSは0.5 pFを2個、pullは80 kΩ、GPIO出力抵抗25 Ωは比較用の仮定です。

ngspice 45の結果:

| 直列抵抗 | 10–90% rise | HIGH（2 µs） | 閉キーLOW（50 kΩ pull） | cable側GND短絡電流 |
| ---: | ---: | ---: | ---: | ---: |
| 220 Ω | 68.75 ns | 3.2899 V | 0.4928 V | 13.47 mA |
| 330 Ω | 99.93 ns | 3.2854 V | 0.5048 V | 9.294 mA |
| 470 Ω | 140.00 ns | 3.2797 V | 0.5199 V | 6.666 mA |

閉キーLOWは、sense側とdrive側の両方に候補抵抗を入れ、MCU入力pinで測っています。
470 Ωでも1 µs以上のsettling timeに対して約7倍の時間余裕を取り、HIGHはRP2040のVIH 2.0 V以上、
閉キーLOWはVIL 0.8 V以下です。単線短絡のモデル電流は6.666 mA、6線の独立したGND短絡を単純合算すると
39.996 mAで、RP2040の全GPIO source上限50 mAを下回ります。330 Ωでは同じ合算が55.77 mAとなるため、
速度差を優先する根拠がない初号機では470 Ωを採用します。

LOW側の1N4148Wは近似モデルであり、RP2040のdrive strengthは電流制限ではなく、25 Ωも保証値ではありません。
6線合算も他のGPIO負荷、抵抗許容差、電源変動、MCU内の電流分配を含まないため、複数線短絡の無損傷保証には
使いません。これは任意誤配線を許容する設計ではありません。

## 誤接続と故障モード

| 事象 | 回路上の結果 | 判定 |
| --- | --- | --- |
| 正常な抜線 | 右18キーの経路が開く。中央電源の切断はない | 電気的ストレスは小さい見込み。誤キー/押下残りはIssue #10/#11で検証 |
| 1信号–GND | MCU側470 Ωを通る。仮定モデル6.666 mA | 電流低減のみ。MCU無損傷を未証明 |
| 2信号の逆レベル競合 | 470 Ωを2本通るため仮定上約3.4 mA | 任意の同時競合とfirmware faultは未証明 |
| 10/100 crossover | `R_R1`がGND、`R_R0`と`R_C1`が入れ替わる | 禁止。キー誤検出とGPIO故障状態になる |
| 非PoE LAN port | 独自DC matrixをEthernet PHYへ接続する | 禁止。キーボードとネットワーク機器の安全を保証しない |
| IEEE PoE PSE | 適合PSEは有効な約25 kΩ signatureを検出してから給電する | その検出を保護機能として信用しない。接続禁止 |
| 24 V passive PoE | detectionなしでpin 4/5、7/8へ24 Vが来る製品が存在する | 470 Ωに最大約1.23 W相当。破損/発熱のおそれ、絶対禁止 |
| 48 V相当誤給電 | 470 Ωへ48 Vが掛かる仮定 | 約4.90 W相当。抵抗/TVSでは保護不能、絶対禁止 |
| IEC ESD | TVSがGNDへ電流を逃がす | 部品定格のみ。完成基板のIEC試験と機能確認が必要 |

[Ethernet Allianceの802.3bt解説](https://ethernetalliance.org/wp-content/uploads/2018/04/WP_EA_Overview8023bt_FINAL.pdf)
は、PSEが複数点で有効な25 kΩ付近のsignatureを検出してから給電する仕組みを説明しています。
しかし、[Ubiquitiの24 V passive PoE仕様](https://dl.ui.com/qsg/EP-24V-72W/EP-24V-72W_EN.html)のように、
pin 4/5を正、7/8を負として24 Vを出す実装も存在します。本回路ではpin 8がGNDであり、
470 Ωと低電圧TVSはPoE保護部品ではありません。

PoEやLANの誤接続は実機で破壊試験しません。ケースと基板へ警告し、専用色の短いストレートケーブルを
キーボードと一緒に保管します。PoE環境で取り違えを管理できない場合は、8P8Cではなく物理的に非互換な
ロック付き多極コネクタへ変更します。

## 検査方法

```bash
make check-safety-schematic
make validate-hardware
```

`check-safety-schematic`はKiCad 10でXML netlistを出力し、次を確認します。

- 36 switch、36 diodeとレイアウトJSONのキーIDが1対1
- Bank A/BのA/K向きと6本のmatrix net
- J1/J2 pin 1/8がGND、pin 2–7が指定信号
- 中央ピンに禁止電源netがない
- `ERJ3EKF4700V`が6個、各信号とMCUの間にある
- `TPD4E05U06DQA`が左右各2個、全信号とGNDへ接続される
- `1N4148W-7-F`が36個
- negative testが中央VBUS混入と220 Ωへの変更を拒否する

KiCad ERCの0 violation、構造検査、ngspiceは別の証拠です。完成のためにはIssue #10のQMK走査、
PCB DRC、無通電導通、電流制限付き電源、オシロスコープ、Issue #11の100回挿抜が残ります。
PCのUSBポート、LANスイッチ、PoE機器を故障注入には使いません。
