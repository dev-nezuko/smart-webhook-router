"""Isolated permission regression tests; no PostgreSQL, Redis or provider required."""
from .settings import *  # noqa: F403
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
SECRET_KEY = "synthetic-test-settings-only-not-for-deployment"
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
