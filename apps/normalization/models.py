from __future__ import annotations

from django.db import models


class EntityType(models.TextChoices):
    SHIPMENT = "SHIPMENT", "Shipment"
    INVOICE = "INVOICE", "Invoice"
    UNCLASSIFIED = "UNCLASSIFIED", "Unclassified"


class ShipmentStatus(models.TextChoices):
    PICKED_UP = "PICKED_UP", "Picked Up"
    IN_TRANSIT = "IN_TRANSIT", "In Transit"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", "Out For Delivery"
    DELIVERED = "DELIVERED", "Delivered"


class InvoiceStatus(models.TextChoices):
    ISSUED = "ISSUED", "Issued"
    PAID = "PAID", "Paid"
    VOIDED = "VOIDED", "Voided"
    REFUNDED = "REFUNDED", "Refunded"


class NormalizedEvent(models.Model):
    webhook = models.OneToOneField(
        "ingestion.RawWebhook",
        on_delete=models.CASCADE,
        related_name="normalized_event",
    )
    entity_type = models.CharField(max_length=32, choices=EntityType.choices, db_index=True)
    entity_id = models.CharField(max_length=255, db_index=True)
    canonical_status = models.CharField(max_length=64, db_index=True)
    event_time = models.DateTimeField(db_index=True)
    normalized_payload = models.JSONField()
    confidence_score = models.FloatField()
    llm_model = models.CharField(max_length=128)
    prompt_version = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-event_time"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id", "event_time"], name="norm_entity_event_idx"),
            models.Index(fields=["canonical_status", "created_at"], name="norm_status_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.entity_id}:{self.canonical_status}"
