# 2 × 2 breadboardでJapanese duplex matrixを試す

確認日: 2026-08-01

## 目的と限界

完成PCBを発注する前に、RP2040-Zero、8個のスイッチ、8本のダイオード、4本の470 Ω抵抗で、Japanese duplexの双方向走査を確認します。

この試験で確認できるのは、ダイオード向き、matrix座標、QMK入力、同時押し、phantom抑制、右側相当信号の抜線と復帰です。breadboardの接触、長さ、寄生成分は完成PCBや2 mケーブルと異なります。ESD、PoE誤接続、コネクタ寿命、100回活線挿抜、完成基板の安全性には合格したことになりません。

## 用意するもの

| 数量 | 部品 | 備考 |
| ---: | --- | --- |
| 1 | Waveshare RP2040-Zero | headerを確実にはんだ付けしたもの |
| 1–2 | solderless breadboard | 電源railの途中切れを導通確認 |
| 8 | momentary switch | tactile switchでよい。Chocの機械評価ではない |
| 8 | 1N4148 axial diode | 帯がcathode（K）。最終SMD部品との差を記録 |
| 4 | 470 Ω、1%抵抗 | 各GPIOとmatrix busの間に1本 |
| 適量 | jumper wire | 色をR0/R1/C0/C1で固定する |
| 1 | digital multimeter | 導通、抵抗、diode mode、3V3確認 |
| 1 | current-limited 5 V supply | 初回通電用。USBと同時接続しない |
| 1 | 保護したUSB hubまたはUSB current limiter | HID確認用。故障注入には使わない |
| 任意 | 2 channel以上のoscilloscope | probe groundはMCU GNDだけへ接続 |

RP2040-ZeroはVUSB/VSYSが直結されているため、外部5 VとUSBを同時に接続しません。Waveshare公式はUSBを使わない場合に5 V pinから給電できるとしています。逆流対策なしの電池接続とは別の話です。

## 回路

まず左half相当として次の4線だけを使います。未使用のGP2/GP5と右halfのGP6–GP11は配線しません。

| bus | MCU pin | 配線 |
| --- | --- | --- |
| R0 | GP0 | GP0 → 470 Ω → R0 bus |
| R1 | GP1 | GP1 → 470 Ω → R1 bus |
| C0 | GP3 | GP3 → 470 Ω → C0 bus |
| C1 | GP4 | GP4 → 470 Ω → C1 bus |

470 Ωはスイッチごとではなく、MCUから出る信号線ごとに置きます。breadboard上のmatrix側へVCC、5V、3V3、RAW、GNDを接続しません。スイッチとダイオードは4本の信号busの間だけに入ります。

```text
Bank A（4 keys、row → column）

R0 ── SW-A00 ──|>|── C0       R0 ── SW-A01 ──|>|── C1
R1 ── SW-A10 ──|>|── C0       R1 ── SW-A11 ──|>|── C1

Bank B（4 keys、column → row）

C0 ── SW-B00 ──|>|── R0       C1 ── SW-B01 ──|>|── R0
C0 ── SW-B10 ──|>|── R1       C1 ── SW-B11 ──|>|── R1

|>| の左がanode（A）、帯のある右がcathode（K）
```

Bank AとBank Bで向きが逆です。物理的には同じR/C交点に2キーずつ存在しますが、ダイオード方向で別のlogical keyとして読みます。1本ずつ組み、diode modeでA→Kだけが導通することを確認してから次へ進みます。

## 左halfで期待する入力

v0.3.1のdefault keymapでは次になります。

| key | 物理経路 | matrix | HID |
| --- | --- | --- | --- |
| A00 | R0 → C0 | `[0,0]` | `Q` |
| A01 | R0 → C1 | `[0,1]` | `W` |
| A10 | R1 → C0 | `[1,0]` | `A` |
| A11 | R1 → C1 | `[1,1]` | `S` |
| B00 | C0 → R0 | `[0,3]` | `R` |
| B01 | C1 → R0 | `[1,3]` | `F` |
| B10 | C0 → R1 | `[0,4]` | `T` |
| B11 | C1 → R1 | `[1,4]` | `G` |

キー名の2桁は物理`row,column`です。Bank Bのlogical matrixはtransposeされるため、物理座標とmatrix座標を混同しません。

## 手順0: 通電前

1. RP2040、USB、外部電源をすべて外す。
2. breadboardの電源railが途中で分割されていないか確認する。ただしmatrixへ電源rail自体は使わない。
3. GP0/GP1/GP3/GP4から各busまで約470 Ωであることを測る。
4. 全スイッチを離した状態で、R0/R1/C0/C1間が短絡していないことを確認する。
5. 各スイッチを押したままdiode modeでA→Kの順方向電圧を記録し、逆方向がopenになることを確認する。
6. 隣接列を1列ずつずらしたtactile switchの足を取り違えていないか導通で確認する。

短絡、0 Ωに近いseries経路、逆向きdiodeが1件でもあれば通電しません。

## 手順1: 電流制限付き初回通電

