# KiCad 10開発環境とスモークテスト

この文書は、Issue #1の環境構築を別のCachyOS/Arch環境でも再現するための手順と検証記録です。ホストへの導入、CI、回路シミュレーションを分けて扱います。

## 確認したパッケージ

2026年7月31日にCachyOSの`pacman -Si`とArch Linux公式パッケージ情報を確認しました。

| パッケージ | 確認した版 | 用途 |
|---|---:|---|
| `kicad` | 10.0.5 | 回路図、PCB、`kicad-cli`。Arch版は`ngspice`へ依存 |
| `kicad-library` | 10.0.5 | 標準シンボルとフットプリント |
| `kicad-library-3d` | 10.0.5 | 標準3Dモデル。ERCだけなら必須ではない |
| `ngspice` | 46 | 単体CLIでのSPICE再現試験 |

一次資料は[Arch LinuxのKiCadパッケージ](https://archlinux.org/packages/extra/x86_64/kicad/)と[ngspiceパッケージ](https://archlinux.org/packages/extra/x86_64/ngspice/)です。ミラーの同期時差により、CachyOS側とArch側でリビジョン末尾が一時的に異なることがあります。

## ホストへ導入する場合

パッケージ情報を更新してから導入します。

CachyOSのGUI認証が動く端末で、システムを更新してから導入します。

```bash
pkexec pacman -Syu
pkexec pacman -S --needed kicad kicad-library ngspice
```

3D表示も使う場合は、展開後約3.2 GBのライブラリを追加します。

```bash
pkexec pacman -S --needed kicad-library-3d
```

バージョンを確認します。

```bash
kicad-cli version
ngspice --version
```

このリポジトリの自動検証はKiCad 10.0.xを要求します。将来KiCad 11へ移行するときは、ファイル形式、ERC/DRC差分、CIコンテナを別Issueで更新します。

## ERCスモークテスト

[`hardware/env-check/empty.kicad_sch`](../hardware/env-check/empty.kicad_sch)は、標準ライブラリに依存しない空のKiCad回路図です。次のコマンドはKiCadの版を検査し、`hardware/`以下の全回路図へERC、全基板へDRCを実行します。

```bash
make check-kicad
```

内部では公式CLIの次のオプションを使います。

```bash
kicad-cli sch erc --exit-code-violations --severity-all empty.kicad_sch
```

`--exit-code-violations`により、ERC violationがあれば終了コード5となりCIも失敗します。レポートは一時ディレクトリへ出力し、作業ツリーには残しません。

## RC過渡解析スモークテスト

[`spice/rc-transient.cir`](../spice/rc-transient.cir)は、5 Vステップ、1 kΩ、1 µFの一次RC回路です。時定数は次のとおりです。

```text
tau = R * C = 1 kΩ * 1 µF = 1 ms
V(tau) = 5 V * (1 - exp(-1)) ≈ 3.16 V
```

実行コマンドは次です。

```bash
ngspice -b spice/rc-transient.cir
```

`vout_at_tau_v`が約3.16 V、`time_to_63pct_s`が約1 msと表示されれば、過渡解析と`.meas`が動作しています。全SPICEモデルをまとめて実行する場合は`make simulate`を使います。

## KiCad GUIでの確認

1. KiCadでこのリポジトリを開く。
2. `hardware/env-check/empty.kicad_sch`を回路図エディタで開く。
3. `検査` → `エレクトリカル・ルール・チェッカー`を開き、ERCを実行する。
4. `検査` → `シミュレータ`を開き、シミュレータ自体が起動することを確認する。
5. RC回路をGUIで再作成する場合は、過渡解析を`0`から`5 ms`、最大時間ステップを`1 µs`程度に設定し、`V(out)`が1 ms付近で約3.16 Vになることを確認する。

自動判定の正本はCLIです。GUI確認は、画面表示、メニュー、ホスト固有の共有ライブラリ読み込みを確認する補助試験として扱います。

## `.gitignore`の照合

KiCadの正本ファイルである`.kicad_pro`、`.kicad_sch`、`.kicad_pcb`は追跡対象です。次は生成物または端末固有状態なので除外します。

| パターン | 理由 |
|---|---|
| `*.kicad_prl` | ローカルUI・作業状態 |
| `*-backups/`、`*.bak`、`_autosave-*` | バックアップと自動保存 |
| `~*.lck`、`*.lck` | 編集中のロックファイル |
| `fp-info-cache` | 再生成可能なキャッシュ |
| `*.raw`、`*.log`、`*.tmp` | SPICE出力と一時ファイル |
| `hardware/gerbers/`、`hardware/production/` | CIで再生成する製造出力 |

回路図、基板、シンボル、フットプリントを新しく追加したときは、必要な正本まで広いglobで除外していないか`git status --ignored`で確認します。

## CI

`hardware/**`を変更すると`hardware-ci`がKiCad 10コンテナで次を実行します。

```bash
make validate-hardware
```

これによりKiCad 10.0.x、ERC/DRC、RCを含むngspiceモデルを同じジョブで確認できます。空回路のERC成功は環境スモークテストであり、将来の実回路の電気的妥当性や安全性を保証しません。

## 2026年7月31日の検証結果

Nix storeに取得済みのKiCad 10.0.5とngspice 45を使い、`make validate-hardware`を実行しました。

| 検査 | 結果 |
|---|---|
| `kicad-cli version` | `10.0.5` |
| 空回路ERC | violation 0件 |
| RC回路の`V(out)`、1 ms | `3.160602 V` |
| 63.212%到達時刻 | `0.999999 ms` |
| 既存SPICEモデル3本 | 全て完走 |
| Markdown、ShellCheck、Issue形式 | 合格 |

この数値は1 kΩ・1 µFの教育用RCモデルに対する環境確認値です。分割キーボードの保護部品や活線挿抜安全性の根拠には使用しません。
