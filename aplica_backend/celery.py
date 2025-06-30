import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aplica_backend.settings")

app = Celery("aplica_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
