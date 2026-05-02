#!/usr/bin/env bash
set -euo pipefail

PINNED_COMMIT="3e5fe957d299a43e28a64df35145f569c5ad0a7f"
SOURCE_REPO="${1:-/tmp/BGS-Tally-harness}"
SOURCE_COMMIT="${2:-$PINNED_COMMIT}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_TESTS_DIR="$ROOT_DIR/tests"

if [[ ! -d "$SOURCE_REPO/.git" ]]; then
  echo "Source repo not found at $SOURCE_REPO"
  echo "Clone first: git clone https://github.com/aussig/BGS-Tally.git $SOURCE_REPO"
  exit 1
fi

git -C "$SOURCE_REPO" rev-parse --verify "${SOURCE_COMMIT}^{commit}" >/dev/null
git -C "$SOURCE_REPO" checkout --quiet "$SOURCE_COMMIT"

mkdir -p "$TARGET_TESTS_DIR/edmc/plugins"

cp "$SOURCE_REPO/tests/__init__.py" "$TARGET_TESTS_DIR/__init__.py"
cp "$SOURCE_REPO/tests/harness.py" "$TARGET_TESTS_DIR/harness.py"
cp "$SOURCE_REPO/tests/edmc/"*.py "$TARGET_TESTS_DIR/edmc/"
cp "$SOURCE_REPO/tests/edmc/plugins/"*.py "$TARGET_TESTS_DIR/edmc/plugins/"

echo "Vendored harness snapshot refreshed from:"
echo "  repo:   $SOURCE_REPO"
echo "  commit: $SOURCE_COMMIT"
echo
echo "Do not edit tests/harness.py or tests/edmc/** directly."
echo "Apply project-specific integration changes in tests/harness_bootstrap.py and tests/overlay_adapter.py."
