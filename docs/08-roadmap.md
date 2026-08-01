# 実装ロードマップとIssue完了条件

## なぜIssueへ分けるのか

現在のリポジトリには参照回路と初期QMK定義がありますが、製造可能なPCBと実機評価はまだありません。「文書やCIが丁寧だから完成」とは扱いません。

未完成作業は[GitHub Issues](https://github.com/hjosugi/electronics/issues)と[`issues/`](../issues/)の原稿で追跡します。各Issueには、背景、作業、客観的な完了条件があります。

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

Issue 05では、初号機を36キー、Kailh Choc v1、Chocofi基準の18×17 mm配置、エンコーダなしとする判断を[ADR 0002](adr/0002-use-36-key-choc-v1-layout.md)へ記録しました。Kinesisの縦列、独立親指クラスタ、分離、段階的tentingという原則を取り入れ、stagger、splay、親指位置、机上フィット値を[制限付きプロファイル](layout/profiles/balanced-kinesis-inspired.json)から生成します。人体適合、キーキャップ干渉、フットプリント、concave keywellは実機で未検証であり、後続Issueで確認します。

Issue 06、07、09では、36キーduplex matrix、GPIO0–11、中央8P8Cの`GND x2 + signal x6`、
470 Ω、両端TPD4E05U06DQAを[回路・安全性文書](13-matrix-rj45-safety.md)と
[ADR 0003](adr/0003-use-470-ohm-and-dual-ended-tvs.md)へ確定しました。KiCad 10 ERCとnetlist構造検査、
ngspice感度解析は合格済みです。これはPCB、QMK、活線挿抜、IEC ESDの完了を先取りしません。

## フェーズ2: シミュレーションとファームウェア

| Issue | 検証 | 合格の考え方 |
| --- | --- | --- |
| 09 protection | R/L/C、直列抵抗、TVS、GPIO閾値 | 候補値の根拠と感度解析 |
| 10 firmware | Japanese duplex走査、抜線、ghosting | QMK自動テスト + 2 × 2実機 |

Issue 02では、RP2040用の初期36キー定義、固定QMK commit、ローカルUF2、CI artifactを[ファームウェア環境](14-qmk-firmware.md)へ記録します。これはIssue 10の同時押し、抜線、ghosting、2 × 2実機検証を先取りしません。

Issue 10の自動部分では、全36位置、方向切替、右側抜線、ideal-diode ghost pathを[QMK matrixテスト](15-qmk-matrix-tests.md)で検査します。曖昧な半分は前状態へ保留しますが、2 × 2実配線が未実施なのでIssueはopenのままです。

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
