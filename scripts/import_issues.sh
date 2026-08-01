#!/usr/bin/env bash
# issues/*.mdをGitHub Issueへ登録する。
# Usage: ./scripts/import_issues.sh [--dry-run] <owner>/<repo>
set -euo pipefail

dry_run=false
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run=true
  shift
fi

repo="${1:?usage: $0 [--dry-run] <owner>/<repo>}"
issue_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../issues" && pwd)"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

declare -A labels=(
  [env]="1d76db"
  [repo]="0e8a16"
  [ci]="5319e7"
  [hardware]="d93f0b"
  [firmware]="fbca04"
  [simulation]="006b75"
  [safety]="b60205"
  [test]="c2e0c6"
  [decision]="bfdadc"
  [docs]="0075ca"
)

if [[ "$dry_run" == false ]]; then
  for name in "${!labels[@]}"; do
    gh label create "$name" \
      --repo "$repo" \
      --color "${labels[$name]}" \
      --force
  done
fi

existing_titles="$work_dir/existing-titles.txt"
if gh issue list \
  --repo "$repo" \
  --state all \
  --limit 1000 \
  --json title \
  --jq '.[].title' >"$existing_titles"; then
  :
elif [[ "$dry_run" == true ]]; then
  : >"$existing_titles"
else
  echo "既存Issueを取得できませんでした: $repo" >&2
  exit 1
fi

for issue in "$issue_dir"/[0-9][0-9]-*.md; do
  title="$(sed -n '1s/^# //p' "$issue")"
  issue_labels="$(sed -n '2s/^Labels: //p' "$issue")"

  if [[ -z "$title" || -z "$issue_labels" ]]; then
    echo "Issue形式が不正です: $issue" >&2
    exit 1
  fi

  if grep -Fqx -- "$title" "$existing_titles"; then
    echo "skip: $title"
    continue
  fi

  if [[ "$dry_run" == true ]]; then
    echo "create: $title [$issue_labels]"
    continue
  fi

  body_file="$work_dir/body.md"
  tail -n +3 "$issue" >"$body_file"
  gh issue create \
    --repo "$repo" \
    --title "$title" \
    --label "$issue_labels" \
    --body-file "$body_file"
  printf '%s\n' "$title" >>"$existing_titles"
done
