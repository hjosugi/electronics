#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "$script_dir/.." && pwd)
committed="$repo_root/notebooklm/split-keyboard-hotplug-safety.md"
temporary=$(mktemp "${TMPDIR:-/tmp}/notebooklm-check.XXXXXX")
trap 'rm -f -- "$temporary"' EXIT

NOTEBOOKLM_OUTPUT="$temporary" "$script_dir/build-notebooklm.sh" >/dev/null

if ! cmp -s -- "$temporary" "$committed"; then
  printf 'NotebookLM bundle is stale. Run: make notebooklm\n' >&2
  diff -u -- "$committed" "$temporary" || true
  exit 1
fi

printf 'NotebookLM bundle is up to date.\n'
