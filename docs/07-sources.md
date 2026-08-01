# 一次資料と更新日

確認日: 2026-07-31

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

## 参考キーボード

- [tompi/cheapino](https://github.com/tompi/cheapino)
  1 MCU、8P8C、Japanese duplex matrixの公開作例。
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

## USB-Cと保護部品

- [USB-IF: USB Type-C Cable and Connector Specification Release 2.5](https://usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-25)
  2026年4月8日公開のType-Cケーブル・コネクタ仕様。
- [TI: TUSB320](https://www.ti.com/lit/ds/symlink/tusb320.pdf)
  CC attach、向き、DFP/UFP/DRPの検出と制御。
- [TI: TPS2552/TPS2553](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf)
  電流制限、逆電圧保護、FAULT、遅延時間。
- [TI: TPD2EUSB30A](https://www.ti.com/product/TPD2EUSB30A)
  2チャネル、3.6 V `VRWM`、低容量ESD保護の選定例。

## 本資料で行った訂正と限定

- `TPS2553 = 逆流を即時遮断`とは書かない。逆電圧検出には代表4 msの遅延がある。
- `RP2040でPIO full-duplexが使える = USB-C電源が安全`とは扱わない。
- `8P8Cに電源がない = ESDやPoE誤接続にも安全`とは扱わない。
- `330 Ωなら常に安全`とは扱わない。MCU定格と信号閾値で再評価する。
- `KiCadシミュレーション成功 = 製造可能`とは扱わない。ERC、DRC、導通、実測を別に行う。
