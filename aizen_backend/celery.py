from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ["DJANGO_SETTINGS_MODULE"] = "aizen_backend.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aizen_backend.settings")

app = Celery("aizen_backend")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Pick up tasks from all installed apps
app.autodiscover_tasks()
