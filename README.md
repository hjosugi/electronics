# electronics: split keyboard starter

通電中でも中央ケーブルを抜き差ししやすい、有線分割キーボードを設計するためのOSSスターターです。

初号機の設計目標は、`1 MCU + 8P8C（通称RJ45）+ 右側完全パッシブ`です。中央ケーブルへVCCを流さず、TRRSで問題になる挿抜中のVCC–GND短絡経路を構造的に除きます。

> [!WARNING]
> このリポジトリは調査資料、SPICEモデル、開発Issueをまとめた設計開始点です。製造可能なKiCad基板や完成済みファームウェアではなく、活線挿抜、ESD、誤配線、PoE誤接続への安全性も実機では未検証です。PCのUSBポートを故意に短絡する試験には使用しないでください。

## 現在の成果物

- 36/42キー向けJapanese duplex matrixと8P8Cピン割り当て案
- Kinesisの原則を取り入れた、調整可能な36キー・Choc v1レイアウト
- TRRS、8P8C、USB-C、無線方式の比較
- GPIO直列抵抗、TRRS相当短絡、接点バウンスの教育用ngspiceモデル
- KiCadから実機評価までの安全チェックリスト
- GitHubへ登録する13件のIssue定義と冪等な登録スクリプト
- KiCad ERC/DRC用とスターター検証用のGitHub Actions

## 推奨アーキテクチャ

```text
PC ─ USB ─ 左側RP2040 ─ 直列抵抗 ─ 8P8Cケーブル ─ 右側スイッチ/ダイオード
                                             GND + matrix信号のみ
                                             VCC/5V/3V3/RAWなし
```

右側にRGB、OLED、トラックボール、MCUなどの能動部品を載せる場合は、この前提を利用できません。電源スイッチ、逆流、ESD、通信、電源順序を含む別設計が必要です。

## 読む順番

1. [要件、結論、安全性の境界](docs/00-overview.md)
2. [1 MCU + パッシブ右手 + 8P8C](docs/01-passive-rj45-design.md)
3. [コネクタ方式の比較](docs/02-connector-options.md)
4. [OSS回路シミュレーション手順](docs/03-simulation-guide.md)
5. [付属ngspice回路の解説](docs/04-spice-models.md)
6. [基板化と実機検証のチェックリスト](docs/05-hardware-validation.md)
7. [参考資料の評価](docs/06-reference-review.md)
8. [一次資料と更新日](docs/07-sources.md)
9. [実装ロードマップとIssue完了条件](docs/08-roadmap.md)
10. [教育用ngspiceモデルの基準結果](docs/09-simulation-results.md)
11. [KiCad 10開発環境とスモークテスト](docs/10-kicad-environment.md)
12. [CachyOSツールチェーン環境](docs/11-toolchain-environment.md)
13. [検証処理の並列化と性能](docs/12-validation-performance.md)
14. [初号機36キーレイアウトと調整プロファイル](docs/layout/README.md)
15. [Architecture Decision Records](docs/adr/README.md)

NotebookLMへ登録する候補は[ソースリスト](docs/notebooklm-sources.md)にまとめています。[統合Markdown](notebooklm/split-keyboard-hotplug-safety.md)は`make notebooklm`で再生成できます。

ブラウザ向けの入口は[ドキュメントページ](docs/index.html)です。色、余白、font-size、line-height、font-familyは[共通CSS変数](docs/assets/document.css)へ集約し、`make check-document-css`で直書きとインラインstyleを検査します。

## ローカル検証

ngspiceが導入済みなら、全チェックを実行できます。

```bash
make validate
```

`make validate`はNotebookLM、レイアウト生成物、ドキュメントCSS、Markdownリンク、静的検査、SPICEモデルを並列実行します。KiCadのERC/DRCとnegative testまで含める場合は`make validate-hardware`を使います。

CachyOSでホストへ恒久インストールせず試す場合は、Nixの一時環境を利用できます。

```bash
nix shell nixpkgs#ngspice nixpkgs#shellcheck -c make validate
```

SPICEモデルだけを個別実行する場合:

```bash
ngspice -b spice/trrs-vcc-short.cir
ngspice -b spice/gpio-series-resistors.cir
ngspice -b spice/passive-connector-bounce.cir
ngspice -b spice/rc-transient.cir
```

レイアウトJSONだけを再生成・検証する場合:

```bash
make layout
make check-layout
make check-document-css
```

モデル内の電源抵抗、GPIO出力抵抗、ケーブル容量などは比較用の仮定値です。採用部品が決まったら、データシートまたは実測値へ置き換えてください。

## 開発環境

KiCad 10.0.xとQMKをホストへ導入する場合の例です。実際に実行する前にパッケージ差分を確認してください。

```bash
pkexec pacman -S --needed kicad kicad-library ngspice qmk
qmk setup
kicad-cli version
```

KiCadにはngspiceベースの統合シミュレータがあります。CLI版`ngspice`は、付属`.cir`ファイルの再現実行とCIに使います。

KiCad 10環境、空回路ERC、RC過渡解析をまとめて確認する手順は[開発環境スモークテスト](docs/10-kicad-environment.md)に記録しています。

現在のKiCad/ngspice/QMK導入状態は`make environment`で確認できます。確認済みパッケージ版、3Dライブラリ容量、エージェント環境の制約は[ツールチェーン環境](docs/11-toolchain-environment.md)に記録しています。

## Issue

`issues/*.md`はGitHub Issuesの再現可能な正本です。各ファイルは1行目がタイトル、2行目がラベル、3行目以降が本文です。

```bash
./scripts/import_issues.sh hjosugi/electronics
```

同じタイトルがすでに存在する場合はスキップするため、再実行しても重複しません。`--dry-run`を付けると書き込みなしで対象を確認できます。

## ディレクトリ構成

```text
docs/                  調査、設計、安全性、レイアウト、一次資料
issues/                GitHub Issue定義
spice/                 教育用ngspiceモデル
scripts/               検証、Issue登録、Release梱包
hardware/              将来のKiCadプロジェクト
firmware/              将来のQMK定義
case/                  将来のケース/プレートCAD
.github/workflows/     スターター検証とERC/DRC
```

## ライセンス

現在収録している独自の文書、スクリプト、SPICEモデルは[MIT License](LICENSE)です。Chocofiの座標を基準にしたレイアウト生成物、プロファイル、生成スクリプトは[CERN-OHL-P-2.0と第三者通知](docs/layout/THIRD_PARTY_NOTICES.md)に従います。将来追加するQMK派生コードや第三者のフットプリント・モデルも、各上流ライセンスを維持し、必要ならディレクトリ単位のライセンスを追加します。

Cheapinoなどの参照先は設計上の比較資料であり、その設計ファイルをこのリポジトリへ複製してはいません。
