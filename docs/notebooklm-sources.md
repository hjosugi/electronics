# NotebookLM ソースリスト

## 一次資料 (実装リファレンス)
- https://github.com/tompi/cheapino — 1 MCU + RJ45 + Japanese duplex matrix の参考実装 (36 キー, RP2040-Zero, 19.00mm ピッチ)
- https://github.com/tompi/cheapino/blob/master/doc/firmware.md — firmware は本家 QMK 未マージ。tompi/qmk_firmware の cheapino branch を参照
- https://github.com/pashutk/chocofi/tree/273676d11b06785fb5a1a94860a39fc36c38baba — 36キー、Choc、3x5+3、強い小指staggerの物理配置基準
- https://kinesis-ergo.com/shop/advantage2/ — 左右分離、縦列、親指クラスタ、20° tenting、concave keywellのメーカー説明
- https://docs.ergogen.xyz/points/ — stagger、spread、splay、thumb zoneの公式パラメータ資料
- https://github.com/ijprest/keyboard-layout-editor/blob/580b916084e69e600b2144b0217c8b1d9710daa0/serial.js — KLE serialized dataの公式実装
- https://github.com/satt99/caravelle-build-guide — 無線分割 (中央ケーブルを無くす方向) の設計思想
- https://github.com/sekigon-gonnoc/auto-kdk — 自動生成系。誤った USB 接続による破損警告も反面教師として

## ドキュメント
- https://docs.qmk.fm/ — custom matrix、RP2040 対応のページを個別追加
- https://docs.qmk.fm/custom_matrix — COL2ROW/ROW2COL併用matrixのcustom scan
- https://docs.kicad.org/ — KiCad 10 マニュアル (特にシミュレータ章)
- https://kibot.readthedocs.io/ — CI での出力自動化
- サリチル酸ブログ「自作キーボード温泉街の歩き方」 — 設計ノウハウ / ビルドガイドカテゴリから該当記事を個別 URL で追加

## データシート (PDF をダウンロードして追加)
- https://www.kailhswitch.com/info/kailh-kl-switches-pg1350-series-23772219.html — Choc v1 PG1350のメーカー型番一覧
- https://www.kailhswitch.com/uploads/15927/files/CPG135001S30.pdf — Choc v1ホットスワップ接点CPG135001S30のメーカー図面
- https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf — GPIO閾値、pull、drive、合計電流
- https://files.waveshare.com/upload/4/4c/RP2040_Zero.pdf — RP2040-Zero回路図とpinout
- https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf — 採用TVS TPD4E05U06DQA
- https://industrial.panasonic.com/ww/products/pt/general-purpose-chip-resistors/models/ERJ3EKF4700V — 採用470 Ω
- https://www.diodes.com/datasheet/download/1N4148W.pdf — 採用matrix diode 1N4148W-7-F
- https://catalog.belden.com/techdata/EN/1583E_techdata.pdf — 2 m cable R/Cモデルの根拠
- https://ethernetalliance.org/wp-content/uploads/2018/04/WP_EA_Overview8023bt_FINAL.pdf — IEEE PoE detection
- https://dl.ui.com/qsg/EP-24V-72W/EP-24V-72W_EN.html — 24 V passive PoEの実例
- (将来 USB-C 中央接続に進む場合) TI TUSB320, TPS2553

## 運用メモ
- ブログや docs はサイト丸ごとではなく記事・章単位で追加すると引用精度が上がる
- docs/adr/ の設計判断 md もソース登録し、自分の過去の決定を検索可能にする
