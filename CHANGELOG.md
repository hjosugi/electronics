# Changelog

## Unreleased

- RP2040-Zero向け36キーJapanese duplex custom matrixと初期keymapを追加
- QMK本体をcommit SHAへ固定し、ローカル/CIのUF2再現ビルドを追加
- QMK lint、GPIO/論理matrix静的検査、GPL-2.0-or-later通知を追加
- 全36位置、抜線、方向安全性、ghost経路を検査するQMK GoogleTestを追加
- 曖昧な交互ダイオード経路を半分単位で保留する保守的ghost filterを追加

## 0.2.0 - 2026-08-01

- 36キーJapanese duplex matrix、GPIO0–11、ダイオード極性をKiCad 10参照回路へ実装
- 中央8P8CをGND 2本 + 信号6本に固定し、電源netを構造検査で禁止
- 6本のPanasonic ERJ3EKF4700V（470 Ω）と左右両端のTI TPD4E05U06DQAを採用
- 220/330/470 Ωのrise、HIGH/LOW、故障電流と24/48 V誤給電境界をngspiceで比較
- KiCad XML netlist検査とVBUS/抵抗値のnegative testをhardware validationへ追加
- matrix mapping、部品型番、crossover/LAN/PoE故障分析、安全性の限界を文書化
- ADR 0003とNotebookLM統合Markdownを追加

- Kinesisの原則を取り入れた36キー・Choc v1の調整可能レイアウトADRを追加
- mm単位の正本JSON、KLE JSON、制限付きプロファイル、再生成・不変条件検証を追加
- concave keywellと0°/10°/20° tentingを実機比較する追跡Issueを追加
- ドキュメントページとCSS変数ベースのタイポグラフィ検証を追加
- `docs/`をGitHub Pagesへ公開するActions workflowを追加
- KiCad 10.0.xの版確認、空回路ERC、RC過渡解析を再現する環境スモークテストを追加
- `hardware-ci`を実ファイルに対するERC/DRC violationで失敗する構成へ更新
- ERC/DRC violation fixtureと終了コード5を確認するnegative testを追加
- 初号機へWaveshare RP2040-Zeroを採用する判断をADRへ記録
- CachyOS向けの環境診断と、KiCad/ngspice/QMKの確認済み導入手順を追加
- 独立した検証とSPICE回路を並列化し、CIの重複実行を自動キャンセル

## 0.1.0 - 2026-08-01

- 1 MCU、8P8C、右側完全パッシブ方式の設計方針を文書化
- コネクタ方式、SPICEシミュレーション、実機検証の資料を追加
- 教育用ngspiceモデル3本を追加
- ngspice 45での基準測定値とNotebookLM統合Markdownを追加
- 12件の開発Issue定義と冪等な登録スクリプトを追加
- スターター検証と将来のKiCad ERC/DRC向けCIを追加

この版には製造可能なKiCad基板とQMKファームウェアは含まれません。
