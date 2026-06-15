from __future__ import annotations

from rest_framework import serializers


class NormalizedEventSerializer(serializers.Serializer):
    webhook_id = serializers.UUIDField(source="webhook.id")
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
    canonical_status = serializers.CharField()
    event_time = serializers.DateTimeField()
    confidence_score = serializers.FloatField()
    llm_model = serializers.CharField()
    prompt_version = serializers.CharField()
    created_at = serializers.DateTimeField()
