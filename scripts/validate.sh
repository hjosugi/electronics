#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

known_labels="env repo ci hardware firmware simulation safety test decision docs"
issue_count=0
scripts=(scripts/*.sh)

for script in "${scripts[@]}"; do
  bash -n "$script"
done

if command -v shellcheck >/dev/null; then
  shellcheck "${scripts[@]}"
fi

for issue in issues/[0-9][0-9]-*.md; do
  title="$(sed -n '1s/^# //p' "$issue")"
  labels="$(sed -n '2s/^Labels: //p' "$issue")"

  if [[ -z "$title" || -z "$labels" ]]; then
    echo "Issue形式が不正です: $issue" >&2
    exit 1
  fi

  IFS=',' read -r -a issue_labels <<<"$labels"
  for label in "${issue_labels[@]}"; do
    if [[ " $known_labels " != *" $label "* ]]; then
      echo "未定義ラベル '$label': $issue" >&2
      exit 1
    fi
  done

  issue_count=$((issue_count + 1))
done

if [[ "$issue_count" -ne 13 ]]; then
  echo "Issue定義は13件必要です（現在: $issue_count件）" >&2
  exit 1
fi

if [[ -d .git ]] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --check
fi

echo "静的検証に合格しました（Issue: ${issue_count}件）"
