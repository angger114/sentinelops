"""sentinel-fn-init :: seed findings + repeat-offender history + generate the Distributed Map inventory.
Test payload: {"findingId": "SEC-DEMO0001", "resourceId": "sentinel-target-angger26", "inventorySize": 25}"""
import json
import os
import time
import boto3
from sentinel_common import get_logger, to_dynamo_safe

log = get_logger("init")
ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
FINDINGS_TABLE = os.environ["FINDINGS_TABLE"]
SCAN_INPUT_BUCKET = os.environ["SCAN_INPUT_BUCKET"]


def handler(event, context):
    finding_id = event.get("findingId", "SEC-DEMO0001")
    resource_id = event.get("resourceId", "sentinel-target-angger26")
    size = int(event.get("inventorySize", 25))
    table = ddb.Table(FINDINGS_TABLE)

    # 1) Current snapshot row.
    table.put_item(Item=to_dynamo_safe({
        "pk": f"FINDING#{finding_id}", "sk": "SNAPSHOT",
        "findingId": finding_id, "resourceId": resource_id,
        "resourceType": "S3Bucket", "severity": "HIGH", "status": "PROCESSING",
        "seededAt": int(time.time()),
    }))

    # 2) A few prior history rows for the SAME resourceId so the repeat-offender
    #    DynamoDB Query (resource-index GSI) returns a realistic count.
    for i in range(3):
        table.put_item(Item=to_dynamo_safe({
            "pk": f"FINDING#SEC-HIST{i}", "sk": "SNAPSHOT",
            "findingId": f"SEC-HIST{i}", "resourceId": resource_id,
            "resourceType": "S3Bucket", "severity": "LOW", "status": "REMEDIATED",
        }))

    # 3) Distributed Map inventory JSON.
    inventory = [{
        "resourceArn": f"arn:aws:s3:::bucket-{i:04d}",
        "resourceId": f"bucket-{i:04d}",
        "public": (i % 5 == 0), "encrypted": (i % 7 != 0),
    } for i in range(size)]
    key = f"inventory/{finding_id}.json"
    s3.put_object(Bucket=SCAN_INPUT_BUCKET, Key=key, Body=json.dumps(inventory).encode())

    log.info("init.seeded", extra={"extra": {"findingId": finding_id, "resourceId": resource_id, "inventory": size}})
    return {"seeded": finding_id, "resourceId": resource_id, "inventoryKey": key, "inventorySize": size}
