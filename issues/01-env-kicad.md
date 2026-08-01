# [env] KiCad 10 環境構築 (CachyOS)
Labels: env

## 背景
回路設計とシミュレーションの基盤。KiCad 10.0.5が現行stable (2026-07-22リリース)。KiCadはngspiceをシミュレーションエンジンとして使うが、ディストリビューションのパッケージ分割は導入時に確認する。

## やること
- CachyOS/Archの公式パッケージ名を確認してKiCad、標準ライブラリ、ngspiceを導入
- `kicad-cli version` で 10.0.x を確認
- 回路図エディタ → 検査 → シミュレータ で ngspice が動くことを確認
- リポジトリ側`.gitignore`とKiCadが生成する除外候補を照合

## 完了条件
- 空プロジェクトで ERC が実行できる
- RC 回路の過渡解析 (tran) が 1 本流せる
