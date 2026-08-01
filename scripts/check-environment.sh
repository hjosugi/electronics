#!/usr/bin/env bash
set -euo pipefail

mode="${1:---report}"
case "$mode" in
  --report | --require-base | --require-hardware | --require-firmware | --require-all)
    ;;
  *)
    echo "usage: $0 [--report|--require-base|--require-hardware|--require-firmware|--require-all]" >&2
    exit 2
    ;;
esac

missing_required=0

is_required() {
  local group="$1"
  case "$mode:$group" in
    --require-base:base | --require-hardware:base | --require-hardware:hardware | \
      --require-firmware:base | --require-firmware:firmware | --require-all:*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

check_tool() {
  local group="$1"
  local label="$2"
  shift 2

  if command -v "$1" >/dev/null 2>&1; then
    local version
    version="$("$@" 2>&1 | sed -n '1p')"
    printf 'ok      %-12s %s\n' "$label" "$version"
    return 0
  fi

  if is_required "$group"; then
    printf 'missing %-12s required for %s\n' "$label" "$group" >&2
    missing_required=1
  else
    printf 'missing %-12s optional for this check (%s)\n' "$label" "$group"
  fi
}

check_tool base Git git --version
check_tool base Make make --version
check_tool hardware KiCad kicad-cli version
check_tool hardware ngspice ngspice --version
check_tool firmware QMK qmk --version
check_tool support ShellCheck shellcheck --version
check_tool support GitHub-CLI gh --version
check_tool support Nix nix --version
check_tool support direnv direnv version

if ((missing_required != 0)); then
  echo >&2
  echo "導入手順: docs/11-toolchain-environment.md" >&2
  exit 1
fi
