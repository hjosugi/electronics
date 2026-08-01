#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
qmk_root="${1:-${QMK_HOME:-}}"

if [[ -z "$qmk_root" ]]; then
  echo "usage: $0 /path/to/qmk_firmware" >&2
  exit 2
fi

qmk_root="$(realpath "$qmk_root")"
# The repository root is computed at runtime, so ShellCheck cannot follow it.
# shellcheck disable=SC1091
source "$repo_root/firmware/qmk/qmk-version.env"

if [[ ! -d "$qmk_root/.git" ]]; then
  echo "QMK checkoutではありません: $qmk_root" >&2
  exit 2
fi

actual_ref="$(git -C "$qmk_root" rev-parse HEAD)"
if [[ "$actual_ref" != "$QMK_REF" ]]; then
  echo "QMK commitが一致しません: expected=$QMK_REF actual=$actual_ref" >&2
  exit 1
fi

if ! command -v qmk >/dev/null; then
  echo "qmk CLIが見つかりません" >&2
  exit 127
fi

actual_cli="$(qmk --version | awk '{print $NF}')"
if [[ "$actual_cli" != "$QMK_CLI_VERSION" ]]; then
  echo "警告: QMK CLI expected=$QMK_CLI_VERSION actual=$actual_cli" >&2
fi

source_keyboard="$repo_root/firmware/qmk/keyboards/electronics/splitkb36"
target_parent="$qmk_root/keyboards/electronics"
target_keyboard="$target_parent/splitkb36"
mkdir -p "$target_parent"

if [[ -e "$target_keyboard" || -L "$target_keyboard" ]]; then
  echo "QMK側のkeyboard定義と衝突します: $target_keyboard" >&2
  exit 1
fi

ln -s "$source_keyboard" "$target_keyboard"
cleanup() {
  if [[ -L "$target_keyboard" && "$(readlink "$target_keyboard")" == "$source_keyboard" ]]; then
    unlink "$target_keyboard"
  fi
}
trap cleanup EXIT

jobs="${QMK_JOBS:-$(nproc)}"
(
  cd "$qmk_root"
  qmk lint -kb electronics/splitkb36
  qmk compile -j "$jobs" -kb electronics/splitkb36 -km default
)

firmware="$qmk_root/electronics_splitkb36_default.uf2"
if [[ ! -s "$firmware" ]]; then
  echo "UF2が生成されませんでした: $firmware" >&2
  exit 1
fi

output_dir="$repo_root/dist/qmk"
mkdir -p "$output_dir"
output="$output_dir/electronics_splitkb36_default-$actual_ref.uf2"
cp "$firmware" "$output"

echo "UF2: $output"
sha256sum "$output"
