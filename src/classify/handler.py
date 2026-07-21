"""sentinel-fn-classify :: severity scoring + approval gate decision."""
import os
from sentinel_common import get_logger

log = get_logger("classify")

# Weighted risk model. Higher score => higher severity.
RESOURCE_WEIGHTS = {
    "AuthorizeSecurityGroupIngress": 60,
    "SecurityGroup": 55,
    "S3Bucket": 45,
    "PutBucketPolicy": 50,
    "IAMPolicy": 40,
    "RDSInstance": 35,
    "UNKNOWN": 20,
}
APPROVAL_THRESHOLD = int(os.environ.get("APPROVAL_THRESHOLD", "50"))


def handler(finding, context):
    rtype = finding.get("resourceType", "UNKNOWN")
    score = RESOURCE_WEIGHTS.get(rtype, RESOURCE_WEIGHTS["UNKNOWN"])
    # Public exposure bumps the score.
    if "public" in str(finding.get("resourceId", "")).lower():
        score += 25

    if score >= 75:
        severity = "CRITICAL"
    elif score >= 45:
        severity = "HIGH"
    else:
        severity = "LOW"

    requires_approval = score >= APPROVAL_THRESHOLD
    log.info("classify.done", extra={"extra": {"severity": severity, "score": score}})
    return {"severity": severity, "score": score, "requiresApproval": requires_approval}