1. USBを接続せず、安定化5 VをRP2040-Zeroの5 V pinとGNDへ接続する。
2. 電流上限は無押下で起動を確認できる低い値から始め、board単体の実測値を記録して必要分だけ上げる。推測値を合格基準にしない。
3. 5 Vと3V3を測り、発熱、臭い、電圧低下、current-limit動作がないことを確認する。
4. 電源を切り、5 Vが十分低下してから配線へ触れる。

この段階ではHIDを確認しません。電源が不安定ならUSBへ移行しません。

## 手順2: UF2とsingle-key

1. 外部5 Vを完全に外す。
2. v0.3.1のUF2 SHA-256が`266826a48637016e0db4767345872961118c4c5274de118b6d745da2dc2af631`であることを確認する。
3. BOOTSELでUF2を書き込み、一度USBを外す。
4. 配線を再点検し、保護したUSB hubまたはUSB current limiter経由で接続する。
5. Linux/Waylandでは`wev`などのevent viewerを使い、通常アプリへ文字を送らない。
6. 8キーを1個ずつ押して離し、上表のkey-down/key-upが1組だけ出ることを確認する。

押していないキー、連打、key-up不足が出たら停止し、電源を外してdiode向き、switch pin、jumper接触を確認します。

## 手順3: 同時押しとghost filter

8キーの2キー組合せは`8 choose 2 = 28`通りです。各組合せで、2つのkey-downと2つのkey-upだけが出ることを記録します。

次の3-key pathは意図的に曖昧になります。

| path | 押す順 | 期待する保守動作 |
| --- | --- | --- |
| row → column | A00、B10、最後にA11 | 最後のA11とphantom A01を出さず、先の2キーを維持 |
| column → row | B00、A01、最後にB11 | 最後のB11とphantom B10を出さず、先の2キーを維持 |

最後のキーを離した後は通常の2キー状態へ戻ります。同じrectangleの4キーを本当に押した場合もraw scanだけでは区別できないため、追加キーを一時保留するのが現行firmwareの仕様です。

## 手順4: 右half相当の抜線

1. 電源を外す。
2. 同じ4本の抵抗と2 × 2 moduleを、R0=GP6、R1=GP7、C0=GP9、C1=GP10へ移す。
3. 無通電検査を繰り返してからUSB接続する。
4. single-keyと28通りの2-keyを再確認する。
5. 1キーを押した状態で、4信号をまとめて切れる4極headerを通常の向きに抜く。信号だけを切り、電源やGNDを故意に擦らせない。
6. key-upが出て押下残りがないこと、USB再列挙やMCU resetがないことを確認する。
7. 再接続後、resetなしで全8キーが戻ることを確認する。

右halfのdefault keyは、A00/A01/A10/A11が`Backspace/Y/Enter/H`、B00/B01/B10/B11が`I/K/O/L`です。event viewerを使い、編集中の文書で試さないでください。

抜線の耐久、8P8C接点順序、ESD、2 m cableはIssue #11です。このbreadboard手順では、斜め挿し、短絡、PoE/Ethernet接続を試しません。

## 手順5: 波形（任意）

- probe groundはRP2040-ZeroのGNDへ1点接続する。
- R0/R1/C0/C1は470 Ωのmatrix側で観測する。
- 無押下HIGH、押下LOW、方向切替時に複数pinが同時outputにならないことを確認する。
- firmwareのsettlingは1 µsなので、sample前に信号が安定しているか記録する。
- 長いprobe ground leadのringingを回路のovershootと誤認しない。

オシロスコープのearth接地を、浮いていない別電源や信号線へ接続しません。測定器の接地方式が不明なら波形試験を省略します。

## 記録

Issue #10へ次を添付またはcommitします。

| 項目 | 必須記録 |
| --- | --- |
| design / firmware | main commit、release、UF2 SHA-256 |
| MCU | 製品名、revision、購入元、写真 |
| parts | diode/resistor/switchの型番またはlot |
| power | supply/hub、current limit、無押下電流、5 V、3V3 |
| wiring | 配線図と全体写真、diode帯が読める写真 |
| singles | 左8、右8のdown/up結果 |
| pairs | 左28、右28の結果 |
| ghost | 2方向の押下順、実際のevent、4-key制限 |
| disconnect | 押下中抜線、key-up、再列挙/reset、再接続 |
| waveform | probe位置、time/div、voltage/div、capture。未実施なら理由 |
| anomalies | 再現手順、期待、実際、停止判断、新規Issue |

結果が合わない場合、filterを外して「実機ではghostしなかった」と推測で進めません。配線、event log、波形を保存し、最小再現を新しいIssueへ分離します。

## 一次資料

- [Waveshare RP2040-Zero wiki](https://www.waveshare.com/wiki/RP2040-Zero)
- [Raspberry Pi: RP2040 documentation](https://www.raspberrypi.com/documentation/microcontrollers/microcontroller-chips.html#rp2040)
- [Hardware design with RP2040](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf)
- [QMK RP2040 platform](https://docs.qmk.fm/platformdev_rp2040)
