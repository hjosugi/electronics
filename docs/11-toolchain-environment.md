# CachyOSツールチェーン環境

確認日: 2026-08-01

## 状態を確認する

```bash
./scripts/check-environment.sh --report
./scripts/check-environment.sh --require-hardware
./scripts/check-environment.sh --require-firmware
```

`--report`は不足を表示しても成功します。`--require-hardware`はKiCad/ngspice、`--require-firmware`はQMKがなければ失敗するため、セットアップ完了の機械的な確認に使えます。

## CachyOS/Archのパッケージ

2026-08-01に、このホストの同期データベースで次を確認しました。

| パッケージ | 確認版 | 用途 |
| --- | --- | --- |
| `kicad` | 10.0.5-1.1 | 回路図、PCB、ERC/DRC、GUIシミュレータ |
| `kicad-library` | 10.0.5-1 | シンボル、フットプリント、テンプレート |
| `kicad-library-3d` | 10.0.5-1 | 3Dモデル、任意 |
| `ngspice` | 46-2.1 | `.cir`のCLI再現実行 |
| `qmk` | 1.2.0-2 | QMK CLIとクロスツールチェーン |

KiCad 3Dライブラリは展開後約3.2 GBです。回路図・PCB・SPICEを先に始めるだけなら省略し、ケース干渉や3D確認を始める時点で追加できます。

### ホストへ導入

CachyOSのGUI認証が動く端末で実行します。

```bash
pkexec pacman -S --needed kicad kicad-library ngspice qmk
```

3Dモデルも必要なら追加します。

```bash
pkexec pacman -S --needed kicad-library-3d
```

導入後:

```bash
kicad-cli version
ngspice --version
qmk --version
./scripts/check-environment.sh --require-all
```

`qmk setup`はQMK firmwareをユーザーディレクトリへcloneするため、保存先を確認してから別途実行します。

## root不要のSPICE検証

ホストへ恒久インストールせず、現在の文書・スクリプト・SPICEモデルだけを検証する場合:

```bash
nix shell nixpkgs#ngspice nixpkgs#shellcheck -c make validate
```

このコマンドはngspice 45で実行済みです。測定値は[基準結果](09-simulation-results.md)に記録しています。KiCad GUI、QMKのUF2ビルド、実機USB接続はこのコマンドの検証範囲外です。

## エージェント実行環境の制約

今回のエージェント環境では、`pkexec`のsetuid属性が無効化されており、ホストへのpacman導入は実行できませんでした。またNix daemonとDocker/Podman socketも一部のサンドボックス呼び出しから拒否されます。

これはパッケージ不在や回路の失敗ではありません。Issue #1はCLI/CIでERCとRC過渡解析まで確認済みですが、ホスト上のKiCad GUI確認が残っています。Issue #2は、QMK環境を導入してUF2をビルドするまで未完了です。
