#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v ngspice >/dev/null; then
  echo "ngspice が必要です" >&2
  exit 1
fi

circuits=(
  spice/rc-transient.cir
  spice/trrs-vcc-short.cir
  spice/gpio-series-resistors.cir
  spice/passive-connector-bounce.cir
)

log_dir="$(mktemp -d "${TMPDIR:-/tmp}/electronics-spice.XXXXXX")"
cleanup() {
  find "$log_dir" -type f -delete
  rmdir "$log_dir"
}
trap cleanup EXIT

pids=()
logs=()
for index in "${!circuits[@]}"; do
  log="$log_dir/${index}.log"
  ngspice -b "${circuits[$index]}" >"$log" 2>&1 &
  pids+=("$!")
  logs+=("$log")
done

status=0
for index in "${!circuits[@]}"; do
  if wait "${pids[$index]}"; then
    printf '==> %s\n' "${circuits[$index]}"
    grep -E 'Measurements for Transient Analysis|^[a-z][a-z0-9_]*[[:space:]]+=[[:space:]]+' \
      "${logs[$index]}" || true
  else
    status=1
    printf '==> %s (failed)\n' "${circuits[$index]}"
    cat "${logs[$index]}"
  fi
done

if ((status != 0)); then
  echo "SPICE検証に失敗しました" >&2
  exit "$status"
fi

echo "SPICE検証に合格しました（${#circuits[@]}回路を並列実行）"
