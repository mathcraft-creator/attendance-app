#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WHEEL_DIR="$ROOT_DIR/wheelhouse"

mkdir -p "$WHEEL_DIR"

# Online environment required
python -m pip download -r "$ROOT_DIR/requirements.txt" -d "$WHEEL_DIR"

echo "Wheelhouse built at: $WHEEL_DIR"
echo "Offline install command:"
echo "  pip install --no-index --find-links=wheelhouse -r requirements.txt"
