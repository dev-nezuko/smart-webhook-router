from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from openai import APIError, APITimeoutError, OpenAI, RateLimitError

from apps.normalization.prompts import PROMPT_VERSION, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from apps.normalization.schemas import NormalizationResult

logger = logging.getLogger("apps.normalization")


class NormalizationError(Exception):
    """Non-retryable normalization errors."""


class RetryableNormalizationError(Exception):
    """Retryable normalization errors (network/rate limits/transients)."""


@dataclass(frozen=True)
class OpenAINormalizationResponse:
    normalized: NormalizationResult
    llm_model: str
    prompt_version: str


class OpenAINormalizationService:
    """Encapsulates OpenAI prompt construction and strict-response parsing."""

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise NormalizationError("OPENAI_API_KEY is not configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.OPENAI_TIMEOUT_SECONDS)

    def normalize(self, payload: Any) -> OpenAINormalizationResponse:
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
        prompt = USER_PROMPT_TEMPLATE.format(payload_json=payload_json)

        try:
            completion = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                response_format={"type": "json_object"},
                temperature=0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
        except (RateLimitError, APITimeoutError, APIError) as exc:
            raise RetryableNormalizationError(str(exc)) from exc
        except Exception as exc:
            raise NormalizationError(f"OpenAI invocation failed: {exc}") from exc

        try:
            content = completion.choices[0].message.content or "{}"
            parsed = json.loads(content)
            normalized = NormalizationResult.from_dict(parsed)
        except Exception as exc:
            raise NormalizationError(f"Malformed model response: {exc}") from exc

        return OpenAINormalizationResponse(
            normalized=normalized,
            llm_model=completion.model,
            prompt_version=settings.NORMALIZATION_PROMPT_VERSION or PROMPT_VERSION,
        )
