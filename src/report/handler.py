"""sentinel-fn-report :: aggregate findings, write a CSV report to S3, presign, notify via SNS.
Triggered by the RemediationCompleted EventBridge rule and by the nightly sweep."""
import csv
import io
import os
import time
import boto3
from boto3.dynamodb.conditions import Key
from sentinel_common import get_logger, from_dynamo

log = get_logger("report")
ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
sns = boto3.client("sns")

FINDINGS_TABLE = os.environ["FINDINGS_TABLE"]
ARTIFACTS_BUCKET = os.environ["ARTIFACTS_BUCKET"]
ALERTS_TOPIC = os.environ["ALERTS_TOPIC_ARN"]
STATUS_INDEX = os.environ.get("STATUS_INDEX", "status-index")


def _cors(body, code=200):
    return {"statusCode": code,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(body, default=str)}


def handler(event, context):
    table = ddb.Table(FINDINGS_TABLE)
    # API Gateway GET /report -> return the finding list as JSON for the Amplify dashboard.
    if isinstance(event, dict) and event.get("httpMethod") == "GET":
        items = []
        for status in ("REMEDIATED", "QUARANTINED", "PROCESSING"):
            r = table.query(IndexName=STATUS_INDEX, KeyConditionExpression=Key("status").eq(status))
            items.extend(from_dynamo(r.get("Items", [])))
        return _cors({"count": len(items), "findings": items})
    rows = []
    for status in ("REMEDIATED", "QUARANTINED", "PROCESSING"):
        resp = table.query(
            IndexName=STATUS_INDEX,
            KeyConditionExpression=Key("status").eq(status),
        )
        rows.extend(from_dynamo(resp.get("Items", [])))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["findingId", "resourceType", "severity", "status", "remediationAction"])
    for r in rows:
        writer.writerow([r.get("findingId"), r.get("resourceType"),
                         r.get("severity"), r.get("status"), r.get("remediationAction", "")])

    key = f"reports/sentinel-report-{int(time.time())}.csv"
    s3.put_object(Bucket=ARTIFACTS_BUCKET, Key=key, Body=buf.getvalue().encode())
    url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": ARTIFACTS_BUCKET, "Key": key}, ExpiresIn=86400
    )
    sns.publish(
        TopicArn=ALERTS_TOPIC,
        Subject="[SentinelOps] Compliance report ready",
        Message=f"{len(rows)} findings summarised.\nDownload (24h): {url}",
    )
    log.info("report.done", extra={"extra": {"rows": len(rows), "key": key}})
    return {"rows": len(rows), "reportKey": key}
