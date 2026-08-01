# [repo] リポジトリ初期化
Labels: repo

## やること
- まず文書、SPICE、NotebookLM bundle、検証スクリプトを公開する
- 実装開始時に`hardware/`、`firmware/`、`case/`、`docs/adr/`を追加する
- 現在の独自資料はMIT。QMK派生コードや第三者フットプリントを追加する前に、各ライセンスを確認してディレクトリごとの区分をREADMEへ追記する
- README冒頭に、TRRSを使わない理由、中央ケーブルにVCCを流さないこと、右側を完全パッシブにすることを書く
- `.gitignore`とCI workflowを配置する

## 完了条件
- initial commitが`main`へpush済み
- 公開状態が`PUBLIC`であることをGitHubから読み戻した
- 本Issue群が登録済み
