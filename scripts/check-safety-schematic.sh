#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v kicad-cli >/dev/null; then
  echo "kicad-cli が必要です" >&2
  exit 1
fi

work_dir="$(mktemp -d "${TMPDIR:-/tmp}/electronics-safety-netlist.XXXXXX")"
cleanup() {
  find "$work_dir" -type f -delete
  rmdir "$work_dir"
}
trap cleanup EXIT

kicad-cli sch export netlist \
  --format kicadxml \
  --output "$work_dir/split-keyboard.xml" \
  hardware/split-keyboard/split-keyboard.kicad_sch

python3 scripts/check-safety-netlist.py \
  --layout docs/layout/36-key-choc-v1.layout.json \
  --self-test \
  "$work_dir/split-keyboard.xml"
