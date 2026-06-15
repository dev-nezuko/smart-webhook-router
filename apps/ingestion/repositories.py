from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import IntegrityError, transaction

from apps.ingestion.models import ProcessingStatus, RawWebhook


@dataclass(frozen=True)
class RawWebhookCreateResult:
    webhook: RawWebhook
    created: bool


class RawWebhookRepository:
    """Repository for raw webhook persistence and retrieval."""

    @staticmethod
    def create_or_get(
        *,
        vendor: str,
        external_event_id: str | None,
        idempotency_key: str,
        raw_payload: Any,
    ) -> RawWebhookCreateResult:
        defaults = {
            "external_event_id": external_event_id,
            "raw_payload": raw_payload,
            "processing_status": ProcessingStatus.RECEIVED,
        }
        try:
            with transaction.atomic():
                webhook, created = RawWebhook.objects.get_or_create(
                    vendor=vendor,
                    idempotency_key=idempotency_key,
                    defaults=defaults,
                )
                return RawWebhookCreateResult(webhook=webhook, created=created)
        except IntegrityError:
            webhook = RawWebhook.objects.get(vendor=vendor, idempotency_key=idempotency_key)
            return RawWebhookCreateResult(webhook=webhook, created=False)

    @staticmethod
    def get_by_id(webhook_id: str) -> RawWebhook:
        return RawWebhook.objects.get(id=webhook_id)
