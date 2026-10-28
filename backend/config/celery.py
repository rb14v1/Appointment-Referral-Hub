import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("appointment_referral_hub")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "expire-waitlist-offers": {
        "task": "waitlist.tasks.expire_stale_offers",
        "schedule": crontab(minute="*/5"),
    },
    "send-appointment-reminders": {
        "task": "notifications.tasks.send_due_reminders",
        "schedule": crontab(minute="*/15"),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
