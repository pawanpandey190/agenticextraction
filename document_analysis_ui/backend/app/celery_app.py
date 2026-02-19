"""Celery application configuration."""

from celery import Celery
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "document_analysis",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.api_timeout_seconds,
)

# Discover tasks from tasks.py
celery_app.autodiscover_tasks(["app"])
