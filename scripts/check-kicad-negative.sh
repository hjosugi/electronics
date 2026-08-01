#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v kicad-cli >/dev/null; then
  echo "kicad-cli が必要です" >&2
  exit 1
fi

kicad_version="$(kicad-cli version)"
if [[ ! "$kicad_version" =~ ^10\.0\. ]]; then
  echo "KiCad 10.0.x が必要です（検出: $kicad_version）" >&2
  exit 1
fi

report_dir="$(mktemp -d "${TMPDIR:-/tmp}/electronics-kicad-negative.XXXXXX")"
cleanup() {
  find "$report_dir" -type f -delete
  rmdir "$report_dir"
}
trap cleanup EXIT

erc_report="$report_dir/erc.rpt"
set +e
kicad-cli sch erc \
  --exit-code-violations \
  --severity-all \
  --output "$erc_report" \
  tests/fixtures/kicad/erc-dangling-wire.kicad_sch
erc_status=$?
set -e

if [[ "$erc_status" -ne 5 ]]; then
  echo "ERC violation fixtureの終了コードが5ではありません（実際: $erc_status）" >&2
  exit 1
fi
if ! grep -Fq '[wire_dangling]' "$erc_report"; then
  echo "ERCレポートにwire_danglingがありません" >&2
  exit 1
fi

drc_report="$report_dir/drc.rpt"
set +e
kicad-cli pcb drc \
  --exit-code-violations \
  --severity-all \
  --output "$drc_report" \
  tests/fixtures/kicad/drc-open-outline.kicad_pcb
drc_status=$?
set -e

if [[ "$drc_status" -ne 5 ]]; then
  echo "DRC violation fixtureの終了コードが5ではありません（実際: $drc_status）" >&2
  exit 1
fi
if ! grep -Fq '[invalid_outline]' "$drc_report"; then
  echo "DRCレポートにinvalid_outlineがありません" >&2
  exit 1
fi

echo "KiCad negative testに合格しました（ERC/DRCともにviolationを検出、終了コード5）"
