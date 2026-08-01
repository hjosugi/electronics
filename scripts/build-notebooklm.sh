#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "$script_dir/.." && pwd)
output=${NOTEBOOKLM_OUTPUT:-"$repo_root/notebooklm/split-keyboard-hotplug-safety.md"}

documents=(
  docs/00-overview.md
  docs/01-passive-rj45-design.md
  docs/02-connector-options.md
  docs/03-simulation-guide.md
  docs/04-spice-models.md
  docs/05-hardware-validation.md
  docs/06-reference-review.md
  docs/07-sources.md
  docs/08-roadmap.md
  docs/09-simulation-results.md
  docs/10-kicad-environment.md
  docs/11-toolchain-environment.md
  docs/12-validation-performance.md
  docs/13-matrix-rj45-safety.md
  docs/14-qmk-firmware.md
  docs/layout/README.md
  docs/adr/0001-use-waveshare-rp2040-zero.md
  docs/adr/0002-use-36-key-choc-v1-layout.md
  docs/adr/0003-use-470-ohm-and-dual-ended-tvs.md
)

mkdir -p -- "$(dirname -- "$output")"
temporary=$(mktemp "${TMPDIR:-/tmp}/notebooklm-bundle.XXXXXX")
trap 'rm -f -- "$temporary"' EXIT

{
  printf '# 分割キーボードのホットプラグ安全設計とOSSシミュレーション\n\n'
  printf '> NotebookLM用統合資料。生成元は本リポジトリのdocsディレクトリです。\n'
  printf '> 内容確認日: 2026-08-01。製造前にリンク先の最新版と採用部品を再確認してください。\n\n'
  printf '## この統合資料について\n\n'
  printf 'このファイルは検索と質問応答をしやすくするため、設計判断、回路、シミュレーション、実機検証、出典を順番に結合しています。編集は生成元の各文書へ行い、make notebooklmで再生成してください。\n'

  for document in "${documents[@]}"; do
    printf '\n\n---\n\n'
    python3 "$script_dir/rewrite-markdown-links.py" "$repo_root/$document" "$repo_root/notebooklm" | sed '1s/^# /## /'
  done
} >"$temporary"

mv -- "$temporary" "$output"
trap - EXIT

printf 'generated %s\n' "$output"
