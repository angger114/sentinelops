"""sentinel-fn-ingest :: normalize incoming finding + idempotency guard (DynamoDB)."""
import hashlib
import json
import os
import time
import boto3
from botocore.exceptions import ClientError
from sentinel_common import get_logger, to_dynamo_safe

log = get_logger("ingest")
ddb = boto3.resource("dynamodb")
IDEMPOTENCY_TABLE = os.environ["IDEMPOTENCY_TABLE"]
TTL_SECONDS = int(os.environ.get("IDEMPOTENCY_TTL", "86400"))


def _finding_id(event):
    # Accept a supplied findingId or derive a deterministic one from the raw event.
    if event.get("findingId"):
        return event["findingId"]
    raw = json.dumps(event.get("detail", event), sort_keys=True, default=str)
    return "SEC-" + hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def handler(event, context):
    log.info("ingest.received", extra={"extra": {"keys": list(event.keys())}})
    detail = event.get("detail", event)
    finding = {
        "findingId": _finding_id(event),
        "resourceType": detail.get("resourceType", detail.get("eventName", "UNKNOWN")),
        "resourceId": detail.get("resourceId", detail.get("requestParameters", {}).get("groupId", "n/a")),
        "region": detail.get("awsRegion", os.environ.get("AWS_REGION", "us-east-1")),
        "rawSource": event.get("source", "manual"),
        "receivedAt": int(time.time()),
    }

    table = ddb.Table(IDEMPOTENCY_TABLE)
    is_duplicate = False
    try:
        table.put_item(
            Item=to_dynamo_safe({
                "idempotencyKey": finding["findingId"],
                "expiresAt": int(time.time()) + TTL_SECONDS,
            }),
            ConditionExpression="attribute_not_exists(idempotencyKey)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            is_duplicate = True
            log.info("ingest.duplicate", extra={"extra": {"findingId": finding["findingId"]}})
        else:
            raise

    return {"finding": finding, "isDuplicate": is_duplicate}
