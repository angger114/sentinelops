"""sentinel-fn-approval-callback :: API Gateway webhook that resumes a paused Step Functions
execution by sending the task token success/failure.

POST /approval  body: {"taskToken": "...", "decision": "APPROVED"|"REJECTED", "reviewer": "..."}
"""
import json
import boto3
from sentinel_common import get_logger

log = get_logger("approval")
sfn = boto3.client("stepfunctions")


def _resp(code, body):
    return {"statusCode": code, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)}


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except (TypeError, ValueError):
        return _resp(400, {"error": "invalid JSON body"})

    token = body.get("taskToken")
    decision = (body.get("decision") or "").upper()
    if not token or decision not in ("APPROVED", "REJECTED"):
        return _resp(400, {"error": "taskToken and decision(APPROVED|REJECTED) required"})

    try:
        if decision == "APPROVED":
            sfn.send_task_success(
                taskToken=token,
                output=json.dumps({"decision": "APPROVED", "reviewer": body.get("reviewer", "unknown")}),
            )
        else:
            sfn.send_task_failure(
                taskToken=token, error="ApprovalRejected",
                cause=f"Rejected by {body.get('reviewer', 'unknown')}",
            )
    except sfn.exceptions.TaskDoesNotExist:
        return _resp(410, {"error": "task token expired or already resolved"})
    except sfn.exceptions.InvalidToken:
        return _resp(400, {"error": "invalid task token"})

    log.info("approval.resolved", extra={"extra": {"decision": decision}})
    return _resp(200, {"status": "resumed", "decision": decision})
