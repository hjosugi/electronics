# 分割キーボードのホットプラグ安全設計とOSSシミュレーション

> NotebookLM用統合資料。生成元は本リポジトリのdocsディレクトリです。
> 内容確認日: 2026-08-01。製造前にリンク先の最新版と採用部品を再確認してください。

## この統合資料について

このファイルは検索と質問応答をしやすくするため、設計判断、回路、シミュレーション、実機検証、出典を順番に結合しています。編集は生成元の各文書へ行い、make notebooklmで再生成してください。


---

## 要件、結論、安全性の境界

## この資料が扱う要件

想定するのは、36キーまたは42キー程度の左右分割キーボードです。

- PCとのUSB接続は左側だけに固定する
- MCUはRP2040系を候補とする
- 右側にはRGB、OLED、トラックボールなどの電源を必要とする機能を載せない
- キーボードの電源が入ったままでも、中央ケーブルを抜き差ししたい
- 設計と検証には無料のOSSを使いたい

右側に電源を必要とする部品を追加する場合、この前提は崩れます。その場合は「パッシブ右手」ではなく、左右にMCUと電源を持つ一般的な分割構成として、電源スイッチ、逆流、ESD、左右通信を別途設計します。

## 推奨アーキテクチャ

```text
PC
 │ USB
 ▼
┌──────────────────────── 左側 ────────────────────────┐
│ RP2040 ─ キーマトリクス                              │
│    │                                                 │
│    └─ 470 Ω × 6本または7本 ─ 8P8Cコネクタ           │
└──────────────────────────┬───────────────────────────┘
                           │ ストレートケーブル
                           │ GND + マトリクス線のみ
                           │ 電源線なし
┌──────────────────────────┴───────────────────────────┐
│ 8P8Cコネクタ ─ ダイオード + キースイッチ             │
│                         右側にMCU・電源なし           │
└──────────────────────── 右側 ────────────────────────┘
```

右側を外すと、右側のキースイッチへ至る導通がなくなるだけです。右側の電源電圧が落ちる過渡現象や、左右MCU間通信の切断処理は存在しません。

## なぜTRRSを推奨しないのか

一般的な2 MCU分割キーボードでは、TRRSにGND、VCC、通信線を割り当てます。TRRSプラグは挿抜時に複数の接点を順番に擦って通過するため、定常時には離れているVCCとGNDが一時的に接触し得ます。

