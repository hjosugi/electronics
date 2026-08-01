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

mapfile -d '' schematics < <(
  find hardware -type f -name '*.kicad_sch' -print0 | sort -z
)
mapfile -d '' boards < <(
  find hardware -type f -name '*.kicad_pcb' -print0 | sort -z
)

if (( ${#schematics[@]} == 0 )); then
  echo "ERC対象のKiCad回路図がありません" >&2
  exit 1
fi

report_dir="$(mktemp -d "${TMPDIR:-/tmp}/electronics-kicad.XXXXXX")"
cleanup() {
  find "$report_dir" -type f -delete
  rmdir "$report_dir"
}
trap cleanup EXIT

for index in "${!schematics[@]}"; do
  schematic="${schematics[$index]}"
  report="$report_dir/erc-${index}.rpt"
  echo "==> ERC: $schematic"
  kicad-cli sch erc \
    --exit-code-violations \
    --severity-all \
    --output "$report" \
    "$schematic"
done

for index in "${!boards[@]}"; do
  board="${boards[$index]}"
  report="$report_dir/drc-${index}.rpt"
  echo "==> DRC: $board"
  kicad-cli pcb drc \
    --exit-code-violations \
    --severity-all \
    --output "$report" \
    "$board"
done

echo "KiCad環境検証に合格しました（KiCad $kicad_version、回路図: ${#schematics[@]}、基板: ${#boards[@]}）"
