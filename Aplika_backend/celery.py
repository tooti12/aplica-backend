import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Aplika_backend.settings")

app = Celery("Aplika_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
