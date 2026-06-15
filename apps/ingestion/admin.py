from __future__ import annotations

from django.contrib import admin, messages
from django.http import HttpRequest

from apps.ingestion.models import ProcessingStatus, RawWebhook
from apps.ingestion.services import ReplayService


@admin.register(RawWebhook)
class RawWebhookAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vendor",
        "external_event_id",
        "processing_status",
        "retry_count",
        "received_at",
    )
    list_filter = ("vendor", "processing_status", "received_at")
    search_fields = ("id", "external_event_id", "idempotency_key", "vendor", "error_message")
    readonly_fields = ("id", "received_at")
    actions = ["replay_selected"]

    @admin.action(description="Replay selected failed/dead-letter webhooks")
    def replay_selected(self, request: HttpRequest, queryset):
        replayed = 0
        for webhook in queryset:
            if ReplayService.replay(webhook):
                replayed += 1
        self.message_user(request, f"Replayed {replayed} webhook(s).", level=messages.SUCCESS)
