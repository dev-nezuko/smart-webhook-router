from __future__ import annotations

from django.db import transaction

from apps.ingestion.models import ProcessingStatus, RawWebhook
from apps.normalization.models import NormalizedEvent
from apps.normalization.schemas import NormalizationResult


class NormalizedEventRepository:
    @staticmethod
    @transaction.atomic
    def create_for_webhook(
        *,
        webhook: RawWebhook,
        result: NormalizationResult,
        llm_model: str,
        prompt_version: str,
    ) -> NormalizedEvent:
        normalized_event, _created = NormalizedEvent.objects.update_or_create(
            webhook=webhook,
            defaults={
                "entity_type": result.entity_type,
                "entity_id": result.entity_id,
                "canonical_status": result.canonical_status,
                "event_time": result.event_time,
                "normalized_payload": result.normalized_payload,
                "confidence_score": result.confidence_score,
                "llm_model": llm_model,
                "prompt_version": prompt_version,
            },
        )
        webhook.processing_status = ProcessingStatus.NORMALIZED
        webhook.error_message = ""
        webhook.save(update_fields=["processing_status", "error_message"])
        return normalized_event
