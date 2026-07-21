#!/usr/bin/env bash
# Package the shared layer + every Lambda into zips and upload to the artifacts bucket.
# Usage: ARTIFACTS_BUCKET=sentinel-artifacts-angger26 ./scripts/package.sh
set -euo pipefail
BUCKET="${ARTIFACTS_BUCKET:?set ARTIFACTS_BUCKET}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"; rm -rf "$BUILD"; mkdir -p "$BUILD/functions"

# layer (python/sentinel_common/...)
( cd "$ROOT/src/layer" && zip -qr "$BUILD/layer.zip" python )
aws s3 cp "$BUILD/layer.zip" "s3://$BUCKET/layer.zip"

for dir in ingest classify enrich compliance_check remediate approval_callback report init; do
  ( cd "$ROOT/src/$dir" && zip -qr "$BUILD/functions/$dir.zip" . )
  aws s3 cp "$BUILD/functions/$dir.zip" "s3://$BUCKET/functions/$dir.zip"
done
echo "Packaged + uploaded to s3://$BUCKET"
