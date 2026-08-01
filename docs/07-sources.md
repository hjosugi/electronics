# 一次資料と更新日

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
