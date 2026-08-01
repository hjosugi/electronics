# Third-party notices for the layout geometry

## Chocofi

- Upstream: <https://github.com/pashutk/chocofi>
- Source commit: `273676d11b06785fb5a1a94860a39fc36c38baba`
- Source file: `pcb/chocofi-topplate.kicad_pcb`
- Upstream license: CERN Open Hardware Licence Version 2 - Permissive（CERN-OHL-P-2.0）
- Upstream copyright: Chocofi contributors

このリポジトリの`36-key-choc-v1.layout.json`、`36-key-choc-v1.kle.json`、`profiles/balanced-kinesis-inspired.json`、`scripts/build-layout.py`は、上記ファイルのスイッチ中心座標を基準にしています。

2026-08-01にhjosugi/electronics向けとして、次の変更を行いました。

- 座標原点を片側ローカル座標へ正規化
- 同じ形状から左右鏡像の36キーを生成
- キーID、ゾーン、行列インデックスを追加
- Kinesisの縦列、独立親指クラスタ、調整式tentingという設計原則を文書化
- column splay、親指位置、机上フィット値を制限付きプロファイル化
- KLEレビュー用データを追加
- MCU、電池、TRRS、PCB外形、配線、フットプリントは取り込まず、別設計とした

これらの派生成果物はCERN-OHL-P-2.0で提供します。ライセンス全文は[`LICENSE.CERN-OHL-P-2.0.txt`](LICENSE.CERN-OHL-P-2.0.txt)にあります。リポジトリ内のその他の独自文書、スクリプト、SPICEモデルには、特記がない限りルートのMIT Licenseが適用されます。
