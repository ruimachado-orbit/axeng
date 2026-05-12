#!/usr/bin/env bash
# Build the Axeng marketing page as a static S3/CloudFront artifact.
# Produces: out-website/index.html + _next/static assets.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/out-website}"

cd "$ROOT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Building Axeng website static artifact"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

npm run build

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/_next"

# /website is prerendered by Next. Promote it to / for S3/CloudFront hosting.
cp "$ROOT_DIR/.next/server/app/website.html" "$OUT_DIR/index.html"
cp "$ROOT_DIR/.next/server/app/website.rsc" "$OUT_DIR/website.rsc" 2>/dev/null || true
cp -R "$ROOT_DIR/.next/static" "$OUT_DIR/_next/static"

# Copy public assets if present (favicon, images, etc.).
if [ -d "$ROOT_DIR/public" ]; then
  rsync -a "$ROOT_DIR/public/" "$OUT_DIR/"
fi

# S3/CloudFront static hosting fallback pages.
cp "$OUT_DIR/index.html" "$OUT_DIR/404.html"

printf "✅ Static artifact ready: %s\n" "$OUT_DIR"
printf "   Entry: %s/index.html\n" "$OUT_DIR"
