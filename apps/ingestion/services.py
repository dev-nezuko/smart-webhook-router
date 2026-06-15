from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from django.db import transaction

from apps.ingestion.models import ProcessingStatus, RawWebhook
from apps.ingestion.repositories import RawWebhookCreateResult, RawWebhookRepository
from apps.ingestion.utils import build_idempotency_key, extract_external_event_id
from apps.normalization.tasks import process_raw_webhook

logger = logging.getLogger("apps.ingestion")


class IngestionService:
    """Handle raw webhook acceptance and async dispatch."""

    @staticmethod
    def ingest(payload: Any, vendor: str) -> RawWebhookCreateResult:
        start = perf_counter()
        external_event_id = extract_external_event_id(payload)
        idempotency_key = build_idempotency_key(vendor=vendor, payload=payload, external_event_id=external_event_id)

        result = RawWebhookRepository.create_or_get(
            vendor=vendor,
            external_event_id=external_event_id,
            idempotency_key=idempotency_key,
            raw_payload=payload,
        )

        if result.created:
            transaction.on_commit(lambda: process_raw_webhook.delay(str(result.webhook.id)))

        duration_ms = (perf_counter() - start) * 1000
        logger.info(
            "webhook_accepted",
            extra={
                "webhook_id": str(result.webhook.id),
                "vendor": vendor,
                "duration_ms": round(duration_ms, 2),
                "processing_status": result.webhook.processing_status,
            },
        )
        return result


class ReplayService:
    @staticmethod
    def replay(webhook: RawWebhook, *, force: bool = False) -> bool:
        if webhook.processing_status in {ProcessingStatus.PROCESSING, ProcessingStatus.RECEIVED} and not force:
            return False
        webhook.processing_status = ProcessingStatus.RECEIVED
        webhook.error_message = ""
        webhook.save(update_fields=["processing_status", "error_message"])
        transaction.on_commit(lambda: process_raw_webhook.delay(str(webhook.id)))
        return True
