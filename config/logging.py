from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from config.observability import get_correlation_id


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }

        for key in (
            "webhook_id",
            "vendor",
            "entity_type",
            "entity_id",
            "processing_status",
            "duration_ms",
            "retry_count",
            "task_id",
        ):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)
