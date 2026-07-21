"""sentinel-fn-enrich :: enrich one compliance dimension. Called by the Express inline Map."""
from sentinel_common import get_logger

log = get_logger("enrich")

DIMENSION_HINTS = {
    "encryption": "Check SSE-KMS / TLS in-transit posture.",
    "public-access": "Check 0.0.0.0/0 ingress and public ACLs.",
    "tagging": "Check mandatory Owner/CostCenter tags.",
    "logging": "Check CloudTrail / access logging enabled.",
}


def handler(event, context):
    dimension = event.get("dimension", "unknown")
    finding = event.get("finding", {})
    detail = {
        "hint": DIMENSION_HINTS.get(dimension, "n/a"),
        "resourceId": finding.get("resourceId"),
        "correlationId": event.get("correlationId"),
        "compliant": dimension not in ("public-access",),  # demo heuristic
    }
    log.info("enrich.dimension", extra={"extra": {"dimension": dimension}})
    return {"dimension": dimension, "detail": detail}
