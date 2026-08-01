# 実装ロードマップとIssue完了条件

## なぜIssueへ分けるのか

現在のリポジトリは、方式選定と検証方法をまとめたスターターです。製造可能なKiCad基板やQMKファームウェアがまだないため、「文書が丁寧だから完成」とは扱いません。

未完成作業は[GitHub Issues](https://github.com/hjosugi/electronics/issues)と[`issues/`](../issues/)の原稿で追跡します。各Issueには、背景、作業、客観的な完了条件があります。

## フェーズ0: 公開基盤

| Issue | 目的 | 完了の証拠 |
| --- | --- | --- |
| 01 KiCad環境 | KiCad 10とngspiceを同じ環境で使う | ERCとRC過渡解析の実行記録 |
| 02 QMK環境 | RP2040用QMKを再現ビルドする | 自作keyboard定義のUF2 |
| 03 repo初期化 | 文書、SPICE、CI、Issueを公開する | main SHA、PUBLIC読戻し、Issue一覧 |
| 04 ERC/DRC CI | 回路変更ごとの機械検査 | 意図的violationでCIが失敗する証拠 |

Issue 01は[PR #13](https://github.com/hjosugi/electronics/pull/13)で空回路ERCとRC過渡解析を確認済みですが、ホスト上のKiCad GUI確認が残っています。Issue 03は初回公開とIssue登録を確認済みです。Issue 02はローカルUF2、Issue 04は意図的violationでCIが失敗する証拠がそろうまで完了扱いにしません。

## フェーズ1: 要件と回路

| Issue | 決めること | 主な成果物 |
| --- | --- | --- |
| 05 要件 | 36/42キー、スイッチ、ピッチ、stagger | レイアウトJSON、ADR |
| 06 matrix | 行列サイズ、ダイオード極性、GPIO | 回路図、割当表、ERC結果 |
| 07 8P8C保護 | pinout、直列R、TVS、禁止接続 | BOM候補、pinout、故障分析 |
| 08 MCU | RP2040-Zeroか素RP2040か | 選定ADR |

このフェーズでは、部品名だけでなく正確な注文型番、データシート改訂、シンボル/フットプリントの由来を記録します。Issue 05の要件が決まるまで、製造用配線を確定しません。

Issue 08では、初号機にWaveshare RP2040-Zeroモジュールを採用する判断を[ADR 0001](https://github.com/hjosugi/electronics/blob/main/docs/adr/0001-use-waveshare-rp2040-zero.md)へ記録しました。GPIO割り当て、保護回路、QMK設定の合格を先取りする決定ではありません。

## フェーズ2: シミュレーションとファームウェア

| Issue | 検証 | 合格の考え方 |
| --- | --- | --- |
| 09 protection | R/L/C、直列抵抗、TVS、GPIO閾値 | 候補値の根拠と感度解析 |
| 10 firmware | Japanese duplex走査、抜線、ghosting | QMK自動テスト + 2 × 2実機 |

SPICEとQMKテストは別の証拠です。SPICEは電圧・電流を検証し、QMKテストはキー状態を検証します。片方の合格で他方を省略しません。

## フェーズ3: 実基板

Issue 11では、電流制限付き電源と専用治具を使って活線挿抜を評価します。

- 通常挿抜100回
- 供給電流、3V3、代表GPIOの観測
- 誤入力、押下残り、USB再列挙の確認
- 基板SHA、firmware SHA、ケーブル、測定器の記録

PCのUSBポート、Ethernetスイッチ、PoE機器を故障注入用には使いません。誤接続は机上解析、無通電導通、保護した治具で評価します。

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
