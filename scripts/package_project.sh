#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
PKG_NAME="attendance-app-package-$(date +%Y%m%d-%H%M%S)"
PKG_DIR="$DIST_DIR/$PKG_NAME"

rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"

# Core files
cp "$ROOT_DIR"/*.py "$PKG_DIR" 2>/dev/null || true
cp "$ROOT_DIR"/requirements.txt "$PKG_DIR"/
cp "$ROOT_DIR"/.env.example "$PKG_DIR"/
cp "$ROOT_DIR"/README.md "$PKG_DIR"/
cp "$ROOT_DIR"/.gitignore "$PKG_DIR"/

# Frontend scaffold files (if present)
for f in package.json tsconfig.json next.config.mjs next-env.d.ts; do
  if [[ -f "$ROOT_DIR/$f" ]]; then
    cp "$ROOT_DIR/$f" "$PKG_DIR"/
  fi
done

if [[ -d "$ROOT_DIR/app" ]]; then
  mkdir -p "$PKG_DIR/app"
  cp -R "$ROOT_DIR/app"/* "$PKG_DIR/app/" 2>/dev/null || true
fi

# Packaging docs/scripts
mkdir -p "$PKG_DIR/packaging"
cp "$ROOT_DIR/packaging"/README.md "$PKG_DIR/packaging"/

mkdir -p "$PKG_DIR/scripts"
cp "$ROOT_DIR/scripts"/build_wheelhouse.sh "$PKG_DIR/scripts"/

cd "$DIST_DIR"
zip -rq "$PKG_NAME.zip" "$PKG_NAME"

echo "Created package: $DIST_DIR/$PKG_NAME.zip"