[QMK Split Keyboard公式資料](https://docs.qmk.fm/features/split_keyboard)は、VCCを運ぶTRRS接続について次の趣旨を明記しています。

- ホットプラグには対応しない
- TRRSを挿抜する前にUSBを外す
- そうしないとコントローラを短絡、破損させる可能性がある

したがって、電源ONのまま挿抜することが要件なら、操作上の注意だけに依存せず、中央ケーブルから電源線をなくす方が単純です。

## 「ホットプラグ安全」の範囲

本資料でいう「ホットプラグに向く」は、主に次の意味です。

- 中央ケーブル内にVCCとGNDの短絡組み合わせがない
- 右側切断時に、給電中の右側回路や通信MCUが突然電源断しない
- 外部GPIOに直列抵抗を入れ、短時間の競合電流を制限する

次の意味ではありません。

- IEC 61000-4-2のESD試験に合格済み
- すべての誤配線や破損ケーブルに耐える
- LAN機器へ誤接続しても安全
- 任意の長さ、品質のケーブルで誤入力が起きない
- 無制限の挿抜回数を保証する

公開資料では、この境界を曖昧にせず、「危険経路の除去」「電流の制限」「最終的な実機確認」を別の検証項目として扱います。

## 方式比較

| 方式 | 右側電源 | MCU数 | 中央ケーブルの電源短絡 | 右側の機能 | 初号機への推奨 |
| --- | ---: | ---: | --- | --- | --- |
| TRRS + VCC + serial | あり | 2 | 挿抜中にあり得る | 多い | 非推奨 |
| 8P8C + パッシブ行列 | なし | 1 | 経路自体がない | キーと受動部品のみ | 推奨 |
| USB-C + 独自serial + VBUS | あり | 2 | 保護設計が必要 | RGB/OLED等も可能 | 上級者向け |
| 左右無線 | 各側に電池 | 2 | 中央ケーブルなし | 構成次第 | 別要件として有効 |

## ここからの設計順序

1. 36キーか42キーかを決める。
2. Japanese duplex matrixの行数と列数を決める。
3. 実コネクタのピン番号をデータシートで確定する。
4. MCU側の全外部線へ直列抵抗を配置する。
5. 回路図上で中央ケーブルに電源ネットがないことを確認する。
6. SPICEで故障ケースの電流を比較する。
7. KiCadのERC/DRCと、無通電の導通試験を行う。
8. 電流を監視できる環境で実機試験する。


---

## 1 MCU + パッシブ右手 + 8P8Cの設計

## 8P8CとRJ45という呼び方

一般に「RJ45」と呼ばれる8接点のモジュラーコネクタを使います。厳密には、コネクタ形状は8P8Cであり、RJ45は配線を含む登録ジャック規格名です。本資料では検索性のため「8P8C、通称RJ45」と表記します。

Ethernet用のマグネティクス内蔵ジャックではなく、8接点がそのまま基板へ出るモジュラージャックを選びます。採用部品の機械図、接点番号、シールド端子、内蔵LEDや内蔵抵抗の有無をデータシートで確認してください。

## Japanese duplex matrix

Japanese duplex matrixは、同じ行・列の組に、ダイオード方向が反対の2キーを割り当てる方式です。理論上、`行数 × 列数 × 2` 個のキーを `行数 + 列数` 本の信号で扱えます。

| 片側キー数 | 行 × 列 | 理論上の最大キー数 | 必要な信号線 |
| ---: | ---: | ---: | ---: |
| 18 | 3 × 3 | 18 | 6 |
| 21 | 4 × 3 | 24 | 7 |

42キーでは片側21キーなので、4 × 3の24枠のうち3枠を未使用にします。これはキーレイアウト上の割り当てであり、余った枠を物理キーへ接続する必要はありません。

ダイオード方向を使い分けるため、通常の一方向マトリクスとは走査方法が異なります。QMKで採用する場合は、Cheapinoなどの実装を参考にしつつ、対象キーボード専用のcustom matrix処理とテストが必要です。単に`MATRIX_ROWS`と`MATRIX_COLS`を設定するだけで完成するとは限りません。

## 提案ピン割り当て

次は、この教材で使用する論理ピン割り当てです。実部品の端子番号は、必ずジャックのデータシートと導通試験で照合します。

### 36キー、片側18キー

| 8P8C接点 | 信号 | 用途 |
| ---: | --- | --- |
| 1 | GND | ESD保護の基準、信号走査には本質的に不要 |
| 2 | NC | 将来予約。両側で未接続 |
| 3 | R_COL_0 | 右側Japanese duplex列0 |
| 4 | R_COL_1 | 右側Japanese duplex列1 |
| 5 | R_COL_2 | 右側Japanese duplex列2 |
| 6 | R_ROW_0 | 右側Japanese duplex行0 |
| 7 | R_ROW_1 | 右側Japanese duplex行1 |
| 8 | R_ROW_2 | 右側Japanese duplex行2 |

### 42キー、片側21キー

| 8P8C接点 | 信号 | 用途 |
| ---: | --- | --- |
| 1 | GND | ESD保護の基準 |
| 2 | R_ROW_3 | 右側Japanese duplex行3 |
| 3 | R_COL_0 | 右側Japanese duplex列0 |
| 4 | R_COL_1 | 右側Japanese duplex列1 |
| 5 | R_COL_2 | 右側Japanese duplex列2 |
| 6 | R_ROW_0 | 右側Japanese duplex行0 |
| 7 | R_ROW_1 | 右側Japanese duplex行1 |
| 8 | R_ROW_2 | 右側Japanese duplex行2 |

36キーと42キーで同じPCBを共用したい場合、接点2だけを未実装または`R_ROW_3`として扱えます。信号名、コネクタ番号、ケーブル側の接点番号をシルクと回路図の両方へ記載してください。

## GND線の意味

右側がスイッチとダイオードだけなら、キー電流は行線から列線へ戻るため、GNDはキーマトリクス走査そのものには必要ありません。それでも1本をGNDへ割り当てる理由は次の通りです。

- コネクタ付近のTVSアレイに短い帰路を与える
- ケーブルや筐体の静電気をMCUの信号ピン以外へ逃がす設計余地を残す
- 将来のシールド接続を検討しやすくする

GNDを設けただけでESD対策が完了するわけではありません。TVSの配置とGNDへの経路インダクタンスが重要です。右側へTVSを置く場合も電源は不要ですが、漏れ電流、接合容量、スタンドオフ電圧を確認します。

## 直列抵抗

MCUのGPIOと8P8Cコネクタの間に、各信号1本ずつ直列抵抗を入れます。

```text
RP2040 GPIO ── 470 Ω ── 8P8C ── ケーブル ── 右側スイッチ行列
```

初号機の採用値は470 Ωです。3.3 Vが理想的にGNDへ短絡した単純計算では、抵抗だけで制限される電流は次の値です。

| 直列抵抗 | `3.3 V / R` | 備考 |
| ---: | ---: | --- |
| 220 Ω | 15.0 mA | MCUによっては大きい。無条件には推奨しない |
| 330 Ω | 10.0 mA | 比較候補 |
| 470 Ω | 7.0 mA | 採用。信号立上りと入力閾値はngspiceと実機で確認する |

実際にはGPIO出力抵抗、ケーブル抵抗、接点抵抗も直列に入ります。一方、MCUの許容値は「設定できるドライブ強度」「通常動作条件」「絶対最大定格」「全GPIO合計」で意味が異なります。上表だけで安全判定せず、採用MCUと実装ボードのデータシートに照らします。

Japanese duplexで2本のGPIOが逆レベルを駆動して競合した場合、電流経路には原則として両側の直列抵抗が入ります。470 Ωを2本通る理想計算なら約3.5 mA以下になります。ただし、基板上の短絡が抵抗よりMCU側で起きた場合は保護されないため、抵抗はコネクタの近くではなく、信号源であるMCUと外部配線の間に確実に置きます。

## TVSアレイ

TVSはオプションですが、手で頻繁に触る外部コネクタでは配置用フットプリントを確保する価値があります。

- 3.3 V信号に適したスタンドオフ電圧
- キーマトリクスの立上りを壊さない接合容量
- MCUの入力クランプより先にサージ電流を逃がせるクランプ特性
- コネクタ直後に置き、TVSからGNDへの配線を短く太くする

たとえば[TI TPD2EUSB30A](https://www.ti.com/product/TPD2EUSB30A)は2チャネル、3.6 Vの`VRWM`、代表0.7 pFの製品ですが、これは選定例でありBOM確定ではありません。必要チャネル数、パッケージ、実装能力、クランプ電圧を含めて比較してください。

## ケーブルと誤接続対策

- 市販の8P8Cストレート結線パッチケーブルを使う
- クロスケーブル、電話線、片側だけ配列が違う自作ケーブルを混ぜない
- 初回接続前に1-1、2-2、…、8-8の導通をテスターで確認する
- 基板とケースに`SPLIT ONLY / NO LAN / NO PoE`と明記する
- Ethernetスイッチ、ルーター、PoEインジェクターへ接続しない
- LANケーブルと見分けられる短い色やラベルを専用品として固定する

8P8Cを採用する最大の注意点は、Ethernetに見えることです。パッシブ右側へ電源を送らない設計でも、PoE機器や故障した配線への誤接続を安全にする保証はありません。利用者が迷わない外観と表示は回路の一部として扱います。

## 回路図レビューで確認すること

- `VBUS`、`5V`、`3V3`、`RAW`のネットが中央コネクタに接続されていない
- すべての外部マトリクス線が直列抵抗を通る
- コネクタのシールド端子と信号GNDの扱いが意図どおり
- TVSの向き、GND帰路、スタンドオフ電圧が正しい
- 左右コネクタのミラー配置でピン番号が逆転していない
- NC接点に銅箔やテストパッドから意図しない接続がない
- ERCで電源警告を無理に非表示にしていない


---

## TRRSとUSB-C案の評価

## TRRS + VCC + 通信線

### 長所

- 小型で、分割キーボードの作例が多い
- GND、VCC、通信1～2本を少ない部品で接続できる
- 2 MCU構成ならQMKの一般的なsplit transportを利用しやすい

### この要件での問題

TRRSプラグはTip、Ring、Sleeveの接点を奥へ滑らせて挿入します。定常接続時のピン割り当てが正しくても、挿抜途中の接触順序は別問題です。VCCを含む限り、電源とGNDまたは信号線が一時的に接触する可能性があります。

このため[QMK公式](https://docs.qmk.fm/features/split_keyboard)はUSBを外してからTRRSを抜き差しするよう明記しています。「ゆっくり抜けばよい」「データ線へ抵抗を入れたからよい」では、VCCとGNDの短絡経路は消えません。

結論として、電源ONのまま中央ケーブルを抜き差しする要件には採用しません。電源OFFでのみ挿抜する通常の2 MCU分割なら、別の設計として成立します。

## 8P8C + パッシブ行列

### 長所

- 中央ケーブルに電源を流さないため、VCC-GND短絡経路を除去できる
- 右側にMCU、レギュレータ、発振、左右通信が不要
- 抜線時の状態が「右側キーが開放される」に単純化される
- 8接点あり、片側21キーの4 × 3 Japanese duplexにも足りる
- 安価でラッチがあり、ストレートケーブルを入手しやすい

### 注意点

- Ethernetと誤認されやすい
- 接点バウンスとESDは残る
- ケーブルが長いほど容量、アンテナ効果、クロストークが増える
- Japanese duplex用のファームウェア走査が必要
- 右側にRGB、OLED、アクティブセンサーを置けない

この資料の要件では、欠点を管理しやすく、最も推奨できます。

## USB-C + 独自通信 + VBUS

### これはUSBではない

USB-CコネクタのD+、D-へ独自のUART相当信号を割り当てても、USBプロトコルにはなりません。普通のUSB機器に見えるコネクタを非USB用途に使うと、利用者はPC、充電器、別のキーボードへ接続できると誤解します。

QMK公式も、左右間にUSBケーブルを使う方式について、通常のUSB接続と誤認されると短絡し得るため推奨しないと説明しています。さらに2026年4月公開の[USB Type-C Cable and Connector Specification Release 2.5](https://usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-25)には、Type-Cコネクタの第三者機能への利用条件が記載されています。独自配線をUSB準拠製品として表示してはいけません。

### それでも検討する場合のブロック

右側にMCU、RGB、OLEDなどが必要で、固定マスターのUSB-C接続を研究するなら、少なくとも次の機能を分けて設計します。

```text
左側5 V
  │
  ├─ Type-C CC attach/orientation/role detection
  │        │ valid attach
  │        ▼
  └─ current-limited power-distribution switch ─ VBUS ─ 右側5 V

左TX ─ series R ─ D+ ─────────────────────────── 右RX
左RX ─ series R ─ D- ─────────────────────────── 右TX
GND  ─────────────────────────────────────────── GND
```

固定マスターなら、左はSource/DFP、右はSink/UFPとしてCCを正しく終端します。右側のCC1とCC2へ単純に5.1 kΩを置くだけでなく、左側で接続を検出し、有効な接続後にだけVBUSスイッチを有効化する必要があります。コントローラICのリファレンス回路、USB-Cレセプタクルの向き、ケーブル種別を含めてレビューします。

### 部品例の正しい読み方

| 部品 | 役割 | 誤解してはいけない点 |
| --- | --- | --- |
| [TUSB320](https://www.ti.com/product/TUSB320) | CC接続、向き、役割、電流モードの検出 | VBUSの大電流を直接開閉するパワースイッチではない |
| [TPS2553](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf) | 調整可能な電流制限付き配電スイッチ | 理想ダイオードではない。逆電圧検出にはデータシート上、代表4 msの遅延がある |
| [TPD2EUSB30A](https://www.ti.com/product/TPD2EUSB30A) | 2線の低容量ESD保護 | 電流制限や誤配線防止の代わりにはならない |

元の案にある「TPS2553で逆流阻止」という短い説明だけでは不足します。データシートは、出力が入力を代表135 mV上回った状態を代表4 ms検出してMOSFETをオフにする動作を示しています。その間の逆電流や、無給電時の各ピンのバックパワーも含めて確認が必要です。

### RP2040の左右通信

[QMKのRP2040資料](https://docs.qmk.fm/platformdev_rp2040)と[serial driver資料](https://docs.qmk.fm/drivers/serial)によれば、RP2040はQMK split keyboardのhalf-duplexとfull-duplexをサポートし、PIO実装では任意GPIOをTX/RXにできます。2線full-duplexを使うこと自体は可能です。

しかし、ファームウェア対応は電気的なホットプラグ安全性を保証しません。通信ドライバ、CC制御、VBUSスイッチ、ESD、左右の電源順序は別の設計問題です。

## 左右どちらでもPC接続可能にする場合

左右どちらをPCへつないでも動く構成は、固定マスターより大幅に複雑です。

- 両側がSourceにもSinkにもなり得るDRP制御
- どちらの5 Vを採用するか決める電源MUX
- 同時接続時の逆流防止
- USBデータ経路の切替
- 左右役割の決定とファームウェア同期
- 異なるPCへ左右を同時接続した故障ケース

初号機では扱いません。左右挿し替えが必須なら、既存の検証済み設計や専用電源MUX/Type-C PDコントローラのリファレンス設計を基礎に、独立したプロジェクトとして設計してください。

## 無線という別解

中央ケーブル自体をなくせば、中央コネクタのホットプラグ問題もなくなります。Caravelle-BLEのような左右独立電源の作例や、nRF52840 + ZMKはこの方向です。

ただし、問題は次へ移ります。

- Li-Poまたは一次電池の安全な取り扱い
- 充電回路、保護回路、電源スイッチ
- 左右の無線同期と消費電力
- 電池寿命、輸送、廃棄

有線パッシブ方式の代替ではありますが、最初の回路として必ず簡単とは限りません。


---

## OSS回路シミュレーション手順

## ツールの使い分け

| 目的 | ツール | 特徴 |
| --- | --- | --- |
| 電流とスイッチ動作を直感的に見る | [CircuitJS1](https://github.com/pfalstad/circuitjs1) | ブラウザで動くGPLの回路シミュレータ |
| 回路図、PCB、SPICEを同じ設計で扱う | [KiCad 10](https://docs.kicad.org/10.0/ja/eeschema/eeschema.html) + ngspice | 本番設計の中心 |
| SPICE実験をGUIで繰り返す | [Qucs-S](https://ra3xdh.github.io/) + ngspice | 複数のOSSシミュレーションバックエンドを使える |
| ネットリストを自動実行する | [ngspice](https://ngspice.sourceforge.io/) | 本リポジトリの再現テストに使用 |
| QMKのロジックを検証する | [QMK Unit Testing](https://docs.qmk.fm/unit_testing) | 回路電流ではなくC/C++ロジックを検証 |

回路シミュレーションとファームウェアテストは代替関係ではありません。次の3層で分けます。

1. 電気的な故障経路: SPICE
2. Japanese duplex走査とキー状態: QMK Unit Testing
3. 寄生要素、コネクタ、実MCU: 実機

## 最初に立てる問い

キーボード全体を一度に再現しようとせず、故障モードごとに小さな回路を作ります。

- VCCとGNDが50 µs触れたら、電源電流はどの経路を流れるか
- GPIOがGNDへ触れたら、220/330/470 Ωでどこまで電流を下げられるか
- コネクタ接点が100 µs単位でバウンスしたら、入力波形はどうなるか
- 右側を抜いたとき、給電された容量性負荷が残るか
- シミュレーションへ入れていない保護機能は何か

最後の問いが重要です。簡略モデルに存在しないUSBホストの電流制限を、グラフから推測してはいけません。

## CircuitJS1で原理を見る

### TRRS相当の瞬間短絡

次を配置します。

```text
5 V電源 ─ 0.3 Ω ─ 電流計 ─ VCC接点
                              │
                         一時接触スイッチ
                              │
                             GND
```

0.3 Ωは電源、ケーブル、配線を合わせた仮の抵抗です。実測値ではありません。スイッチを短時間オンにし、電源電流が大きくなることを確認します。次に、中央ケーブルからVCC線を丸ごと削除します。保護抵抗の値を調整するのではなく、短絡ループ自体がなくなる差を見ます。

### GPIO直列抵抗

```text
3.3 V ─ GPIO出力抵抗相当25 Ω ─ 候補抵抗 ─ switch ─ GND
```

直列抵抗を0、100、220、330、470 Ωへ変えます。電流の桁を比較してください。GPIO出力段の25 Ωも教育用仮定で、RP2040の保証値ではありません。

CircuitJS1は概念確認に優れますが、採用予定のICが提供するSPICEモデルやIBISモデルを正確に置き換えるものではありません。

## 付属ngspiceモデルを実行する

### 必要なもの

```bash
ngspice --version
make simulate
```

個別に実行する場合は次の通りです。

```bash
ngspice -b spice/trrs-vcc-short.cir
ngspice -b spice/gpio-series-resistors.cir
ngspice -b spice/passive-connector-bounce.cir
```

バッチ実行では、各ネットリストに書かれた`.meas`の結果が標準出力へ表示されます。終了コードが0でも、測定値が設計目標内かは人が判断します。

## KiCad 10 + ngspiceで再現する

[KiCad 10回路図エディタの公式マニュアル](https://docs.kicad.org/10.0/ja/eeschema/eeschema.html#simulator)によると、KiCadの統合シミュレータはngspiceをエンジンとして使用し、過渡解析やIBISモデルを扱えます。

### 回路図を作る

1. 新規KiCadプロジェクトを作る。
2. `Simulation_SPICE`ライブラリから電圧源、PULSE源、スイッチを置く。
3. 抵抗、コンデンサ、GNDを置く。
4. 電圧制御スイッチへ`SW`モデルを割り当てる。
5. `VBUS_RIGHT`、`GPIO_EXT`など、観測するネットへラベルを付ける。
6. コネクタ記号そのものが解析に不要なら、スイッチと寄生R/Cで置き換える。

SPICEでは基準ノード0、すなわちGNDが必要です。GNDがない回路は行列が特異になり、解析できません。

### 過渡解析を設定する

短絡時間が50 µsなら、それより十分小さい最大ステップを使います。

| 設定 | 初期値の例 |
| --- | --- |
| Analysis | Transient |
| Time step | 100 ns～1 µs |
| Final time | 20 ms |
| Max time step | 100 ns～1 µs |
| Initial time | 0 |

大きすぎるタイムステップでは、50 µsの短絡を数点しか計算せず、ピークや立上りを見落とします。一方で小さくしすぎると計算時間が増えます。最大ステップを半分にして結果が大きく変わらないことを確認します。

### 観測する波形

- `V(VBUS_RIGHT)`: 右側電源を持つ方式の電圧
- `I(VUSB)`: USB電源モデルから流れる電流
- `V(GPIO_EXT)`: 直列抵抗より外側のGPIO線
- `I(RSERIES)`: 外部故障時の抵抗電流
- `V(CONTACT_CTL)`: コネクタ接触状態を作る制御波形

### 4つの故障ケース

#### A. 通常の取り外し

信号、電源、GNDが時間差で切れるモデルを作ります。実コネクタの接触順序をデータシートや実測で得られない場合、順番を入れ替えた複数ケースを解析します。

#### B. VCC-GNDの瞬間短絡

10.050 msから10.100 msまで50 µsだけスイッチをオンにします。短絡時間を10 µs、50 µs、1 msへ変え、電源モデルの感度を確認します。

#### C. GPIO-GNDの接触

0、100、220、330、470 Ωを比較します。最大電流だけでなく、GPIOのHigh電圧が受信側の閾値を満たすかも確認します。

#### D. 接点バウンス

100 µs ON、100 µs OFF、50 µs ON、50 µs OFFのようなPWL制御を使います。ファームウェアのデバウンスで吸収できる時間スケールでも、電気的な競合電流は別に確認します。

## 実部品モデルへ進む

抵抗、理想スイッチ、理想電源で傾向を掴んだあと、必要に応じて次を追加します。

- MCUのIBIS出力/入力モデル
- ケーブルの直列R、Lと線間/対地C
- TVSメーカーのSPICEモデル
- 電源スイッチメーカーの暗号化されていない対応モデル
- コネクタ接点抵抗の最小、代表、最大
- 右側のデカップリング容量とESR

メーカーのモデルがngspice互換とは限りません。収束させるためにモデルを改変した場合、元モデルとの差と変更理由を記録します。

## Qucs-Sを使う場合

[Qucs-S公式](https://ra3xdh.github.io/)は、ngspiceを含む外部シミュレーションカーネルをGUIから利用します。多数の抵抗値やスイッチ時刻を変えながらグラフを比較したい場合に便利です。

本資料の`.cir`をそのまま基準にし、Qucs-Sで描き直した回路のノード名と値を一致させます。GUI上で結果が出ても、エクスポートされたSPICEネットリストを確認し、意図したモデルが実行されていることを確かめます。

## RP2040全体をSPICEで再現しない理由

SPICEはアナログ電気特性を扱う道具で、RP2040のCPU、USB、PIO、QMKを丸ごと実行するエミュレータではありません。反対に、ファームウェアエミュレータはコネクタ短絡電流やTVSクランプを再現しません。

そのため、完全な一体シミュレーションを目標にせず、次の証拠を組み合わせます。

- SPICE: 電流、電圧、時定数
- QMKテスト: キーマトリクス状態、デバウンス、抜線時のキー解放
- オシロスコープ/電流計: 実波形
- ERC/DRC/導通試験: 配線の正しさ


---

## 付属ngspice回路の解説

## 共通の考え方

5つのネットリストは、実製品を完全再現するものではありません。比較したい危険経路だけを小さく切り出しています。

モデル値には次の仮定を使います。

| 要素 | 仮定 | 理由 |
| --- | ---: | --- |
| 電源 | 5 V | USB VBUSの公称値を簡略化 |
| 電源・配線抵抗 | 0.30 Ω | 理想電源による無限大電流を避ける教育用仮定 |
| GPIO電源 | 3.3 V | RP2040系GPIOを想定 |
| GPIO出力抵抗 | 25 Ω | 比較用の仮定。保証値ではない |
| 外部直列抵抗 | 100～470 Ω | 候補値の差を見る |
| スイッチON抵抗 | 0.05 Ω | 接点を有限抵抗として扱う |
| ケーブル容量 | 300 pF | 短いケーブルの影響を見る仮定 |

絶対値を採用判断へ使う前に、実測またはデータシートの最小・代表・最大へ置き換えてください。

## `trrs-vcc-short.cir`

### 比較する2経路

1. 5 Vが中央コネクタへ出ており、挿抜中にGNDへ触れる経路
2. 中央コネクタに電源線が存在しないパッシブ方式

1つ目では、制御パルスが10.000 msから10.050 msまで短絡スイッチをオンにします。電源電流のピークと、50 µsに流れた電荷量の近似を測定します。

2つ目には5 V源からコネクタへの回路素子がありません。SPICE上で電流が小さいというより、対象となるVCC短絡ブランチ自体が存在しません。これがアーキテクチャ上の差です。

### 読み方

表示される大電流はPCのUSBポートで実際に流れる値ではありません。実機ではホスト側の電流制限、ヒューズ、ケーブル抵抗、コネクタ抵抗が影響します。重要なのは「VCCを通すと短絡ループが成立する」ことです。

USBポートを故意に短絡してモデルを検証してはいけません。電流制限付き電源と保護した試験治具を使います。

## `gpio-series-resistors.cir`

### 比較する枝

同じ1 msの故障パルスに対し、外部直列抵抗がほぼ0、100、220、330、470 Ωの5枝を同時に解析します。各枝は別の3.3 V源と25 Ωの出力抵抗を持つため、相互に影響しません。

概算電流は次です。

```text
I ≈ 3.3 V / (25 Ω + Rseries + 0.05 Ω)
```

したがって330 Ωでは約9.3 mA、470 Ωでは約6.7 mAになります。これはSPICEモデル内の期待値であり、RP2040の保証値ではありません。

### 直列抵抗の限界

- 抵抗よりMCU側の短絡には効かない
- ESDエネルギーをクランプする部品ではない
- High/Low閾値と立上り時間の確認が必要
- 全GPIOが同時に競合する故障は、合計電流も評価する

## `passive-connector-bounce.cir`

### モデル化した動作

- 左側GPIOが1 MHzより十分遅いテスト用矩形波を出す
- 採用値470 Ωを通ってコネクタへ向かう
- コネクタは複数回ON/OFFしてから接続状態になる
- 右側は300 pFと100 kΩの受動負荷だけ
- VCC線は存在しない

接点が開いている間、右側ノードは100 kΩでGNDへ戻る仮想測定負荷により0 Vへ向かいます。実際のパッシブキーマトリクスでは、未押下のスイッチ経路は開放であり、観測条件はファームウェアのプルアップ/プルダウン設定に依存します。

### 確認すること

- 故障期間の直列抵抗電流
- 接続後のHighレベル
- 300 pF負荷での立上り時間
- 接点バウンスが収まった後に定常状態へ戻ること

実ケーブルの容量をLCRメータで測ったら、`Ccable`を置き換えて再実行します。ケーブル長を変えた試験では、抵抗値だけでなく容量も一緒に記録してください。

## `hardware/sim/rj45-protection-selection.cir`

Issue #9の採用判断用モデルです。220/330/470 Ωについて、ケーブルと両端TVSの容量を加えた立上り、
pull-upと近似ダイオードを通る閉キーLOW、signal–GND短絡電流を比較します。

2 mケーブルはBelden 1583Eの最大56 pF/mと95 Ω/kmを基礎に、容量120 pF、接点を含む抵抗1 Ωへ丸めています。
GPIO出力抵抗25 Ωと1N4148Wの近似モデルは保証値ではありません。

同じ回路には24 Vと48 Vを採用値470 Ωへ直接加える枝があります。これはPoE耐性試験ではなく、
抵抗損失が約1.23 Wと4.90 Wになり、0.1 W部品と低電圧TVSで保護できないことを示す境界確認です。
LANやPoE機器を接続して再現してはいけません。

## シミュレーションの合格条件を決める

固定の万能値はありません。採用部品に基づいて次を記録します。

- GPIO最大故障電流が、設計で定めた限度未満
- High/Low電圧が、温度と電源ばらつきを含む入力閾値を満たす
- 立上り/立下りが、走査周期に対して十分短い
- 故障除去後にラッチ状態や持続電流が残らない
- 最大ステップを半分にしても、ピークと積分値が許容差内
- 最小/代表/最大モデルで結論が逆転しない

数値と根拠を`simulation-report.md`のような別文書へ保存すると、後で抵抗やMCUを変更したときに比較できます。

## 現在の簡略モデル実行結果

ngspice 45で確認した測定値、再現コマンド、読み方は[教育用ngspiceモデルの基準結果](https://github.com/hjosugi/electronics/blob/main/docs/09-simulation-results.md)へ分離しています。値を変更したときは、数値が変わった理由をモデル差として記録します。最終判断は採用MCUの定格、実ケーブル、電流制限付き治具での測定へ置き換えます。


---

## 基板化と実機検証のチェックリスト

## 安全上の前提

次の試験は、PCのUSBポートを故意に短絡して行いません。初期通電には、電流上限を設定できる電源、電流計、または保護されたUSBハブを使います。測定器のGNDクリップで意図しない短絡を作らないよう、接地方式も確認してください。

シミュレーション、ERC、DRCが通っても、実コネクタのピン番号違い、はんだブリッジ、ケーブル配線違いは残り得ます。通電前の導通試験を省略しません。

## 1. 部品確定前

- [ ] MCUモジュールの正確な型番と回路図を入手した
- [ ] GPIOが3.3 V専用か、5 V tolerantかを確認した
- [ ] 1ピンと全GPIO合計の電流条件を確認した
- [ ] 8P8Cジャックの接点番号を機械図で確認した
- [ ] マグネティクス、LED、抵抗が内蔵されていないジャックを選んだ
- [ ] シールド端子の接続方針を決めた
- [ ] 直列抵抗の値とパッケージを決めた
- [ ] TVSを使う場合、`VRWM`、容量、漏れ、クランプ、パッケージを確認した
- [ ] ケーブルはストレート結線の専用品を決めた
- [ ] `SPLIT ONLY / NO LAN / NO PoE`表示場所を確保した

## 2. KiCad回路図

- [ ] 中央コネクタに電源ネットが1本もない
- [ ] `R_ROW_*`と`R_COL_*`がすべて直列抵抗を通る
- [ ] 抵抗はMCUと外部コネクタの間にある
- [ ] 左右のコネクタ番号が同じ向きで対応している
- [ ] Japanese duplexのダイオード方向がキー割り当てと一致する
- [ ] NCピンはNo Connect指定または意図した未接続になっている
- [ ] TVSからGNDまでが短い配置になる回路階層にした
- [ ] テストポイントが抵抗のMCU側とコネクタ側にある
- [ ] ERC警告を1件ずつ説明できる

## 3. PCBレイアウト

- [ ] コネクタ外形、ラッチ方向、ケース開口が一致する
- [ ] 基板端からコネクタの張り出し量が正しい
- [ ] TVSはコネクタ直後で、保護対象より先に配線される
- [ ] TVSのGNDビアを部品近傍へ複数置く設計を検討した
- [ ] 直列抵抗をバイパスする銅箔やテスト配線がない
- [ ] 外部信号をクロック、USB、発振子から離した
- [ ] コネクタ周辺に読める警告シルクがある
- [ ] DRCが0件、または全例外に根拠がある
- [ ] 3D表示と実部品データシートの寸法を照合した

## 4. 無通電検査

### ケーブル単体

1. 両端の接点1同士が導通する。
2. 2同士から8同士まで同様に確認する。
3. 隣接接点、シールド、ラッチ金具との短絡がない。
4. ケーブルを曲げながら導通が途切れない。
5. 合格ケーブルへ専用ラベルを付ける。

### 基板

1. USB VBUSと中央コネクタ全接点が非導通である。
2. 3V3と中央コネクタ全接点が非導通である。
3. GNDは指定した接点だけへ導通する。
4. 各GPIOから対応接点までの抵抗値が、実装した直列抵抗と一致する。
5. 隣接接点の短絡がない。
6. 左右を接続し、各キーのダイオード方向をダイオードモードで確認する。

## 5. 初回通電

1. 右側と中央ケーブルを外す。
2. 電流上限を低く設定した5 V電源または保護治具で左側だけを通電する。
3. 3V3が定格内で、待機電流が設計値と大きく違わないことを確認する。
4. QMKを書き込み、左側キーだけを検証する。
5. 電源を切り、合格済みケーブルと右側を接続する。
6. 再通電し、右側を含む全キーを1つずつ確認する。
7. 同時押し、逆向きダイオードの組、未使用matrix位置を確認する。

最初からPC本体へ接続せず、異常電流時に切り分けられる経路を使います。

## 6. ホットアンプラグ試験

### 観測項目

- USB側の供給電流
- 3V3レール
- コネクタ側の代表行・列信号
- 抜線前後のキー状態
- QMKの停止、再起動、USB切断の有無

### 手順

1. 何もキーを押さず右側を抜く。
2. 右側の単独キーを押したまま抜く。
3. 逆ダイオード方向を使う2キーを押したまま抜く。
4. ケーブルを再接続し、全キーが復帰することを確認する。
5. 抜き差し速度を変えて繰り返す。
6. PC側USBが再列挙されていないことをログで確認する。

押したまま抜いたキーがファームウェア上で押下状態に残る場合、電気回路が壊れていなくても操作上の不具合です。抜線を検知できない完全パッシブ方式では、matrix scanの未検出状態がキー解放として処理されることをQMKテストと実機の両方で確認します。

## 7. ホットプラグ試験

1. 右側を外した状態で左側を動作させる。
2. キーを押していない右側を接続する。
3. 接続直後に誤キー入力がないことを確認する。
4. 右側キーを押した状態で接続し、想定した入力だけが出ることを確認する。
5. USB供給電流と3V3に異常なピークやリセットがないことを確認する。
6. 接続後に全キーと同時押しを再確認する。

## 8. 信号品質

- 代表行・列のHigh/Low電圧をオシロスコープで測る
- ケーブルなし、短いケーブル、最長予定ケーブルで比較する
- 330 Ωと470 Ωを比較する場合、立上り時間とノイズを記録する
- scan開始直後ではなく、入力をサンプルする時点の電圧を見る
- リング、オーバーシュート、二重遷移があれば、配線、抵抗、サンプル時間を見直す

ロジックアナライザだけではアナログの閾値余裕やオーバーシュートを見落とします。最終段階ではオシロスコープを使います。

## 9. 合格記録

最低限、次を残します。

| 項目 | 記録例 |
| --- | --- |
| 基板リビジョン | rev A |
| 回路図Git SHA | 40桁SHA |
| MCU/ボード型番 | メーカー型番まで |
| ファームウェアGit SHA | 40桁SHA |
| 直列抵抗 | 470 Ω、許容差1% |
| TVS | 型番、実装有無 |
| ケーブル | 長さ、結線、製品型番 |
| 電源 | 型番、電流上限 |
| オシロスコープ | 帯域、プローブ条件 |
| 試験回数 | unplug/plug各回数 |
| 結果 | 電流、電圧、誤入力、再起動 |

「動いた」だけでなく、どのハードウェアとファームウェアの組み合わせで確認したかを再現できる形にします。

## 10. 発注前の停止条件

次のどれかが残る場合、製造発注を止めます。

- 中央コネクタに電源ネットがある
- コネクタ接点番号を実部品データシートで確認できない
- 直列抵抗を通らない外部GPIOがある
- ERC/DRCエラーの意味が不明
- ケーブル結線を固定できない
- Japanese duplex走査の自動テストがない
- 故障電流をMCU定格と比較していない
- シミュレーションと実回路で使う値が一致していない


---

## 参考資料の評価

## 評価基準

資料を「有名かどうか」ではなく、今回の要件へ直接使える証拠かで分類します。

- キー配置やPCB作業の参考
- 1 MCUパッシブ分割の実例
- 2 MCU通信の実例
- ホットプラグ安全性の一次資料
- 部品の電気定格を決めるデータシート

別の目的に優れた資料を、ホットプラグ安全性の根拠へ流用しません。

## Cheapino

[Cheapino](https://github.com/tompi/cheapino)は、8P8C接続、Japanese duplex matrix、1 MCUという設計思想を明記しており、今回のアーキテクチャに最も近い公開作例です。

参考にできること:

- 1 MCUで左右を走査する全体構成
- Japanese duplexのキー割り当てとファームウェア
- 8P8Cコネクタの基板・ケース実装
- 左右を分けた組立とトラブルシュート

そのまま流用しないこと:

- 本資料の36/42キー用論理ピン割り当て
- 採用する別型番ジャックのフットプリント
- MCUボードが違う場合のGPIO定格
- 自分のケース、ケーブル、ESD要件

Cheapinoが存在することは有力な設計参考ですが、自作基板のERC、DRC、導通、耐久試験を省略する根拠にはなりません。

## Salicylic-acid3/KiCAD_FootPrint

[KiCAD_FootPrint](https://github.com/Salicylic-acid3/KiCAD_FootPrint)は、キースイッチ、穴、スタビライザーなど自作キーボード向けのフットプリント集です。配置作業の出発点として有用です。

注意点:

- フットプリント集は、ホットプラグ保護回路のリファレンス回路ではない
- ライブラリ内の複数作者・ライセンス表記を維持する
- 採用する実部品のデータシートとパッド寸法を照合する
- KiCadバージョン変換後にDRCと3D位置を再確認する
- TRRSフットプリントが存在しても、今回TRRSを採用する理由にはならない

特にコネクタは、シンボル名やA/B/C/Dのようなパッド名だけでTip/Ring/Sleeveまたは接点番号を推測しません。テスターと部品データシートで対応を確定します。

## サリチル酸さんの設計資料

[GL516デザインガイド](https://zenn.dev/salicylic_acid3/books/gl516_design_guide/)などは、キーレイアウト、プレート、PCB、発注、QMKまでの設計工程を体系的に学ぶ資料です。

今回の使いどころ:

- キー配置から基板外形へ進む作業順序
- KiCadでの部品配置、配線、製造データの考え方
- 組立性とケースを含めたレビュー

公開年と使用KiCadバージョンを確認し、KiCad 10のUI、ライブラリ、ファイル形式へ読み替えます。ホットプラグの電気要件はQMK公式と部品データシートを優先します。

## Caravelle-BLE

[Caravelle-BLE build guide](https://github.com/satt99/caravelle-build-guide)は、左右へ独立した電池を持たせ、Bluetoothで接続する別解の参考です。

参考にできること:

- 中央ケーブルをなくす設計方針
- 左右個別の電源、組立、ペアリング手順
- 無線分割キーボードのユーザー体験

今回のパッシブ右手方式へ直接持ち込めないこと:

- 電池と電源回路
- 無線MCUとペアリング
- 右側が能動回路である前提

「ケーブルがないので中央挿抜問題がない」という設計上の比較対象です。

## Auto-KDK

[Auto-KDK](https://github.com/sekigon-gonnoc/auto-kdk)は、キー配置からPCB、ケース、ファームウェア設定を生成する設計自動化ツールです。現在のREADMEでは、有線RP2040と無線nRF52840の専用コントローラ、EasyEDAを使う発注手順が説明されています。

参考にできること:

- キー配置、ケース、PCB、ファームウェアを一貫して生成する流れ
- 配線後のDRCと製造手順
- 分割型レイアウトの試作速度

注意点:

- READMEは左右通信用コネクタを別々のPCへ接続すると、PCを含め破損する危険があると警告している
- 生成物は今回の「1 MCU + 右側パッシブ + 電源なし」と同一構成とは限らない
- 自動配線が成功しても、電源役割、誤接続、ホットプラグの故障解析は別途必要
- EasyEDA中心の工程は、KiCad + ngspiceのシミュレーション工程と分けて考える

Auto-KDKは設計作業の自動化には有用ですが、ホットプラグ安全回路を検証済みにする道具ではありません。

## QMK

今回の要件で最も重要な一次資料は[QMK Split Keyboard](https://docs.qmk.fm/features/split_keyboard)です。TRRS + VCCがホットプラグ不可であること、USB形状のケーブルが誤接続される危険を、公式資料が明示しています。

またRP2040の2 MCU案を評価する場合は、[RP2040 platform](https://docs.qmk.fm/platformdev_rp2040)と[serial driver](https://docs.qmk.fm/drivers/serial)を参照します。PIO full-duplexのサポートは通信機能の証拠であり、電源保護の証拠ではありません。

## KiCad 10とngspice

2026年7月31日時点でKiCad公式ブログの最新安定版案内は[10.0.5](https://www.kicad.org/blog/2026/07/KiCad-10.0.5-Release/)です。KiCad 10の公式回路図マニュアルは、統合シミュレータがngspiceを使い、過渡解析とIBISモデルを扱えることを説明しています。

KiCadはPCBまで含む設計の正本、ngspiceは回路挙動の解析エンジンとして使います。古い記事に合わせてKiCadを下げるのではなく、概念を現行UIと公式ライブラリへ読み替えます。

## 資料を採用する順序

1. MCU、コネクタ、保護ICのメーカー・データシート
2. QMK、KiCad、ngspiceの公式文書
3. Cheapinoなど設計ファイルが公開された実例
4. 設計ガイドと自動化ツール
5. 個人ブログ、動画、掲示板

下位資料は発見や作業手順に役立ちますが、上位資料と矛盾する電気定格や安全判断には使いません。


---

## 一次資料と更新日

確認日: 2026-08-01

リンク先は更新されることがあります。製造直前に、版番号、改訂日、採用部品の注文型番を再確認してください。

## 分割キーボードとファームウェア

- [QMK: Split Keyboard](https://docs.qmk.fm/features/split_keyboard)
  TRRS + VCCがホットプラグ不可であること、左右間へUSB形状のケーブルを使う誤接続リスク。
- [QMK: Raspberry Pi RP2040](https://docs.qmk.fm/platformdev_rp2040)
  RP2040のsplit keyboard、SIO/PIO、half/full-duplexサポート。
- [QMK: serial Driver](https://docs.qmk.fm/drivers/serial)
  RP2040 PIOのfull-duplex設定と使用リソース。
- [QMK: Unit Testing](https://docs.qmk.fm/unit_testing)
  Google Testベースのテストと`make test:all`。
- [Raspberry Pi: RP2040 Datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
  GPIO、電源、絶対最大定格、PIOの一次資料。
- [Waveshare: RP2040-Zero](https://www.waveshare.com/wiki/RP2040-Zero)
  公式回路図、pinout、GPIO16のオンボードRGBを確認。
- [QMK: Custom Matrix](https://docs.qmk.fm/custom_matrix)
  `COL2ROW`と`ROW2COL`を併用する不規則matrixのcustom scan。

## 参考キーボード

- [tompi/cheapino](https://github.com/tompi/cheapino)
  1 MCU、8P8C、Japanese duplex matrixの公開作例。
- [pashutk/chocofi（参照commit）](https://github.com/pashutk/chocofi/tree/273676d11b06785fb5a1a94860a39fc36c38baba)
  36キー、Choc、3×5+3の物理配置基準。座標の派生範囲とCERN-OHL-P-2.0は`docs/layout/`に記録。
- [Kinesis Advantage2公式資料](https://kinesis-ergo.com/shop/advantage2/)
  左右分離、縦列、親指クラスタ、20° tenting、concave keywellのメーカー説明。
- [Kailh PG1350シリーズ](https://www.kailhswitch.com/info/kailh-kl-switches-pg1350-series-23772219.html)
  Choc v1のスイッチ型番、操作力、ストロークのメーカー資料。
- [Salicylic-acid3/KiCAD_FootPrint](https://github.com/Salicylic-acid3/KiCAD_FootPrint)
  自作キーボード向けKiCadフットプリント集。
- [サリチル酸: GL516デザインガイド](https://zenn.dev/salicylic_acid3/books/gl516_design_guide/)
  キー配置、PCB、ケース、発注を含む設計工程。
- [satt99/caravelle-build-guide](https://github.com/satt99/caravelle-build-guide)
  左右独立電源の無線分割キーボード作例。
- [sekigon-gonnoc/auto-kdk](https://github.com/sekigon-gonnoc/auto-kdk)
  PCB、ケース、ファームウェア設定の自動生成と誤接続警告。

## EDAとシミュレーション

- [KiCad 10: Schematic Editor / Simulator](https://docs.kicad.org/10.0/ja/eeschema/eeschema.html#simulator)
  ngspice統合、過渡解析、IBISモデル。
- [KiCad 10.0.5 Release](https://www.kicad.org/blog/2026/07/KiCad-10.0.5-Release/)
  2026年7月22日公開の安定版案内。
- [ngspice](https://ngspice.sourceforge.io/)
  OSS SPICEエンジン。
- [ngspice documentation](https://ngspice.sourceforge.io/docs.html)
  ユーザーマニュアル、過渡解析、内部動作資料。
- [Qucs-S](https://ra3xdh.github.io/)
  ngspiceなどのOSSバックエンドを使えるQt GUI。
- [Qucs-S: Choosing a Simulation Backend](https://qucs-s-help.readthedocs.io/en/latest/overview/choosing-a-sim-backend.html)
  バックエンド比較とngspice推奨。
- [pfalstad/circuitjs1](https://github.com/pfalstad/circuitjs1)
  Falstad Circuit Simulatorのブラウザ版ソース。
- [Ergogen: Points](https://docs.ergogen.xyz/points/)
  column stagger、spread、splay、独立zoneをパラメータ化する公式資料。
- [Keyboard Layout Editor: serial.js](https://github.com/ijprest/keyboard-layout-editor/blob/580b916084e69e600b2144b0217c8b1d9710daa0/serial.js)
  KLE Raw dataのメタデータ、座標、回転を扱う公式実装。

## USB-Cと保護部品

- [USB-IF: USB Type-C Cable and Connector Specification Release 2.5](https://usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-25)
  2026年4月8日公開のType-Cケーブル・コネクタ仕様。
- [TI: TUSB320](https://www.ti.com/lit/ds/symlink/tusb320.pdf)
  CC attach、向き、DFP/UFP/DRPの検出と制御。
- [TI: TPS2552/TPS2553](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf)
  電流制限、逆電圧保護、FAULT、遅延時間。
- [TI: TPD2EUSB30A](https://www.ti.com/product/TPD2EUSB30A)
  2チャネル、3.6 V `VRWM`、低容量ESD保護の選定例。

## 採用する8P8C保護回路

- [TI: TPD4E05U06 datasheet Rev. O](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf)
  4 channel、5.5 V `VRWM`、0.5 pF typical、IEC 61000-4-2部品定格、USON-10 pinout。
- [Panasonic: ERJ3EKF4700V](https://industrial.panasonic.com/ww/products/pt/general-purpose-chip-resistors/models/ERJ3EKF4700V)
  470 Ω、1%、0603、0.100 Wの注文型番。
- [Diodes Incorporated: 1N4148W DS30086 Rev. 31-2](https://www.diodes.com/datasheet/download/1N4148W.pdf)
  `1N4148W-7-F`、SOD123、カソード表示、電気特性。
- [Belden: 1583E technical data](https://catalog.belden.com/techdata/EN/1583E_techdata.pdf)
  Cat 5eケーブルの最大mutual capacitance 56 pF/m、最大導体DCR 95 Ω/km。
- [Ethernet Alliance: Overview of IEEE 802.3bt](https://ethernetalliance.org/wp-content/uploads/2018/04/WP_EA_Overview8023bt_FINAL.pdf)
  PoEのsignature detectionとpairsetへの給電条件。
- [Ubiquiti: EP-24V-72W](https://dl.ui.com/qsg/EP-24V-72W/EP-24V-72W_EN.html)
  pin 4/5正、7/8負で24 Vを出すpassive PoE製品の一次資料。
- [KiCad: Libraries License](https://www.kicad.org/libraries/license/)
  標準symbol/footprintのCC-BY-SA-4.0と設計ファイル向け例外。

## 本資料で行った訂正と限定

- `TPS2553 = 逆流を即時遮断`とは書かない。逆電圧検出には代表4 msの遅延がある。
- `RP2040でPIO full-duplexが使える = USB-C電源が安全`とは扱わない。
- `8P8Cに電源がない = ESDやPoE誤接続にも安全`とは扱わない。
- `470 Ωなら常に安全`とは扱わない。MCU定格と信号閾値で再評価する。
- `KiCadシミュレーション成功 = 製造可能`とは扱わない。ERC、DRC、導通、実測を別に行う。


---

## 実装ロードマップとIssue完了条件

## なぜIssueへ分けるのか

現在のリポジトリには参照回路と初期QMK定義がありますが、製造可能なPCBと実機評価はまだありません。「文書やCIが丁寧だから完成」とは扱いません。

未完成作業は[GitHub Issues](https://github.com/hjosugi/electronics/issues)と[`issues/`](../issues)の原稿で追跡します。各Issueには、背景、作業、客観的な完了条件があります。

## フェーズ0: 公開基盤

| Issue | 目的 | 完了の証拠 |
| --- | --- | --- |
| 01 KiCad環境 | KiCad 10とngspiceを同じ環境で使う | ERCとRC過渡解析の実行記録 |
| 02 QMK環境 | RP2040用QMKを再現ビルドする | 自作keyboard定義のUF2 |
| 03 repo初期化 | 文書、SPICE、CI、Issueを公開する | main SHA、PUBLIC読戻し、Issue一覧 |
| 04 ERC/DRC CI | 回路変更ごとの機械検査 | 意図的violationでCIが失敗する証拠 |

Issue 01は[PR #13](https://github.com/hjosugi/electronics/pull/13)で空回路ERCとRC過渡解析を確認済みですが、ホスト上のKiCad GUI確認が残っています。Issue 03は初回公開とIssue登録を確認済みです。Issue 04は[PR #15](https://github.com/hjosugi/electronics/pull/15)で意図的violationの検出を確認済みです。Issue 02は固定QMK commitからのローカルUF2とCI artifactを完了証拠にします。

## フェーズ1: 要件と回路

| Issue | 決めること | 主な成果物 |
| --- | --- | --- |
| 05 要件 | 36/42キー、スイッチ、ピッチ、stagger | レイアウトJSON、ADR |
| 06 matrix | 行列サイズ、ダイオード極性、GPIO | 回路図、割当表、ERC結果 |
| 07 8P8C保護 | pinout、直列R、TVS、禁止接続 | BOM候補、pinout、故障分析 |
| 08 MCU | RP2040-Zeroか素RP2040か | 選定ADR |

このフェーズでは、部品名だけでなく正確な注文型番、データシート改訂、シンボル/フットプリントの由来を記録します。Issue 05の要件が決まるまで、製造用配線を確定しません。

Issue 08では、初号機にWaveshare RP2040-Zeroモジュールを採用する判断を[ADR 0001](https://github.com/hjosugi/electronics/blob/main/docs/adr/0001-use-waveshare-rp2040-zero.md)へ記録しました。GPIO割り当て、保護回路、QMK設定の合格を先取りする決定ではありません。

Issue 05では、初号機を36キー、Kailh Choc v1、Chocofi基準の18×17 mm配置、エンコーダなしとする判断を[ADR 0002](../docs/adr/0002-use-36-key-choc-v1-layout.md)へ記録しました。Kinesisの縦列、独立親指クラスタ、分離、段階的tentingという原則を取り入れ、stagger、splay、親指位置、机上フィット値を[制限付きプロファイル](../docs/layout/profiles/balanced-kinesis-inspired.json)から生成します。人体適合、キーキャップ干渉、フットプリント、concave keywellは実機で未検証であり、後続Issueで確認します。

Issue 06、07、09では、36キーduplex matrix、GPIO0–11、中央8P8Cの`GND x2 + signal x6`、
470 Ω、両端TPD4E05U06DQAを[回路・安全性文書](../docs/13-matrix-rj45-safety.md)と
[ADR 0003](../docs/adr/0003-use-470-ohm-and-dual-ended-tvs.md)へ確定しました。KiCad 10 ERCとnetlist構造検査、
ngspice感度解析は合格済みです。これはPCB、QMK、活線挿抜、IEC ESDの完了を先取りしません。

## フェーズ2: シミュレーションとファームウェア

| Issue | 検証 | 合格の考え方 |
| --- | --- | --- |
| 09 protection | R/L/C、直列抵抗、TVS、GPIO閾値 | 候補値の根拠と感度解析 |
| 10 firmware | Japanese duplex走査、抜線、ghosting | QMK自動テスト + 2 × 2実機 |

Issue 02では、RP2040用の初期36キー定義、固定QMK commit、ローカルUF2、CI artifactを[ファームウェア環境](../docs/14-qmk-firmware.md)へ記録します。これはIssue 10の同時押し、抜線、ghosting、2 × 2実機検証を先取りしません。

Issue 10の自動部分では、全36位置、方向切替、右側抜線、ideal-diode ghost pathを[QMK matrixテスト](../docs/15-qmk-matrix-tests.md)で検査します。曖昧な半分は前状態へ保留しますが、2 × 2実配線が未実施なのでIssueはopenのままです。

SPICEとQMKテストは別の証拠です。SPICEは電圧・電流を検証し、QMKテストはキー状態を検証します。片方の合格で他方を省略しません。

## フェーズ3: 実基板

Issue 11では、電流制限付き電源と専用治具を使って活線挿抜を評価します。

- 通常挿抜100回
- 供給電流、3V3、代表GPIOの観測
- 誤入力、押下残り、USB再列挙の確認
- 基板SHA、firmware SHA、ケーブル、測定器の記録

PCのUSBポート、Ethernetスイッチ、PoE機器を故障注入用には使いません。誤接続は机上解析、無通電導通、保護した治具で評価します。

[Issue #16](https://github.com/hjosugi/electronics/issues/16)では、Kinesisの原則をケースへ適用し、平面PCB + 交換式wedgeとtrue keywell候補を比較します。初号機は0°、10°、20°のtentingを先に検証し、concave keywellは配線方式、組立公差、実測計画を伴う別アーキテクチャとして扱います。リポジトリ内の正本は`issues/13-kinesis-keywell-case.md`です。GitHubではIssueとPull Requestが同じ連番を使うため、ファイル番号と公開Issue番号は一致しません。

## フェーズ4: NotebookLMと発注

Issue 12では、統合Markdownと一次資料をNotebookLMへ登録し、設計判断を検索できる状態にします。発注前には次の成果物をそろえます。

NotebookLM入力、製造snapshot、Gerber/BOM/viewer確認は[発注readyチェックリスト](../docs/16-notebooklm-order-readiness.md)と`production/order-readiness.json`で追跡します。製造用PCBが存在しない現在は機械判定も`NOT READY`であり、仮Gerberを生成して進捗扱いにはしません。

- ERC/DRC結果
- 回路図・PCB PDF
- Gerberとドリルのviewer確認
- BOMの注文型番と代替部品
- pinoutと警告シルク
- シミュレーション報告
- ファームウェアのビルド/テスト結果
- 発注チェックリスト

## Issueをcloseする規則

- 完了条件をすべて満たした証拠をコメントする
- CIが通ったことと、実機が通ったことを混同しない
- 環境制約で未実施の項目を成功扱いしない
- 後続Issueへ移した作業は、移動先を明記する
- 最終成果物のcommit SHAまたはURLを残す

Issue原稿とGitHub本文に差が出た場合、最新の設計判断をADRまたは正式文書へ反映して、チャットやIssueコメントだけに閉じ込めません。


---

## 教育用ngspiceモデルの基準結果

実行日: 2026-08-01
実行環境: ngspice 45（Nix `nixpkgs#ngspice`）

## 再現コマンド

```bash
nix shell nixpkgs#ngspice nixpkgs#shellcheck -c make validate
```

この結果は、リポジトリに収録した理想化モデルの回帰基準です。実際のUSBポート、RP2040、8P8Cケーブル、TVS、コネクタを測定した結果ではありません。

## TRRS相当のVCC–GND短絡

`spice/trrs-vcc-short.cir`は、5 V源、0.30 Ωの仮想電源・配線抵抗、0.05 Ωの接点、100 nFの容量を使い、50 µsの短絡を作ります。

| 測定 | 結果 |
| --- | ---: |
| 電源電流ピーク | 14.28586 A |
| 接点側の最低電圧 | 0.7142426 V |
| 50 µs間の電荷 | 714.217 µC |

14 Aという値をPCのUSBポートで流れる実電流として扱ってはいけません。実機ではホスト側保護、ケーブル、ヒューズ、電源インピーダンスが異なります。このモデルが示すのは、中央コネクタへVCCを出すと短絡ループが成立することです。推奨するパッシブ方式には、このVCCブランチ自体がありません。

## GPIO–GND故障と直列抵抗

`spice/gpio-series-resistors.cir`は、3.3 V源と仮のGPIO出力抵抗25 Ωを各枝へ置き、1 msのGND故障を比較します。

| 外部直列抵抗 | 電流ピーク |
| ---: | ---: |
| 約0 Ω | 131.7313 mA |
| 100 Ω | 26.38944 mA |
| 220 Ω | 13.46664 mA |
| 330 Ω | 9.294466 mA |
| 470 Ω | 6.665993 mA |

直列抵抗を大きくすると、この仮定モデルの故障電流は下がります。一方で信号の立上りと入力閾値への余裕も変わるため、この表だけで330 Ωまたは470 Ωを確定しません。

## パッシブ右側の接点バウンス

`spice/passive-connector-bounce.cir`は、採用値470 Ω、300 pFの仮想ケーブル容量、100 kΩの測定負荷を置き、接点が複数回開閉してから接続する状態を作ります。

| 測定 | 結果 |
| --- | ---: |
| GPIO電源電流ピーク | 6.413094 mA |
| 接続後の右側電圧 | 3.283744 V |
| 接続後の左側電圧 | 3.283745 V |

モデル内に中央VCCはありません。ただし、これだけでは接続直後の誤キー、ESD、クロストーク、実ケーブルの反射、GPIO競合が安全とは証明できません。

## 8P8C保護回路と470 Ωの選定

`hardware/sim/rj45-protection-selection.cir`は、2 mケーブル120 pF、RP2040のI/O timing試験条件にある
nominal load 5 pFを比較用負荷として使い、
両端TPD4E05U06DQA合計1 pF、50 kΩ pull-up、接点込み1 Ω、仮のGPIO出力抵抗25 Ωを使います。
閉キーLOWは実配線どおりsense側とdrive側の両方へ候補抵抗を入れ、MCU入力pinで測定しています。

| 直列抵抗 | 10–90% rise | HIGH（2 µs） | 閉キーLOW | signal–GND故障電流 |
| ---: | ---: | ---: | ---: | ---: |
| 220 Ω | 68.753 ns | 3.289884 V | 0.492783 V | 13.4666 mA |
| 330 Ω | 99.925 ns | 3.285380 V | 0.504759 V | 9.294466 mA |
| 470 Ω | 139.995 ns | 3.279666 V | 0.519854 V | 6.665993 mA |

RP2040の3.3 V時入力閾値`VIH >= 2.0 V`、`VIL <= 0.8 V`と1 µsのsettling条件に対し、
3候補ともこのモデルでは余裕があります。470 Ωはrise 140 nsを維持しながら単線故障を最小にします。
6線がそれぞれGNDへ短絡する仮定合計は39.996 mAで、330 Ωの55.767 mAと異なりRP2040の
全GPIO source上限50 mAを下回るため採用しました。これは他GPIO負荷や部品差を含む無損傷保証ではありません。

| 誤給電モデル | 470 Ω電流 | 470 Ω損失 |
| --- | ---: | ---: |
| 24 V | 51.064 mA | 1.22553 W |
| 48 V | 102.128 mA | 4.90213 W |

これはPoEを接続してよいという結果ではなく、0.1 Wの採用抵抗とTPD4E05U06DQAではPoEを保護できない証拠です。
モデル、採用理由、禁止条件は[ADR 0003](../docs/adr/0003-use-470-ohm-and-dual-ended-tvs.md)に記録しました。

## 次に置き換える仮定

1. RP2040またはモジュール実測から得るGPIO出力インピーダンス
2. 組み立てに使う実ケーブルのLCR実測値と長さ
3. 採用TVSのメーカーSPICEモデル、漏れ、クランプ動特性
4. firmwareのdrive strength、pull、scan周期、sample時刻
5. 最小・代表・最大条件と温度範囲

最終判断は、[基板化と実機検証のチェックリスト](https://github.com/hjosugi/electronics/blob/main/docs/05-hardware-validation.md)に従ってERC、DRC、無通電導通、電流制限付き電源、オシロスコープ、ファームウェアテストを組み合わせて行います。


---

## KiCad 10開発環境とスモークテスト

この文書は、Issue #1の環境構築を別のCachyOS/Arch環境でも再現するための手順と検証記録です。ホストへの導入、CI、回路シミュレーションを分けて扱います。

## 確認したパッケージ

2026年8月1日にCachyOSの`pacman -Si`とArch Linux公式パッケージ情報を確認しました。

| パッケージ | 確認した版 | 用途 |
|---|---:|---|
| `kicad` | 10.0.5 | 回路図、PCB、`kicad-cli`。Arch版は`ngspice`へ依存 |
| `kicad-library` | 10.0.5 | 標準シンボルとフットプリント |
| `kicad-library-3d` | 10.0.5 | 標準3Dモデル。ERCだけなら必須ではない |
| `ngspice` | 46 | 単体CLIでのSPICE再現試験 |

一次資料は[Arch LinuxのKiCadパッケージ](https://archlinux.org/packages/extra/x86_64/kicad/)と[ngspiceパッケージ](https://archlinux.org/packages/extra/x86_64/ngspice/)です。ミラーの同期時差により、CachyOS側とArch側でリビジョン末尾が一時的に異なることがあります。

## ホストへ導入する場合

パッケージ情報を更新してから導入します。

CachyOSのGUI認証が動く端末で、システムを更新してから導入します。

```bash
pkexec pacman -Syu
pkexec pacman -S --needed kicad kicad-library ngspice
```

3D表示も使う場合は、展開後約3.2 GBのライブラリを追加します。

```bash
pkexec pacman -S --needed kicad-library-3d
```

バージョンを確認します。

```bash
kicad-cli version
ngspice --version
```

このリポジトリの自動検証はKiCad 10.0.xを要求します。将来KiCad 11へ移行するときは、ファイル形式、ERC/DRC差分、CIコンテナを別Issueで更新します。

## ERCスモークテスト

[`hardware/env-check/empty.kicad_sch`](../hardware/env-check/empty.kicad_sch)は、標準ライブラリに依存しない空のKiCad回路図です。次のコマンドはKiCadの版を検査し、`hardware/`以下の全回路図へERC、全基板へDRCを実行します。

```bash
make check-kicad
```

内部では公式CLIの次のオプションを使います。

```bash
kicad-cli sch erc --exit-code-violations --severity-all empty.kicad_sch
```

`--exit-code-violations`により、ERC violationがあれば終了コード5となりCIも失敗します。レポートは一時ディレクトリへ出力し、作業ツリーには残しません。

## RC過渡解析スモークテスト

[`spice/rc-transient.cir`](../spice/rc-transient.cir)は、5 Vステップ、1 kΩ、1 µFの一次RC回路です。時定数は次のとおりです。

```text
tau = R * C = 1 kΩ * 1 µF = 1 ms
V(tau) = 5 V * (1 - exp(-1)) ≈ 3.16 V
```

実行コマンドは次です。

```bash
ngspice -b spice/rc-transient.cir
```

`vout_at_tau_v`が約3.16 V、`time_to_63pct_s`が約1 msと表示されれば、過渡解析と`.meas`が動作しています。全SPICEモデルをまとめて実行する場合は`make simulate`を使います。

## KiCad GUIでの確認

1. KiCadでこのリポジトリを開く。
2. `hardware/env-check/empty.kicad_sch`を回路図エディタで開く。
3. `検査` → `エレクトリカル・ルール・チェッカー`を開き、ERCを実行する。
4. `検査` → `シミュレータ`を開き、シミュレータ自体が起動することを確認する。
5. RC回路をGUIで再作成する場合は、過渡解析を`0`から`5 ms`、最大時間ステップを`1 µs`程度に設定し、`V(out)`が1 ms付近で約3.16 Vになることを確認する。

自動判定の正本はCLIです。GUI確認は、画面表示、メニュー、ホスト固有の共有ライブラリ読み込みを確認する補助試験として扱います。

## `.gitignore`の照合

KiCadの正本ファイルである`.kicad_pro`、`.kicad_sch`、`.kicad_pcb`は追跡対象です。次は生成物または端末固有状態なので除外します。

| パターン | 理由 |
|---|---|
| `*.kicad_prl` | ローカルUI・作業状態 |
| `*-backups/`、`*.bak`、`_autosave-*` | バックアップと自動保存 |
| `~*.lck`、`*.lck` | 編集中のロックファイル |
| `fp-info-cache` | 再生成可能なキャッシュ |
| `*.raw`、`*.log`、`*.tmp` | SPICE出力と一時ファイル |
| `hardware/gerbers/`、`hardware/production/` | CIで再生成する製造出力 |

回路図、基板、シンボル、フットプリントを新しく追加したときは、必要な正本まで広いglobで除外していないか`git status --ignored`で確認します。

## CI

`hardware/**`を変更すると`hardware-ci`がKiCad 10コンテナで次を実行します。

```bash
make validate-hardware
```

これによりKiCad 10.0.x、ERC/DRC、RCを含むngspiceモデルを同じジョブで確認できます。空回路のERC成功は環境スモークテストであり、将来の実回路の電気的妥当性や安全性を保証しません。

## 2026年8月1日の検証結果

Nix storeに取得済みのKiCad 10.0.5とngspice 45を使い、`make validate-hardware`を実行しました。

| 検査 | 結果 |
|---|---|
| `kicad-cli version` | `10.0.5` |
| 空回路ERC | violation 0件 |
| RC回路の`V(out)`、1 ms | `3.160602 V` |
| 63.212%到達時刻 | `0.999999 ms` |
| 既存SPICEモデル3本 | 全て完走 |
| Markdown、ShellCheck、Issue形式 | 合格 |

この数値は1 kΩ・1 µFの教育用RCモデルに対する環境確認値です。分割キーボードの保護部品や活線挿抜安全性の根拠には使用しません。

## ERC/DRC violationのnegative test

CIが「正常ファイルで緑になる」だけでなく、違反を確実に失敗として扱うことを次のfixtureで検証します。

| fixture | 意図した違反 | 期待結果 |
|---|---|---|
| `tests/fixtures/kicad/erc-dangling-wire.kicad_sch` | どこにも接続されないwire | `wire_dangling`、終了コード5 |
| `tests/fixtures/kicad/drc-open-outline.kicad_pcb` | 閉じていない`Edge.Cuts` | `invalid_outline`、終了コード5 |

実行コマンドは次です。

```bash
make check-kicad-negative
```

negative test用ファイルは`tests/fixtures/kicad/`に隔離し、製造用の`hardware/`検索対象へ混ぜません。スクリプトは単に非ゼロ終了を期待するのではなく、KiCad CLIがviolation時に返す終了コード5と、レポート中の違反IDを両方確認します。構文エラーやクラッシュを「違反検出成功」と誤認しません。

KiBotによるGerber、BOM、PDF生成は、製造用回路図とPCBが確定してから追加します。空回路とnegative fixtureしかない段階では、製造artifactを生成しても発注可能性の証拠にならないためです。


---

## CachyOSツールチェーン環境

確認日: 2026-08-01

## 状態を確認する

```bash
./scripts/check-environment.sh --report
./scripts/check-environment.sh --require-hardware
./scripts/check-environment.sh --require-firmware
```

`--report`は不足を表示しても成功します。`--require-hardware`はKiCad/ngspice、`--require-firmware`はQMKがなければ失敗するため、セットアップ完了の機械的な確認に使えます。

## CachyOS/Archのパッケージ

2026-08-01に、このホストの同期データベースで次を確認しました。

| パッケージ | 確認版 | 用途 |
| --- | --- | --- |
| `kicad` | 10.0.5-1.1 | 回路図、PCB、ERC/DRC、GUIシミュレータ |
| `kicad-library` | 10.0.5-1 | シンボル、フットプリント、テンプレート |
| `kicad-library-3d` | 10.0.5-1 | 3Dモデル、任意 |
| `ngspice` | 46-2.1 | `.cir`のCLI再現実行 |
| `qmk` | 1.2.0-2 | QMK CLIとクロスツールチェーン |

KiCad 3Dライブラリは展開後約3.2 GBです。回路図・PCB・SPICEを先に始めるだけなら省略し、ケース干渉や3D確認を始める時点で追加できます。

### ホストへ導入

CachyOSのGUI認証が動く端末で実行します。

```bash
pkexec pacman -S --needed kicad kicad-library ngspice qmk
```

3Dモデルも必要なら追加します。

```bash
pkexec pacman -S --needed kicad-library-3d
```

導入後:

```bash
kicad-cli version
ngspice --version
qmk --version
./scripts/check-environment.sh --require-all
```

`qmk setup`はQMK firmwareをユーザーディレクトリへcloneするため、保存先を確認してから別途実行します。

## root不要のSPICE検証

ホストへ恒久インストールせず、現在の文書・スクリプト・SPICEモデルだけを検証する場合:

```bash
nix shell nixpkgs#ngspice nixpkgs#shellcheck -c make validate
```

このコマンドはngspice 45で実行済みです。測定値は[基準結果](../docs/09-simulation-results.md)に記録しています。KiCad GUI、QMKのUF2ビルド、実機USB接続はこのコマンドの検証範囲外です。

## エージェント実行環境の制約

今回のエージェント環境では、`pkexec`のsetuid属性が無効化されており、ホストへのpacman導入は実行できませんでした。またNix daemonとDocker/Podman socketも一部のサンドボックス呼び出しから拒否されます。

これはパッケージ不在や回路の失敗ではありません。Issue #1はCLI/CIでERCとRC過渡解析まで確認済みですが、ホスト上のKiCad GUI確認が残っています。Issue #2は、QMK環境を導入してUF2をビルドするまで未完了です。


---

## 検証処理の並列化と性能

`make validate`と`make validate-hardware`は、互いに独立した検査を同時実行します。高速化のために検査を省略せず、各プロセスのログを一時ファイルへ分離してから決まった順序で表示します。

## 並列化の境界

[`scripts/run-validation.sh`](../scripts/run-validation.sh)は次を並列実行します。

- NotebookLM統合Markdownの再生成差分
- 36キーレイアウトの再生成差分、値域、不変条件
- ドキュメントCSSの必須変数、タイポグラフィ直書き、インラインstyle
- Markdownローカルリンク
- Bash構文、ShellCheck、Issue形式、`git diff --check`
- ngspiceモデル
- KiCad ERC/DRC一式（`validate-hardware`のみ）

[`scripts/check-spice.sh`](../scripts/check-spice.sh)は4回路を並列実行し、成功時は測定値だけを表示します。失敗時は該当回路の完全なngspiceログを表示します。

KiCadの通常検査とnegative testは、KiCad CLIのインスタンスロック競合を避けるため、[`scripts/check-kicad-suite.sh`](../scripts/check-kicad-suite.sh)の中で順番に実行します。KiCad一式は、他の検査とは並列に動きます。

## 2026年8月1日の測定

Nix storeのKiCad 10.0.5、ngspice 45、ShellCheck 0.11.0を使い、ウォームキャッシュで`validate-hardware`相当の全検査を各3回実行しました。この測定値はレイアウト/CSS検査を追加する前の基準値であり、追加後の性能値としては扱いません。

| 実装 | 1回目 | 2回目 | 3回目 | 中央値 |
|---|---:|---:|---:|---:|
| 完全直列 | 5,487 ms | 5,485 ms | 4,587 ms | 5,485 ms |
| 並列ランナー | 3,181 ms | 3,097 ms | 2,722 ms | 3,097 ms |

中央値では約44%短縮しました。この値は当該ホストと負荷状況での参考値であり、GitHub Actionsや別CPUで同じ比率になる保証はありません。

## CIの無駄な実行を減らす

`starter-ci`と`hardware-ci`にはref単位の`concurrency`を設定しています。同じブランチへ新しいcommitがpushされた場合、古い実行をキャンセルし、最新commitの検証を優先します。

性能変更後も、次のコマンドが合格することを必須とします。

```bash
make validate-hardware
```


---

## 36キーJapanese duplex matrixと8P8C保護回路

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


---

## RP2040 QMKファームウェア環境

## 結論

初号機用のQMK定義は、1個のWaveshare RP2040-Zeroから左右両方を直接走査します。右側にMCUはなく、中央8P8Cには6本のマトリクス信号とGNDだけを通します。QMKのsplit transport、VCC、VBUS、RAWは中央接続に使いません。

成果物は[`firmware/qmk/`](../firmware/qmk)にあります。上流QMKは`qmk-version.env`の完全なcommit SHAへ固定し、ローカルとGitHub Actionsで同じソースからUF2を生成します。

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
| QMK native tests | 6 tests passed |
| UF2 SHA-256 | `266826a48637016e0db4767345872961118c4c5274de118b6d745da2dc2af631` |

この記録は「ソースがRP2040向けにコンパイルできた」証拠です。GPIOの電圧、ダイオード極性、同時押し、抜線中の押下残り、活線挿抜安全性を証明するものではありません。

duplex走査とghost抑制の自動テスト、保守的な制限、2 × 2実機手順は[QMK matrixテスト](../docs/15-qmk-matrix-tests.md)に分離しています。

書き込み時はRP2040-ZeroをBOOTSELモードにし、表示された`RPI-RP2`ドライブへUF2をコピーします。基板がない現段階では書き込みと実キー検証をIssue #10の完了証拠にはしません。

## 静的検査

`make check-qmk`はネットワークやQMK checkoutなしで次を検査します。

- RP2040 / UF2 bootloader
- 3 × 12の全座標と36キー
- GP0–GP11の重複なし割り当て
- `CUSTOM_MATRIX = lite`
- 入力pull-upへの中立化と1 µs待ち
- topology固有のghost-risk filterとQMK native tests
- QMK split transportおよび電源rail依存がないこと
- ローカルpinとCI pinが同じQMK commitであること

## 上流資料

- [QMK: Set Up Your Environment](https://docs.qmk.fm/newbs_getting_started)
- [QMK: RP2040 Driver](https://docs.qmk.fm/platformdev_rp2040)
- [QMK: Custom Matrix](https://docs.qmk.fm/custom_matrix)
- [QMK: Data Driven Configuration](https://docs.qmk.fm/reference_info_json)
- [Cheapino custom matrix（設計比較）](https://github.com/tompi/qmk_firmware/blob/cheapino/keyboards/cheapino/matrix.c)

Cheapinoの双方向走査は設計比較に使いましたが、本実装は現在のQMK `CUSTOM_MATRIX = lite` API、今回確定したGPIO割り当て、安全な中立状態に合わせて新規に記述しています。


---

## QMK duplex matrix自動テストと2 × 2実機計画

確認日: 2026-08-01

## 現在の判定

QMKのnative GoogleTestを使う自動テストは合格しました。完成基板と2 × 2ブレッドボード試験は未実施なので、Issue #10はopenのままです。

| 検証 | 状態 | 証拠 |
| --- | --- | --- |
| 全36論理位置 | 合格 | 各位置を1個ずつ押し、対応bitだけが立つ |
| GPIO方向切替 | 合格 | 各相の前に6線input、出力Low 1本、settle後だけread |
| 非曖昧な同時押し | 合格 | 左右4キーで余分な位置なし |
| 右側抜線 | 合格 | 左キーを維持し、右キーを全解放 |
| 3-edge ghost path | 合格 | phantom候補を検出し、曖昧な半分を前状態へ固定 |
| 2 × 2実配線 | 未実施 | RP2040、ダイオード、470 Ω、ケーブルが必要 |

実行コマンドは固定QMK checkoutに対する通常ビルドと共通です。

```bash
QMK_HOME=/path/to/qmk_firmware make build-qmk
```

`build-qmk.sh`は`qmk test-c -t electronics_splitkb36`、`qmk lint`、RP2040 UF2 compileの順に実行します。test discoveryのためにテスト3ファイルだけをQMK checkoutへ一時コピーし、終了時に削除します。既存の同名keyboard/testがある場合は上書きせず停止します。

## テストモデル

テストと実機は[`duplex_matrix.c`](../firmware/qmk/keyboards/electronics/splitkb36/duplex_matrix.c)を共有します。GPIO関数だけをcallbackにし、テスト側は12本のpinと押下ダイオードを有向グラフとして模擬します。

- Bank A: `row -> column`
- Bank B: `column -> row`
- input pinから現在のoutput-low pinへ有向経路があればLow
- 右側をdisconnectするとGP6–GP11にLow経路を作らない

3本の押下が`R0 -> C0 -> R1 -> C1`のような交互経路を作ると、理想ダイオードモデルでは未押下の`R0 -> C1`もLowになります。reverse方向も同じです。raw scanだけから3実押下と4実押下を完全には区別できないため、firmwareは該当半分の6 logical columnsを前回状態に保ちます。反対側は通常どおり更新します。

これはphantom keyを出さない保守策ですが、曖昧な形の正当な3キー目・4キー目も一時的に認識しません。電圧降下で実機にghostが出ない場合でも、この制限は初号firmwareに残ります。実測後に解除または絞り込む場合は、同じ自動テストと新しい実測証拠が必要です。

論理matrixは3 × 12の全位置を36キーが使うため、未使用位置はありません。全座標を1回ずつ走査するテストが、欠落と重複を同時に検出します。

## 2 × 2 duplex実験系

PC直結で故障条件を作らず、電流制限付き3.3 V/5 V電源または保護したUSB hubを使います。中央リンクの通電挿抜評価はIssue #11の治具ができるまで行いません。

部品表、8キーの具体的な配線、左右halfの期待key、28通りの2-key、ghost path、段階的な通電、抜線と波形記録は[2 × 2 breadboard試験手順](../docs/17-breadboard-matrix-test.md)にまとめています。この節は完了条件の要約です。

最小配線は2 row + 2 column、Bank A/B各4キーの計8キーです。

| 信号 | RP2040 | 直列抵抗 | 用途 |
| --- | --- | ---: | --- |
| R0 | GP0 | 470 Ω | row 0 |
| R1 | GP1 | 470 Ω | row 1 |
| C0 | GP3 | 470 Ω | column 0 |
| C1 | GP4 | 470 Ω | column 1 |

Bank Aは`row - switch - diode A -> K - column`、Bank Bは`column - switch - diode A -> K - row`です。実装前後に無通電導通とダイオード極性を確認します。

### 実施項目

1. 電流上限を低く設定し、無押下時電流と3V3を記録する。
2. 8キーを1個ずつ押し、期待するHID keyだけが出ることを確認する。
3. Bank A/Bを含む2キー組合せを全数確認する。
4. `R0 -> C0 -> R1 -> C1`とreverseの3-key pathを作り、phantomがHIDへ出ないことを確認する。
5. 右側相当キーを押したまま4信号を同時に開放し、key-upが出て押下残りがないことを確認する。
6. 再接続後にUSB再列挙やMCU resetなしで全キーが戻ることを確認する。

### 記録テンプレート

| 項目 | 記録 |
| --- | --- |
| main / firmware commit | 未実施 |
| UF2 SHA-256 | 未実施 |
| RP2040 board / revision | 未実施 |
| diode / resistor lot | 未実施 |
| 電源 / current limit | 未実施 |
| 8 single keys | 未実施 |
| 2-key combinations | 未実施 |
| ghost paths | 未実施 |
| disconnect / reconnect | 未実施 |
| oscilloscope captures | 未実施 |

実測欄が埋まり、結果をcommitするまでIssue #10をcloseしません。


---

## NotebookLM入力とPCB発注readyチェックリスト

確認日: 2026-08-01

## 現在の判定

発注は **NOT READY** です。製造用`.kicad_pcb`がまだなく、Issue #10の2 × 2実配線とIssue #11の活線挿抜も未実施です。回路図、文書、CI、UF2が存在することを、Gerber生成可能または発注可能とは扱いません。

判定の正本は[`production/order-readiness.json`](../production/order-readiness.json)です。人がチェック欄だけを更新してreadyにするのではなく、対象commitと成果物pathを固定してから検査します。

```bash
make order-readiness
python3 scripts/check-order-readiness.py --json
python3 scripts/check-order-readiness.py --require-ready
```

通常の`make order-readiness`は未完項目を表示して成功します。発注直前だけ`--require-ready`を使い、blockerが1件でもあれば終了コード2で停止します。manifestの型、path、不整合は常に終了コード1です。

## NotebookLMへ入れるもの

1. `make notebooklm`を実行する。
2. `make validate`で、統合Markdownが生成元と一致することを確認する。
3. [`notebooklm/split-keyboard-hotplug-safety.md`](split-keyboard-hotplug-safety.md)をNotebookLMへファイルとして追加する。
4. [`notebooklm-sources.md`](../docs/notebooklm-sources.md)の一次資料を、サイト全体ではなく該当ページまたはPDF単位で追加する。
5. 統合Markdownに含めたADRを質問し、回答がADR本文と一次資料のどちらを根拠にしたか引用を確認する。
6. notebook名、所有アカウント、確認日、ソース数を非機密の範囲でIssue #12へ記録し、manifestの`notebook_created`と`citation_smoke_test`を更新する。

引用smoke testでは少なくとも次を質問します。

- なぜ中央8P8CへVCCを通さないのか。
- 470 Ωは何を制限し、何を保証しないのか。
- QMKテスト、ngspice、ERC/DRC、実機試験の証拠範囲はどう違うか。
- 初号機でRP2040-Zero、36キー、Choc v1を採用した理由は何か。
- 発注を止めている未完gateは何か。

回答が本資料にない安全性や医学的効果を断定した場合は合格にしません。

## 製造snapshotを固定する

- [ ] `design_ref`を発注対象main commitの完全な40桁SHAへ設定
- [ ] `pcb_path`を製造用`.kicad_pcb`へ設定
- [ ] schematic、PCB、footprint、firmwareの対応commitが同じか記録
- [ ] KiCad、KiBot、QMKの版またはcommitを記録
- [ ] 第三者symbol/footprint/3D modelの由来とライセンスを確認
- [ ] 発注候補fabの当日capabilityと見積設定を確認

価格、最小寸法、穴径、公差、表面処理などは変わり得るため、このリポジトリへ値を永久固定しません。見積時の画面またはPDFと確認日を発注記録へ添付します。

## ERC/DRCと出力前gate

- [ ] 最終回路図でERCを実行し、warningを1件ずつ説明
- [ ] 全footprintを実部品datasheetと照合
- [ ] PCB外形が閉じ、cutout、slot、NPTH/PTHが意図どおり
- [ ] zoneをrefillして最終DRCを0件にするか、例外理由を記録
- [ ] 8P8Cの`SPLIT ONLY / NO LAN`、pin 1/8 GND、pin 2–7 signalをsilkとnetlistで再確認
- [ ] 中央リンクに`VCC/5V/3V3/RAW`がないことをnegative CIでも再確認
- [ ] Issue #10の実配線matrix結果とIssue #11の活線挿抜結果を対象commitへ結び付ける

KiCad 10 CLIはGerberとdrillを出力できます。KiBotを採用する場合はGerber、Excellon、BOM、position、PDF、archiveを同じ設定から生成し、設定ファイルも版管理します。製造用PCBができるまでは、空のarchiveや仮Gerberを合格証拠として作りません。

## 製造ファイル

2層基板の最低限のviewer対象は次です。実際の発注先の当日要件を優先します。

- F.Cu / B.Cu
- F.Mask / B.Mask
- F.SilkS / B.SilkS
- Edge.Cuts
- Excellon PTH / NPTH drill
- drill map
- schematic PDF / PCB assembly PDF
- BOM（メーカー、注文型番、数量、代替、実装区分）
- SMT assemblyを使う場合だけposition/CPL

Gerberとdrillは同じsnapshotから生成して1つのZIPへまとめます。ZIPだけでなく展開後の各layerをKiCad GerbViewまたは独立viewerで確認します。

## Viewer確認

- [ ] Edge.Cutsが連続し、外形と内部cutoutが正しい
- [ ] drill、slot、NPTH/PTHがpadと一致
- [ ] copper、mask、silkの表裏とmirrorが正しい
- [ ] silkがpadやケース開口へ干渉しない
- [ ] switch/socket、RP2040-Zero、8P8C、TVS、抵抗の向きとcourtyardが正しい
- [ ] fab upload後のviewerをローカルviewerと照合
- [ ] 発注設定、数量、板厚、銅厚、表面処理、色、panelizationを記録

JLCPCBの公式手順はDRC後のGerber/Excellon生成と第三者viewer確認を求めています。KiCad版による画面差があるため、KiCad 10のCLI/PCB Editor文書も併読します。

## 発注後に残す証拠

- 発注日、fab、非機密のorder識別子
- `design_ref`とrelease tag
- Gerber ZIP、BOM、PDFのSHA-256
- KiCad/KiBot版とCI run URL
- viewer確認者と確認日
- fab側からの問い合わせ、置換、DFM変更
- 到着写真、無通電検査、初回通電結果へのlink

## 一次資料

- [KiCad 10 CLI: PCB export](https://docs.kicad.org/10.0/en/cli/cli.html)
- [KiCad 10 GerbView](https://docs.kicad.org/10.0/en/gerbview/gerbview.html)
- [KiBot configuration](https://kibot.readthedocs.io/en/latest/configuration.html)
- [KiBot Gerber output](https://kibot.readthedocs.io/en/latest/configuration/outputs/gerber.html)
- [KiBot drill output](https://kibot.readthedocs.io/en/latest/configuration/outputs/gerb_drill.html)
- [JLCPCB: Gerber and drill preparation](https://jlcpcb.com/help/article/gerber-files-preparation)
- [JLCPCB: KiCad Gerber/drill generation](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-7)
- [JLCPCB: KiCad 10 BOM and position files](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad)


---

## 2 × 2 breadboardでJapanese duplex matrixを試す

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


---

## Issue依存・証拠graph

確認日: 2026-08-01

## 目的

[公開graph](../docs/graph)は、設計判断、実装、検証、公開物を有向edgeで結び、現在止まっている理由を検索できるようにします。GitHub Pages上で完結し、追加サービス、CDN、外部JavaScript frameworkは使いません。

データの正本は[`project-graph.json`](../docs/graph/project-graph.json)、表示は[`index.html`](../docs/graph/index.html)と[`graph.js`](../docs/graph/graph.js)、検索・絞り込み規則は[`graph-model.mjs`](../docs/graph/graph-model.mjs)です。手書きの解説、表示、データ処理を分離し、自動処理がcuratedな関係を上書きしない構造にします。

## node

nodeは次を持ちます。

- `id`: 永続的な識別子
- `kind`: `issue`、`decision`、`artifact`、`evidence`、`release`、`gate`
- `status`: `verified`、`open`、`blocked`、`planned`
- `stage`: `decision`、`implementation`、`verification`、`publication`
- `url`: 詳細または証拠の公開URL
- `summary`: そのnodeが証明する範囲

`verified`はnodeの存在や記載済みの検査が確認済みという意味です。キーボード全体の安全性、人体適合、製造可能性を一括して保証しません。

## edge

edgeは向きに意味を持ちます。

| relation | 読み方 |
| --- | --- |
| `defines` | sourceの判断がtargetの構造を定義する |
| `implements` | sourceがtargetの判断を実装する |
| `validates` | sourceの証拠がtargetの限定された性質を検査する |
| `blocked_by` | sourceの完了がtargetの未完証拠で止まる |
| `depends_on` | sourceを成立させる前にtargetが必要 |
| `publishes` | sourceがtargetを公開する |
| `may_change` | sourceがtargetへ影響する可能性があるが未確定 |

全edgeに`confidence`と1件以上の`evidence`を要求します。

- `verified`: ADR、commit、Issue、CI、公開文書で関係を確認できる
- `inferred`: 設計上あり得るが、採用判断や実測がまだない

`inferred`を実線のverified edgeへ格上げする場合、先にADRまたはIssueへ根拠を残します。

## 発注blockerの読み方

`order-ready` nodeから`blocked_by`を辿ると、少なくとも次が未完です。

- Issue #10の2 × 2実配線
- Issue #11の活線挿抜
- Issue #12のNotebookLM引用smoke test
- 製造用PCBとGerber/BOM/viewer

CI successやv0.4.0 releaseは、それらの代用ではありません。

## 検査

```bash
make check-project-graph
python3 scripts/check-project-graph.py --self-test
```

検査はschema、enum、ID重複、dangling edge、self-loop、根拠URL、発注gateの必須blockerを確認します。Node.jsがある環境では、既定表示、issue status、relation、confidence、全文検索のmodel test 5件も実行します。表示側はJSONを読み取るだけで、状態を推測して書き換えません。

## 更新規則

1. 正本JSONへnodeまたはedgeを追加する。
2. verified edgeには公開根拠URLを付ける。
3. 推測なら`inferred`のまま注記と再検討条件を書く。
4. `make validate`を実行する。
5. Issueの解除条件とgraphのstatusが一致するか確認する。

未解決の関係を見つけてもgraph内だけで完了扱いせず、再現手順と解除条件をGitHub Issueへ追加します。


---

## 初号機36キーレイアウトと調整プロファイル

Issue [#5](https://github.com/hjosugi/electronics/issues/5)と[ADR 0002](../docs/adr/0002-use-36-key-choc-v1-layout.md)で、初号機の標準レイアウトを次のように固定しました。

| 項目 | 標準値 |
| --- | --- |
| キー数 | 36キー、片側`3行 × 5列 + 親指3キー` |
| スイッチ | Kailh PG1350（Choc v1） |
| ピッチ | 横18.00 mm、縦17.00 mm |
| column stagger | 外側から`18.00 / 6.00 / 0.00 / 6.62 / 9.00 mm` |
| column splay | 標準は全列0°、各列±3°以内で調整可能 |
| 親指クラスタ | 3キー、位置と角度を制限付きで調整可能 |
| ロータリーエンコーダ | 初号機には載せない |
| キー面 | 初号機は平面PCB。concave keywellは含めない |
| tenting | ケース側で0°、10°、20°を選べる設計目標 |

これは物理配置の基準です。QWERTYなどの論理キーマップ、Japanese duplex matrixの行列割り当て、GPIO、ダイオード極性はIssue #6と#10で別に確定します。

## Kinesisから取り入れる考え方

Kinesis Advantage2のメーカー資料は、左右を離すこと、指の自然な運動に沿う縦列、独立した親指クラスタ、20°のtenting、凹型keywellを主な特徴として説明しています。

初号機では、その考え方を次の境界で取り入れます。

- 左右を独立させ、机上で肩幅、yaw、前後位置を利用者が変えられる
- 各列は縦方向にそろえ、指長差はcolumn staggerで吸収する
- 親指3キーへSpace、Backspace、Enter、レイヤーなど高頻度機能を割り当てられる
- ケースの脚またはウェッジで0°、10°、20°のtentingを選べるようにする
- キー配置を生成プロファイル化し、紙面モックの結果を数値へ反映できる

一方、Kinesisのconcave keywellは、スイッチ面そのものを三次元に配置する構造です。単一の平面PCBへスイッチを実装する初号機では再現できません。keywellを有効にするには、分割小基板、フレキシブルPCB、手配線、または別体スイッチプレートを含む別アーキテクチャが必要です。平面PCBの合格を先取りせず、[Issue #16](https://github.com/hjosugi/electronics/issues/16)で扱います。

これらは医療上の効果や特定の利用者への適合を保証しません。痛みやしびれがある場合は、キーボードだけで解決しようとせず、休止、作業環境の見直し、必要に応じた専門家への相談を優先してください。

## 成果物

- [`profiles/balanced-kinesis-inspired.json`](../docs/layout/profiles/balanced-kinesis-inspired.json): 標準値と利用者が変更できる項目
- [`36-key-choc-v1.layout.json`](../docs/layout/36-key-choc-v1.layout.json): mm単位のスイッチ中心、キーID、机上調整値を含む製造設計用の正本
- [`36-key-choc-v1.kle.json`](../docs/layout/36-key-choc-v1.kle.json): [Keyboard Layout Editor](https://www.keyboard-layout-editor.com/)のRaw dataへ読み込むレビュー用JSON
- [`scripts/build-layout.py`](../scripts/build-layout.py): プロファイル検証とJSON生成

標準成果物の再生成と差分検査は次のとおりです。

```bash
make layout
make check-layout
```

KLEは正方形の抽象単位を使うため、このファイルではX軸1 unitを18 mm、Y軸1 unitを17 mmとして表示しています。回転したキーの製造座標には、KLE画面から測り直さず、必ず`.layout.json`のmm値を使います。

## 利用者が変更できる範囲

標準プロファイルを別名でコピーし、次の値だけを小さく変更できます。生成スクリプトは範囲外、キー不足、重複ID、キー中心間隔15.5 mm未満を拒否します。

| 設定 | 許容範囲 | 目的 |
| --- | --- | --- |
| C0 stagger | 10–22 mm | 小指列を手首側へ寄せる |
| C1 stagger | 2–10 mm | 薬指長に合わせる |
| C2 stagger | 0 mm固定 | Y座標の基準を維持する |
| C3 stagger | 2–10 mm | 人差し指列の到達を調整する |
| C4 stagger | 5–14 mm | 内側人差し指列の到達を調整する |
| 各列splay | -3–3° | 指の開きに合わせて列をわずかに回す |
| 親指キー位置 | 標準から概ね4–6 mm以内 | 親指長と可動域へ合わせる |
| 親指キー角度 | キーごとの制限内 | 無理な外転を避ける |
| 左右間隔 | 120–260 mm | 肩幅へ合わせる机上設定 |
| half yaw | 0–15° | 手首の尺屈を減らす机上設定 |
| 標準tent | 0°、10°、20°から選択 | 前腕回内へ合わせるケース設定 |

たとえば個人用プロファイルを作り、追跡対象外の一時ディレクトリへ生成します。

```bash
cp docs/layout/profiles/balanced-kinesis-inspired.json /tmp/my-keyboard-profile.json
python3 scripts/build-layout.py \
  --profile /tmp/my-keyboard-profile.json \
  --output-dir /tmp/my-keyboard-layout
```

ピッチ、キー数、スイッチ系統、平面PCBという前提は、このプロファイルでは変更できません。そこまで変える場合は、別設計として新しいADRと検証を必要とします。

## 片側の標準座標

片側ローカル座標は、C0中心のX=0とC2最上段中心のY=0が作る基準点を原点とし、Xは外側小指列から内側人差し指列、Yは指先側から手首側を正方向とします。右側は同じ形状を鏡像化します。

```text
C0  x= 0 mm  y=18.00, 35.00, 52.00
C1  x=18 mm  y= 6.00, 23.00, 40.00
C2  x=36 mm  y= 0.00, 17.00, 34.00
C3  x=54 mm  y= 6.62, 23.62, 40.62
C4  x=72 mm  y= 9.00, 26.00, 43.00
Thumb 0       (48.10, 60.59),   0 deg
Thumb 1       (68.15, 63.18), -15 deg
Thumb 2       (88.75, 66.39),  60 deg
```

column splayを変更すると、各列のhome row中心を軸に上下キーの中心座標も回転します。親指キーの番号は外側から内側です。

## 1:1フィット確認

PCB外形や配線を確定する前に、次を行います。

1. `.layout.json`から1:1の紙または仮プレートを出力する
2. 採用予定のChoc v1キーキャップを置き、隣接干渉を確認する
3. 手首を曲げずに小指3段と親指3キーを押せるか、左右それぞれ確認する
4. 左右間隔、yaw、tentを少なくとも2段階ずつ試し、値と所感を記録する
5. RP2040-Zero、8P8C、ケース壁の領域と干渉しないかKiCadで確認する
6. Kailhの最新図面と購入したスイッチ／ソケットを実測し、フットプリントを照合する

合わない場合は生成後のJSONを直接編集せず、プロファイルを変更します。許容範囲を超える変更は、新しいADRへ理由と実測結果を記録します。

## 一次資料

- [Kinesis Advantage2公式製品資料](https://kinesis-ergo.com/shop/advantage2/): concave keywell、左右分離、縦列、20° tenting、親指クラスタ
- [Kinesis Advantage2 User's Manual](https://kinesis-ergo.com/wp-content/uploads/Adv2-Users-Manual-2-16-18.pdf): 設計意図と姿勢、適応時の注意
- [Ergogen Points公式資料](https://docs.ergogen.xyz/points/): column stagger、spread、splay、thumb zoneのパラメータ化
- [Kailh PG1350シリーズ](https://www.kailhswitch.com/info/kailh-kl-switches-pg1350-series-23772219.html): Choc v1のメーカー型番と機械系統

## 由来とライセンス

標準のスイッチ中心座標は、Chocofiの[`pcb/chocofi-topplate.kicad_pcb`](https://github.com/pashutk/chocofi/blob/273676d11b06785fb5a1a94860a39fc36c38baba/pcb/chocofi-topplate.kicad_pcb)を基準に、原点の正規化、左右鏡像化、キーIDと制限付きプロファイルを追加しました。ChocofiはCERN-OHL-P-2.0です。変更表示は[第三者通知](../docs/layout/THIRD_PARTY_NOTICES.md)、ライセンス全文は[`LICENSE.CERN-OHL-P-2.0.txt`](../docs/layout/LICENSE.CERN-OHL-P-2.0.txt)を参照してください。

KLEのファイル形式は公式実装の[`serial.js`](https://github.com/ijprest/keyboard-layout-editor/blob/580b916084e69e600b2144b0217c8b1d9710daa0/serial.js)に合わせています。KLEのコード自体は複製していません。


---

## ADR 0001: 初号機はWaveshare RP2040-Zeroモジュールを使う

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


---

## ADR 0002: 初号機は調整可能な36キーChoc v1レイアウトとする

- 状態: Accepted
- 決定日: 2026-08-01
- 対応Issue: [#5](https://github.com/hjosugi/electronics/issues/5)
- 適用範囲: 初号機（v0.1）の左右キー配置とスイッチ機械系統

## 文脈

初号機のキー数、スイッチ系統、column stagger、ロータリーエンコーダの有無が未確定でした。この判断はPCB外形、キーマトリクス、GPIO数、キーキャップ、ソケット、ケース高さへ連鎖します。

固定された1種類の平面配置だけでは、指長、親指可動域、肩幅の違いへ対応できません。一方、無制限なパラメータ化は、キーキャップ干渉や未検証のフットプリントを簡単に生みます。Kinesis Advantageの人体工学上の考え方を参考にしつつ、初号機で安全に検証できる範囲と利用者が変えてよい範囲を分ける必要があります。

候補は次のとおりでした。

- 36キー（片側3×5+3）または42キー（片側3×6+3）
- Kailh Choc v1、Choc v2、MX
- Cheapinoに近い19 mm配置、Choc向けの狭い配置、独自stagger
- 固定座標、または制限付きの利用者プロファイル
- 右側ロータリーエンコーダあり、またはなし
- 平面PCB、またはKinesisに近いconcave keywell

## 決定

初号機は次に固定します。

1. 合計36キー、片側`3行 × 5列 + 親指3キー`
2. Kailh PG1350（Choc v1）系統
3. 基準ピッチは横18.00 mm、縦17.00 mm
4. 標準column staggerは外側から`18.00 / 6.00 / 0.00 / 6.62 / 9.00 mm`
5. Kinesisの縦列と親指分担を取り入れ、標準column splayは0°とする
6. column stagger、各列±3°以内のsplay、親指位置、左右間隔、yaw、tent段階を制限付きJSONプロファイルで変更可能にする
7. ロータリーエンコーダは載せない
8. 初号機は単一平面PCBとし、concave keywellは別アーキテクチャとして扱う

標準プロファイル、許容範囲、mm単位の正本は[レイアウト仕様](../docs/layout/README.md)に記録します。

初期購入候補は、Kailh公式がChoc Redとして掲載する`CPG135001D01`、ホットスワップ接点は`CPG135001S30`です。発注番号とフットプリントはIssue #6でメーカーの最新図面と購入実物を照合してから確定し、このADRだけを根拠に発注しません。

## 根拠

### 36キーで初号機の検証範囲を絞る

36キーは、42キーよりスイッチ、ダイオード、配線、ケース開口を6個減らせます。1 MCUと右側完全パッシブ方式の初号機では、キー数を増やすことより、Japanese duplex matrix、8P8C保護、抜線時の入力状態を切り分けられることを優先します。

物理キーが少ないため、数字、記号、ナビゲーションはレイヤーが必要です。これはQMKの論理配列を決めるIssue #10で実機評価します。

### Choc v1で薄型化し、機械系統を限定する

Kailh公式はPG1350を15×15 mmの低背スイッチとして説明し、MX用キーキャップやPCBとは互換でないと明記しています。[PG1350シリーズ一覧](https://www.kailhswitch.com/info/kailh-kl-switches-pg1350-series-23772219.html)にはRed `CPG135001D01`、Brown `CPG135001D02`、White `CPG135001D03`が掲載されています。

初号機ではMXとの複合フットプリントやChoc v2との兼用を要件にせず、PG1350用の穴、接点、キーキャップ間隔へ設計範囲を限定します。低背化はケース高さを減らせますが、スイッチ上面から基板までの総高さはキーキャップ、プレート、ソケット、PCB厚を含めて別途積み上げます。

### Kinesisの原則を平面分割キーボードへ適用する

[Kinesis Advantage2公式資料](https://kinesis-ergo.com/shop/advantage2/)は、左右を離したkeywell、指の自然な運動に沿う縦列、強い親指への高頻度キー移動、20° tenting、凹型keywellを特徴として説明しています。

初号機は物理的に左右が分かれているため、肩幅に応じた左右間隔とyawを机上で変更できます。縦列を標準にし、指長差はcolumn staggerで吸収します。独立した親指3キーは、Space、Backspace、Enter、レイヤーなどをQMKで割り当てる余地を作ります。ケース側には0°、10°、20°の段階的tentingを要求します。

ただし、これらを採用しても人体への適合や医療上の効果は保証できません。紙面モック、実機、作業姿勢を利用者ごとに確認します。

### 調整範囲を機械検査する

[Ergogenの公式Points資料](https://docs.ergogen.xyz/points/)は、列ごとの`stagger`、`spread`、`splay`と、matrixから独立したthumb zoneを定義する方法を説明しています。この考え方を、外部依存のないJSON生成スクリプトへ限定的に取り入れます。

利用者はstagger、±3°以内のsplay、親指位置、机上の左右間隔、yaw、標準tent段階を変更できます。スクリプトは値域、36キー、左右18キー、3×5+3、キーID、最小中心間隔を検査し、生成後JSONの手修正を不要にします。

ピッチ、キー数、Choc v1、平面PCB、中央接続の電気方式はプロファイルで変更できません。これらは別の検証とADRを必要とします。

### Chocofiの同一キー構成を標準値にする

[Chocofi](https://github.com/pashutk/chocofi/tree/273676d11b06785fb5a1a94860a39fc36c38baba)は36キー、片側3×5+3、Choc向け、強めの小指staggerを持つ公開ハードウェアです。初号機と同じ物理キー構成で実物写真、トッププレート、ケースがそろっているため、未検証の独自配置をゼロから作るより明確な標準値になります。

トッププレートのスイッチ中心から、横18 mm、縦17 mmと各列のY位置を読み取り、原点を正規化して左右鏡像へ展開しました。元ファイルをそのまま複製せず、MCU、電池、TRRS、基板外形、配線は採用しません。幾何データの由来、変更内容、CERN-OHL-P-2.0は[第三者通知](../docs/layout/THIRD_PARTY_NOTICES.md)に記録します。

Cheapinoは、公式ビルドガイドで19.00 mm間隔を使うと説明していますが、現行設計はMXスイッチです。1 MCU、8P8C、Japanese duplex matrixの電気アーキテクチャは引き続き参考にしますが、Choc v1を選ぶ今回の物理ピッチにはその19 mm値を流用しません。

### concave keywellを初号機へ含めない

Kinesisのkeywellは、キー面を三次元に配置して指の伸展を抑える構造です。単一平面PCBに直接実装するスイッチを設定値だけで凹型にすることはできません。

分割小基板、フレキシブルPCB、手配線、または別体プレートのいずれかを先に選ばず形だけを模倣すると、配線、実装、ケース公差の問題が増えます。初号機では平面PCBと調整式tentingを検証し、true keywellは[Issue #16](https://github.com/hjosugi/electronics/issues/16)へ分離します。

### エンコーダを初号機から外す

ロータリーエンコーダは、追加GPIO、機械固定、ケース開口、ノブ高さ、回転入力のデバウンス評価を増やします。音量やスクロールは一旦キーとレイヤーへ割り当て、1 MCU・パッシブ右側・活線挿抜評価の完成を優先します。

## 影響

### 利点

- 同一スイッチ、1uキーだけでBOMとプレートを単純化できる
- 42キーよりマトリクスとケースの検証対象が少ない
- Choc v1向けの狭いピッチで左右幅を抑えられる
- 縦列、親指分担、分離、tentingという原則を初号機へ段階的に適用できる
- 利用者は検査された範囲で指長、親指、肩幅へ合わせられる
- Chocofiの実装を比較対象にして標準座標をレビューできる

### 欠点

- 36キーではレイヤー操作を覚える必要がある
- Choc v1とMXのキーキャップ、PCB、プレートを共用できない
- 強い小指staggerと親指角度が全員の手に合うとは限らない
- 平面PCBはKinesisのconcave keywellを再現しない
- プロファイルごとに1:1モックと干渉確認が必要になる
- エンコーダを後付けするにはPCBとケースの再設計が必要になる

## 採用しなかった案

### 42キー、片側3×6+3

専用レイヤーへの依存は減りますが、初号機の部品、配線、外形を増やします。36キーの実機評価で不足が確認された場合に再検討します。

### MX、19 mm級ピッチ

キーキャップとスイッチの選択肢は広い一方、初号機を低背化する要望と合いません。Cheapinoの電気方式を参考にすることと、MX機械系統を採用することは分けて判断します。

### Choc v2または複合フットプリント

対応部品は増えますが、穴、接点、キーキャップ干渉、配線領域の検証組み合わせも増えます。初号機ではChoc v1に限定します。

### 固定座標だけを公開する

再現性は高い一方、手の違いを生成元へ反映できず、生成後JSONの直接編集を招きます。標準値を維持しながら、制限付きプロファイルを正規の変更経路にします。

### 初号機からconcave keywellを作る

人体工学上は魅力がありますが、単一平面PCBと両立しません。電気設計と三次元スイッチ実装を同時に初回検証しない方針とします。

### ロータリーエンコーダあり

音量操作には便利ですが、必須入力ではありません。キーボード本体が合格した後の別リビジョンで扱います。

## 実装条件

1. 標準値は[`balanced-kinesis-inspired.json`](../docs/layout/profiles/balanced-kinesis-inspired.json)へ保存する
2. mm単位の正本は[`36-key-choc-v1.layout.json`](../docs/layout/36-key-choc-v1.layout.json)とし、KLEから製造寸法を逆算しない
3. `make check-layout`で36キー、左右18キー、3×5+3、値域、最小中心間隔、生成物同期を検査する
4. PCB化前に1:1紙面または仮プレートで小指と親指の到達性を確認する
5. 左右間隔、yaw、tentを変えた結果を利用者プロファイルと実測記録へ残す
6. Kailhの最新スイッチ／ソケット図面と購入実物を照合してからフットプリントを確定する
7. matrix、GPIO、ダイオード、8P8C信号はIssue #6と#7で別に決める
8. 中央8P8Cへ`VCC/5V/3V3/RAW`を追加しない

## 再検討条件

次のいずれかが成立した場合、新しいADRで置き換えます。

- 許容範囲内の1:1モックで小指または親指キーに無理なく届かない
- 購入するChoc v1キーキャップが18×17 mm配置で干渉する
- 36キーでは必要操作を実用的なレイヤーへ割り当てられない
- concave keywellの実装方式と検証計画が確定する
- エンコーダが必須となる具体的なユースケースが確定する
- Choc v1スイッチ、ソケット、キーキャップを継続調達できない
- ケース高さや実装制約が低背化の目的を満たさない


---

## ADR 0003: 右matrix信号へ470 Ωと両端TVSを使う

- 状態: Accepted
- 決定日: 2026-08-01
- 対象: 初号機36キー、1 MCU、右側パッシブ、8P8C中央接続

## 文脈

中央ケーブルへ電源を出さなくても、活線挿抜や誤配線ではGPIO–GND、GPIO同士、ESDの経路が残ります。
直列抵抗を大きくすると故障電流は減りますが、ケーブル容量と入力容量に対するsettlingは遅くなります。
TVSはESD電流をGNDへ逃がしますが、容量、クランプ電圧、GND配線が信号とMCUストレスへ影響します。

## 決定

初号機の中央へ出る6信号すべてに、MCU側でPanasonic `ERJ3EKF4700V`（470 Ω、1%、0603、0.1 W）を入れます。
左右の8P8C直後にはTI `TPD4E05U06DQA`を2個ずつ、合計4個置き、6信号を各コネクタ位置でGNDへクランプします。

firmwareの初期条件は次とします。

- GPIO drive strength: 2 mA
- slew: slow
- 走査相を変える前に、出力だった全線を入力へ戻す
- driveは1本ずつ、sampleまで1 µs以上待つ

これらはIssue #10でQMKへ実装し、実機波形で再確認します。

## 根拠

比較用モデルでは、2 mケーブルを120 pF、RP2040のI/O timing試験条件にあるnominal loadを5 pF、
左右TVSを合計1 pF、
接点/ケーブルを1 Ω、GPIO出力抵抗を仮の25 Ωとしました。

| 候補 | 10–90% rise | 閉キーLOW | 3.3 V signal–GND故障電流 | 判断 |
| ---: | ---: | ---: | ---: | --- |
| 220 Ω | 68.75 ns | 0.4928 V | 13.47 mA | 故障電流が大きい |
| 330 Ω | 99.93 ns | 0.5048 V | 9.294 mA | timingは十分だが6線短絡モデルが50 mAを超える |
| 470 Ω | 140.00 ns | 0.5199 V | 6.666 mA | 採用 |

閉キーLOWモデルは実配線どおり、drive側とsense側の両方に候補抵抗を入れています。
470 ΩでもLOWはRP2040のVIL 0.8 V未満、HIGHはVIH 2.0 V超、riseは140 nsで、
1 µsのsettlingに対して約7倍の時間余裕があります。単線短絡は6.666 mA、6線が個別にGNDへ
短絡する仮定モデルの合計は39.996 mAで、50 mAの全GPIO source上限を下回ります。
0.1 W抵抗に対し、3.3 Vの定常短絡でモデル上約20.9 mWです。

この合計値は25 Ωの仮定、3.3 V、他のGPIO負荷なしという条件に限られます。50 mAへ約10 mAしか
残らず、RP2040の出力段や抵抗の許容差を保証する解析でもないため、6線短絡への耐性は主張しません。

TPD4E05U06DQAは5.5 V VRWM、4 channel、0.5 pF typical/channelであり、
6本を4 channel品2個で覆えます。コネクタ両端へ置くのは、ESD侵入口からクランプまでを短くし、
切り離された右基板側にも入口保護を残すためです。

## 安全性の限定

この決定は次を保証しません。

- RP2040のdrive strength設定は電流リミッタではない
- 470 Ωの単線・6線モデル値はGPIOの無損傷保証ではない
- 任意の複数線短絡や他GPIO負荷ではRP2040の全I/O 50 mA上限を超え得る
- TVSのIEC定格は完成基板のIEC合格ではない
- 24/48 VのPoE誤給電では470 Ωが約1.23/4.90 Wを消費し得るため保護不能
- 抜線後の押下残り、再接続、USB再列挙はfirmwareと実機の課題

したがって8P8Cは`SPLIT ONLY / NO LAN`、専用ストレートケーブル、Ethernet/PoE接続禁止を必須条件とします。

## 代替案

### 220 Ω

riseは最短ですが、故障電流がモデル上13 mAを超えるため採用しません。

### 330 Ω

470 Ωよりriseは約40 ns短い一方、単線故障電流は約39%大きく、6線短絡の仮定合計が50 mAを超えます。
今回の1 µs settling条件では速度差を優先する根拠がないため採用しません。

### TVSをMCU側だけに置く

部品数は減りますが、右基板単体と右コネクタ直後の放電経路がなくなるため採用しません。

### 8P8Cをやめる

PoE環境で取り違えを管理できない場合の推奨です。物理的に非互換なロック付き8極以上のコネクタを選び、
このADRを置き換えます。

## 再検討条件

- 実ケーブルLCR測定が120 pF/1 Ωモデルから大きく外れる
- QMK走査で1 µs settlingを確保できない
- 470 ΩでVIL 0.8 V以下、VIH 2.0 V以上を実測できない
- IEC 61000-4-2試験または接触放電でリセット、誤キー、損傷が起きる
- コネクタ周辺のGND returnを短く実装できない
- 利用環境でLAN/PoEとの取り違えを管理できない

詳細な回路、pinout、部品、故障分析は
[36キーJapanese duplex matrixと8P8C保護回路](../docs/13-matrix-rj45-safety.md)を参照します。
