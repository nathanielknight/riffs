import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from timetrack.models import Interval
from timetrack.push import send_to_all
from timetrack.views import day_start, local_tz

# A running interval older than this gets a "did you forget to stop?" nudge.
LONG_RUNNING = datetime.timedelta(hours=10)


def reminder_message(now=None):
    """Work out what (if anything) the daily reminder should say."""
    tz = local_tz()
    now = now or timezone.now()
    today = timezone.localdate(now, tz)
    running = Interval.running()
    if running:
        if now - running.start >= LONG_RUNNING:
            since = timezone.localtime(running.start, tz)
            return f"Still tracking {running.project} since {since:%a %H:%M}. Forget to stop?"
        return None
    tracked_today = Interval.objects.filter(
        start__gte=day_start(today, tz),
        start__lt=day_start(today + datetime.timedelta(days=1), tz),
    ).exists()
    if not tracked_today:
        return "Nothing tracked today. Log your time?"
    return None


class Command(BaseCommand):
    help = (
        "Send a time tracking reminder push notification if nothing has been "
        "tracked today (or an interval has been running a long time). "
        "Schedule with cron at the time you want to be reminded."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--always",
            action="store_true",
            help="Send a reminder even if time has already been tracked today.",
        )

    def handle(self, *args, **options):
        message = reminder_message()
        if message is None and options["always"]:
            message = "Remember to track your time."
        if message is None:
            self.stdout.write("Time already tracked today; no reminder sent.")
            return
        sent = send_to_all("Time Tracker", message)
        self.stdout.write(self.style.SUCCESS(f"Sent reminder to {sent} device(s)."))
