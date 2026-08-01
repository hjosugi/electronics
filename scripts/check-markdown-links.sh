#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "$script_dir/.." && pwd)
status=0

while IFS= read -r markdown; do
  directory=$(dirname -- "$markdown")
  while IFS= read -r target; do
    case "$target" in
      ''|'#'*|http://*|https://*|mailto:*)
        continue
        ;;
    esac

    target=${target%%#*}
    target=${target%%\?*}
    if [[ ! -e "$directory/$target" ]]; then
      printf 'missing local link: %s -> %s\n' "${markdown#"$repo_root/"}" "$target" >&2
      status=1
    fi
  done < <(sed -nE 's/.*\]\(([^)]+)\).*/\1/p' "$markdown")
done < <(find "$repo_root" -path "$repo_root/.git" -prune -o -name '*.md' -type f -print)

exit "$status"
