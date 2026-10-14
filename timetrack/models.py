import datetime

from django.db import models
from django.utils import timezone

GRANULARITY = datetime.timedelta(minutes=5)


def round_time(dt):
    """Round a datetime to the nearest multiple of GRANULARITY."""
    if dt is None:
        return None
    step = int(GRANULARITY.total_seconds())
    floored = dt.replace(second=0, microsecond=0) - datetime.timedelta(
        minutes=dt.minute % (step // 60)
    )
    if (dt - floored).total_seconds() >= step / 2:
        floored += GRANULARITY
    return floored


class Interval(models.Model):
    project = models.CharField(max_length=200)
    note = models.CharField(max_length=500, blank=True)
    start = models.DateTimeField()
    # A null end means the interval is still running.
    end = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-start"]

    def __str__(self):
        return f"{self.project} ({self.start:%Y-%m-%d %H:%M})"

    def save(self, *args, **kwargs):
        self.start = round_time(self.start)
        self.end = round_time(self.end)
        super().save(*args, **kwargs)

    @property
    def is_running(self):
        return self.end is None

    def duration(self, now=None):
        end = self.end or now or timezone.now()
        return max(end - self.start, datetime.timedelta(0))

    @classmethod
    def running(cls):
        return cls.objects.filter(end__isnull=True).order_by("-start").first()


class PushSubscription(models.Model):
    """A browser/device that has opted into reminder notifications."""

    endpoint = models.URLField(max_length=1000, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_agent or self.endpoint[:60]

    def as_subscription_info(self):
        return {
            "endpoint": self.endpoint,
            "keys": {"p256dh": self.p256dh, "auth": self.auth},
        }
