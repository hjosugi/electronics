# Changelog

## Unreleased

- Kinesisの原則を取り入れた36キー・Choc v1の調整可能レイアウトADRを追加
- mm単位の正本JSON、KLE JSON、制限付きプロファイル、再生成・不変条件検証を追加
- concave keywellと0°/10°/20° tentingを実機比較する追跡Issueを追加
- ドキュメントページとCSS変数ベースのタイポグラフィ検証を追加
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
