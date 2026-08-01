#!/usr/bin/env bash
set -euo pipefail

version="${1:?usage: $0 <tag, e.g. v0.1.0>}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! git rev-parse --verify --quiet "refs/tags/$version" >/dev/null; then
  echo "タグが見つかりません: $version" >&2
  exit 1
fi

archive_name="electronics-${version#v}.zip"
mkdir -p dist
git archive \
  --format=zip \
  --prefix="electronics-${version#v}/" \
  --output="dist/$archive_name" \
  "$version"

(
  cd dist
  sha256sum "$archive_name" >"$archive_name.sha256"
)

echo "作成: dist/$archive_name"
echo "作成: dist/$archive_name.sha256"
