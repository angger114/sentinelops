"""SentinelOps shared layer: structured logging, JSON-safe Dynamo helpers, backoff."""
import json
import logging
import os
import time
from decimal import Decimal

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "sentinelops",
        }
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def get_logger(name="sentinelops"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(JsonFormatter())
        logger.addHandler(h)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False
    return logger


def to_dynamo_safe(obj):
    """DynamoDB put_item() rejects Python float — convert to Decimal(str(v))."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, list):
        return [to_dynamo_safe(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_dynamo_safe(v) for k, v in obj.items()}
    return obj


def from_dynamo(obj):
    """Reverse: Decimal -> int/float for JSON responses."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, list):
        return [from_dynamo(v) for v in obj]
    if isinstance(obj, dict):
        return {k: from_dynamo(v) for k, v in obj.items()}
    return obj


def with_backoff(fn, retries=3, base=0.5, cap=8.0):
    attempt = 0
    while True:
        try:
            return fn()
        except Exception:
            attempt += 1
            if attempt > retries:
                raise
            time.sleep(min(cap, base * (2 ** (attempt - 1))))
