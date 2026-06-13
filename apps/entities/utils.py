from __future__ import annotations


def entity_cache_key(entity_type: str, entity_id: str) -> str:
    return f"entity-state:{entity_type}:{entity_id}"
