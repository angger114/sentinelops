"""sentinel-fn-remediate :: applies a real, safe fix (S3 PutPublicAccessBlock) on the target bucket.
Deployed Blue/Green via CodeDeploy (:live alias).

Custom errors let the Step Functions Retry/Catch policies discriminate:
  - RemediationTransient   -> retried with backoff
  - RemediationHardFailure -> caught, routed to QuarantineAndAlert
Trigger them for testing via finding.resourceId == "TRIGGER_TRANSIENT" / "TRIGGER_HARD".
"""
import os
import time
import boto3
from sentinel_common import get_logger

log = get_logger("remediate")
VERSION = os.environ.get("REMEDIATE_VERSION", "1")   # bump to 2 to exercise Blue/Green
TARGET_BUCKET = os.environ.get("TARGET_BUCKET")
s3 = boto3.client("s3")


class RemediationTransient(Exception):
    pass


class RemediationHardFailure(Exception):
    pass


def handler(event, context):
    finding = event.get("finding", {})
    classification = event.get("classification", {})
    rid = finding.get("resourceId", "n/a")

    if rid == "TRIGGER_TRANSIENT":
        raise RemediationTransient("Downstream throttled, retry me.")
    if rid == "TRIGGER_HARD":
        raise RemediationHardFailure("Resource is in a state we cannot auto-fix.")

    # Real, idempotent, safe remediation: block all public access on the target bucket.
    bucket = TARGET_BUCKET or rid
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True, "IgnorePublicAcls": True,
            "BlockPublicPolicy": True, "RestrictPublicBuckets": True,
        },
    )
    action = f"s3-public-access-blocked:{bucket}:v{VERSION}"
    remediated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    log.info("remediate.done", extra={"extra": {
        "findingId": finding.get("findingId"), "bucket": bucket,
        "severity": classification.get("severity"), "version": VERSION}})
    return {"action": action, "remediatedAt": remediated_at, "version": VERSION}
