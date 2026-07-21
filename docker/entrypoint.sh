#!/bin/sh
# Deep compliance scan. MODE=scan (default): evaluate the inventory with Conftest.
# MODE=verify: re-check the remediated target bucket's public-access-block.
set -eu
FINDING_ID="${FINDING_ID:-unknown}"
ARTIFACTS_BUCKET="${ARTIFACTS_BUCKET:?ARTIFACTS_BUCKET required}"
MODE="${MODE:-scan}"

if [ "$MODE" = "verify" ]; then
  TARGET="${TARGET_BUCKET:?TARGET_BUCKET required}"
  BLOCK=$(aws s3api get-public-access-block --bucket "$TARGET" \
            --query 'PublicAccessBlockConfiguration.BlockPublicAcls' --output text 2>/dev/null || echo "MISSING")
  RESULT="{\"findingId\":\"$FINDING_ID\",\"mode\":\"verify\",\"blockPublicAcls\":\"$BLOCK\",\"verified\":$([ "$BLOCK" = "True" ] && echo true || echo false)}"
  echo "$RESULT" | aws s3 cp - "s3://$ARTIFACTS_BUCKET/deep-scan/$FINDING_ID/verify.json"
  echo "$RESULT"
  # Non-zero exit signals a failed verification to the Job/Step Functions.
  [ "$BLOCK" = "True" ]
  exit $?
fi

# scan mode: /work/inventory.json is provided by the initContainer; /policy holds the Rego.
conftest test /work/inventory.json --policy /policy --all-namespaces --output json > /work/results.json 2>/dev/null || true
FAILURES=$(grep -o '"failures":\[[^]]*\]' /work/results.json | grep -o '"msg"' | wc -l | tr -d ' ')
SUMMARY="{\"findingId\":\"$FINDING_ID\",\"mode\":\"scan\",\"violations\":$FAILURES}"
aws s3 cp /work/results.json "s3://$ARTIFACTS_BUCKET/deep-scan/$FINDING_ID/results.json"
echo "$SUMMARY" | aws s3 cp - "s3://$ARTIFACTS_BUCKET/deep-scan/$FINDING_ID/summary.json"
echo "$SUMMARY"
