"""sentinel-fn-compliance-check :: Distributed Map worker. Receives a BATCH of inventory items."""
from sentinel_common import get_logger

log = get_logger("compliance")


def _evaluate(item):
    # Deterministic demo rule: a resource is non-compliant if flagged public or unencrypted.
    non_compliant = bool(item.get("public")) or item.get("encrypted") is False
    return {
        "resourceArn": item.get("resourceArn", item.get("resourceId", "n/a")),
        "compliant": not non_compliant,
        "reason": "public-or-unencrypted" if non_compliant else "ok",
    }


def handler(event, context):
    # With ItemBatcher, event has BatchInput + Items.
    batch_input = event.get("BatchInput", {})
    items = event.get("Items", event if isinstance(event, list) else [event])
    results = [_evaluate(i) for i in items]
    non_compliant = [r for r in results if not r["compliant"]]
    log.info("compliance.batch", extra={"extra": {
        "findingId": batch_input.get("findingId"),
        "count": len(results),
        "nonCompliant": len(non_compliant),
    }})
    return {"evaluated": len(results), "nonCompliant": len(non_compliant), "results": results}
