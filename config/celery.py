"""Celery app for AnnaSetu background tasks."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("annasetu")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
