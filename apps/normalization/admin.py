from django.contrib import admin

from apps.normalization.models import NormalizedEvent


@admin.register(NormalizedEvent)
class NormalizedEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "webhook",
        "entity_type",
        "entity_id",
        "canonical_status",
        "event_time",
        "confidence_score",
        "llm_model",
        "prompt_version",
        "created_at",
    )
    list_filter = ("entity_type", "canonical_status", "prompt_version", "created_at")
    search_fields = ("entity_id", "webhook__id", "canonical_status", "llm_model")
    readonly_fields = ("created_at",)
