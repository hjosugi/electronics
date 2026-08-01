# 初号機36キーレイアウトと調整プロファイル

Issue [#5](https://github.com/hjosugi/electronics/issues/5)と[ADR 0002](../adr/0002-use-36-key-choc-v1-layout.md)で、初号機の標準レイアウトを次のように固定しました。

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

- [`profiles/balanced-kinesis-inspired.json`](profiles/balanced-kinesis-inspired.json): 標準値と利用者が変更できる項目
- [`36-key-choc-v1.layout.json`](36-key-choc-v1.layout.json): mm単位のスイッチ中心、キーID、机上調整値を含む製造設計用の正本
- [`36-key-choc-v1.kle.json`](36-key-choc-v1.kle.json): [Keyboard Layout Editor](https://www.keyboard-layout-editor.com/)のRaw dataへ読み込むレビュー用JSON
- [`scripts/build-layout.py`](../../scripts/build-layout.py): プロファイル検証とJSON生成

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

標準のスイッチ中心座標は、Chocofiの[`pcb/chocofi-topplate.kicad_pcb`](https://github.com/pashutk/chocofi/blob/273676d11b06785fb5a1a94860a39fc36c38baba/pcb/chocofi-topplate.kicad_pcb)を基準に、原点の正規化、左右鏡像化、キーIDと制限付きプロファイルを追加しました。ChocofiはCERN-OHL-P-2.0です。変更表示は[第三者通知](THIRD_PARTY_NOTICES.md)、ライセンス全文は[`LICENSE.CERN-OHL-P-2.0.txt`](LICENSE.CERN-OHL-P-2.0.txt)を参照してください。

KLEのファイル形式は公式実装の[`serial.js`](https://github.com/ijprest/keyboard-layout-editor/blob/580b916084e69e600b2144b0217c8b1d9710daa0/serial.js)に合わせています。KLEのコード自体は複製していません。
