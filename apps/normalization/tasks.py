from __future__ import annotations

import logging
from time import perf_counter

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction

from apps.entities.repositories import EntityStateRepository
from apps.ingestion.models import ProcessingStatus, RawWebhook
from apps.normalization.repositories import NormalizedEventRepository
from apps.normalization.services import (
    NormalizationError,
    OpenAINormalizationService,
    RetryableNormalizationError,
)

logger = logging.getLogger("apps.normalization")


@shared_task(bind=True, max_retries=5, autoretry_for=())
def process_raw_webhook(self, webhook_id: str) -> None:
    start = perf_counter()
    task_id = getattr(self.request, "id", None)

    webhook = RawWebhook.objects.filter(id=webhook_id).first()
    if webhook is None:
        logger.warning("webhook_not_found", extra={"webhook_id": webhook_id, "task_id": task_id})
        return

    if webhook.processing_status == ProcessingStatus.NORMALIZED:
        logger.info(
            "webhook_already_normalized",
            extra={"webhook_id": webhook_id, "task_id": task_id, "vendor": webhook.vendor},
        )
        return

    try:
        with transaction.atomic():
            locked = RawWebhook.objects.select_for_update().get(id=webhook_id)
            if locked.processing_status == ProcessingStatus.PROCESSING:
                logger.info(
                    "webhook_already_processing",
                    extra={"webhook_id": webhook_id, "vendor": locked.vendor, "task_id": task_id},
                )
                return
            locked.processing_status = ProcessingStatus.PROCESSING
            locked.save(update_fields=["processing_status"])

        service = OpenAINormalizationService()
        response = service.normalize(webhook.raw_payload)

        normalized_event = NormalizedEventRepository.create_for_webhook(
            webhook=webhook,
            result=response.normalized,
            llm_model=response.llm_model,
            prompt_version=response.prompt_version,
        )
        EntityStateRepository.upsert_if_newer(normalized_event)

        duration_ms = round((perf_counter() - start) * 1000, 2)
        logger.info(
            "webhook_processed",
            extra={
                "webhook_id": webhook_id,
                "vendor": webhook.vendor,
                "entity_type": normalized_event.entity_type,
                "entity_id": normalized_event.entity_id,
                "processing_status": ProcessingStatus.NORMALIZED,
                "duration_ms": duration_ms,
                "task_id": task_id,
            },
        )
    except RetryableNormalizationError as exc:
        webhook.retry_count += 1
        webhook.processing_status = ProcessingStatus.FAILED
        webhook.error_message = str(exc)
        webhook.save(update_fields=["retry_count", "processing_status", "error_message"])
        retry_delay = min(2 ** self.request.retries, 300)
        logger.warning(
            "webhook_retry_scheduled",
            extra={
                "webhook_id": webhook_id,
                "vendor": webhook.vendor,
                "retry_count": webhook.retry_count,
                "task_id": task_id,
            },
        )
        try:
            raise self.retry(exc=exc, countdown=retry_delay)
        except MaxRetriesExceededError:
            webhook.processing_status = ProcessingStatus.DEAD_LETTER
            webhook.error_message = f"Max retries exceeded: {exc}"
            webhook.save(update_fields=["processing_status", "error_message"])
            logger.error(
                "webhook_dead_letter",
                extra={"webhook_id": webhook_id, "vendor": webhook.vendor, "task_id": task_id},
            )
    except NormalizationError as exc:
        webhook.processing_status = ProcessingStatus.FAILED
        webhook.error_message = str(exc)
        webhook.save(update_fields=["processing_status", "error_message"])
        logger.error(
            "webhook_normalization_failed",
            extra={"webhook_id": webhook_id, "vendor": webhook.vendor, "task_id": task_id},
            exc_info=True,
        )
    except Exception as exc:
        webhook.processing_status = ProcessingStatus.FAILED
        webhook.error_message = f"Unexpected worker failure: {exc}"
        webhook.save(update_fields=["processing_status", "error_message"])
        logger.exception(
            "webhook_worker_unexpected_failure",
            extra={"webhook_id": webhook_id, "vendor": webhook.vendor, "task_id": task_id},
        )
