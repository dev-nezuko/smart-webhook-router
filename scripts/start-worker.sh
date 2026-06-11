#!/usr/bin/env sh
set -e

celery -A config worker -Q normalization --loglevel=INFO --concurrency=4
