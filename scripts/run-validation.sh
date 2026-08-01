#!/usr/bin/env bash
set -euo pipefail

mode="${1:---base}"
case "$mode" in
  --base | --hardware)
    ;;
  *)
    echo "usage: $0 [--base|--hardware]" >&2
    exit 2
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

log_dir="$(mktemp -d "${TMPDIR:-/tmp}/electronics-validation.XXXXXX")"
cleanup() {
  find "$log_dir" -type f -delete
  rmdir "$log_dir"
}
trap cleanup EXIT

names=()
pids=()
logs=()

start_check() {
  local name="$1"
  shift
  local index="${#names[@]}"
  local log="$log_dir/${index}.log"

  names+=("$name")
  logs+=("$log")
  "$@" >"$log" 2>&1 &
  pids+=("$!")
}

start_check "NotebookLM" ./scripts/check-notebooklm.sh
start_check "Layout" python3 ./scripts/build-layout.py --check --self-test
start_check "Document CSS" python3 ./scripts/check-document-css.py
start_check "Markdown links" ./scripts/check-markdown-links.sh
start_check "Static validation" ./scripts/validate.sh
start_check "ngspice" ./scripts/check-spice.sh

if [[ "$mode" == "--hardware" ]]; then
  start_check "KiCad ERC/DRC" ./scripts/check-kicad-suite.sh
fi

status=0
for index in "${!names[@]}"; do
  if ! wait "${pids[$index]}"; then
    status=1
  fi
  printf '\n==> %s\n' "${names[$index]}"
  cat "${logs[$index]}"
done

if ((status != 0)); then
  echo "検証に失敗しました" >&2
  exit "$status"
fi

echo "検証に合格しました（${#names[@]}系統を並列実行）"
