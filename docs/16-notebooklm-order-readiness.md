# NotebookLM入力とPCB発注readyチェックリスト

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
3. [`notebooklm/split-keyboard-hotplug-safety.md`](../notebooklm/split-keyboard-hotplug-safety.md)をNotebookLMへファイルとして追加する。
4. [`notebooklm-sources.md`](notebooklm-sources.md)の一次資料を、サイト全体ではなく該当ページまたはPDF単位で追加する。
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
