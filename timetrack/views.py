import datetime
import json
import zoneinfo
from collections import defaultdict
from urllib.parse import unquote

from constance import config
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import push
from .forms import IntervalForm
from .models import Interval, PushSubscription, round_time

RECENT_PROJECT_COUNT = 8


TZ_COOKIE = "timetrack_tz"


def _zone(name):
    try:
        return zoneinfo.ZoneInfo(name) if name else None
    except zoneinfo.ZoneInfoNotFoundError, ValueError:
        return None


def local_tz():
    """The time zone last reported by a browser, else the server's."""
    return (
        _zone(config.TIMETRACK_TIME_ZONE)
        or _zone(settings.TIME_ZONE)
        or zoneinfo.ZoneInfo("UTC")
    )


def activate_local_tz(request):
    """Use the browser's time zone (sent as a cookie) for this request.

    The browser's zone is also remembered so reminders, which run without a
    browser, follow wherever it was last used.
    """
    browser_tz = _zone(unquote(request.COOKIES.get(TZ_COOKIE, "")))
    if browser_tz and str(browser_tz) != config.TIMETRACK_TIME_ZONE:
        config.TIMETRACK_TIME_ZONE = str(browser_tz)
    tz = browser_tz or local_tz()
    timezone.activate(tz)
    return tz


def day_start(day, tz):
    return datetime.datetime.combine(day, datetime.time.min, tzinfo=tz)


def week_monday(day):
    return day - datetime.timedelta(days=day.weekday())


class Total:
    """A summed duration, flagged if it includes the running interval."""

    def __init__(self):
        self.duration = datetime.timedelta(0)
        self.live = False

    def add(self, interval, now):
        self.duration += interval.duration(now)
        self.live = self.live or interval.is_running


def total_between(start, end, now):
    total = Total()
    for interval in Interval.objects.filter(start__gte=start, start__lt=end):
        total.add(interval, now)
    return total


def recent_projects():
    return list(
        Interval.objects.values_list("project", flat=True)
        .annotate(last_used=Max("start"))
        .order_by("-last_used")[:RECENT_PROJECT_COUNT]
    )


def parse_local_datetime(value):
    """Parse a datetime-local input value in the active time zone."""
    if not value:
        return None
    try:
        naive = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None
    return timezone.make_aware(naive)


@login_required
def index(request):
    tz = activate_local_tz(request)
    now = timezone.now()
    today = timezone.localdate(now)
    this_monday = week_monday(today)

    try:
        selected = datetime.date.fromisoformat(request.GET.get("week", ""))
    except ValueError:
        selected = today
    monday = week_monday(selected)
    week_start = day_start(monday, tz)
    week_end = day_start(monday + datetime.timedelta(days=7), tz)

    days = defaultdict(lambda: {"intervals": [], "total": Total()})
    week_total = Total()
    project_totals = defaultdict(Total)
    for interval in Interval.objects.filter(
        start__gte=week_start, start__lt=week_end
    ).order_by("-start"):
        day = days[timezone.localdate(interval.start)]
        day["intervals"].append(interval)
        day["total"].add(interval, now)
        week_total.add(interval, now)
        project_totals[interval.project].add(interval, now)

    context = {
        "now": now,
        "running": Interval.running(),
        "recent_projects": recent_projects(),
        "all_projects": Interval.objects.values_list("project", flat=True)
        .distinct()
        .order_by("project"),
        "today_total": total_between(
            day_start(today, tz),
            day_start(today + datetime.timedelta(days=1), tz),
            now,
        ),
        "this_week_total": total_between(
            day_start(this_monday, tz),
            day_start(this_monday + datetime.timedelta(days=7), tz),
            now,
        ),
        "monday": monday,
        "sunday": monday + datetime.timedelta(days=6),
        "is_this_week": monday == this_monday,
        "prev_week": monday - datetime.timedelta(days=7),
        "next_week": monday + datetime.timedelta(days=7),
        "days": sorted(days.items(), reverse=True),
        "week_total": week_total,
        "project_totals": sorted(
            project_totals.items(), key=lambda item: item[1].duration, reverse=True
        ),
        "time_zone": str(tz),
        "vapid_public_key": push.public_key(),
        "push_device_count": PushSubscription.objects.count(),
    }
    return render(request, "timetrack/index.html", context)


@login_required
@require_POST
def start(request):
    activate_local_tz(request)
    project = request.POST.get("project", "").strip()
    if not project:
        messages.error(request, "A project name is required to start tracking.")
        return redirect("timetrack:index")
    started = round_time(
        parse_local_datetime(request.POST.get("start")) or timezone.now()
    )

    # Only one interval runs at a time: starting a new one stops the old one.
    running = Interval.running()
    if running:
        running.end = max(started, running.start)
        running.save()

    Interval.objects.create(
        project=project[:200],
        note=request.POST.get("note", "").strip()[:500],
        start=started,
    )
    return redirect("timetrack:index")


@login_required
@require_POST
def stop(request):
    activate_local_tz(request)
    running = Interval.running()
    if running:
        ended = parse_local_datetime(request.POST.get("end")) or timezone.now()
        running.end = max(round_time(ended), running.start)
        running.save()
    return redirect("timetrack:index")


def _week_url(interval):
    week = timezone.localdate(interval.start)
    return reverse("timetrack:index") + f"?week={week_monday(week).isoformat()}"


def _interval_form_view(request, interval):
    activate_local_tz(request)
    if request.method == "POST":
        form = IntervalForm(request.POST, instance=interval)
        if form.is_valid():
            interval = form.save()
            return redirect(_week_url(interval))
    else:
        form = IntervalForm(instance=interval)
    return render(
        request,
        "timetrack/interval_form.html",
        {
            "form": form,
            "interval": interval,
            "all_projects": Interval.objects.values_list("project", flat=True)
            .distinct()
            .order_by("project"),
        },
    )


@login_required
def add_interval(request):
    return _interval_form_view(request, None)


@login_required
def edit_interval(request, id):
    return _interval_form_view(request, get_object_or_404(Interval, id=id))


@login_required
@require_POST
def delete_interval(request, id):
    activate_local_tz(request)
    interval = get_object_or_404(Interval, id=id)
    url = _week_url(interval)
    interval.delete()
    return redirect(url)


def manifest(request):
    data = {
        "name": "Time Tracker",
        "short_name": "Timetrack",
        "start_url": reverse("timetrack:index"),
        "scope": reverse("timetrack:index"),
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#000000",
    }
    return JsonResponse(data, content_type="application/manifest+json")


SERVICE_WORKER = """
self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data.json(); } catch (e) { data = { body: event.data && event.data.text() }; }
  event.waitUntil(
    self.registration.showNotification(data.title || "Time Tracker", {
      body: data.body || "",
      data: { url: data.url || "%(index)s" },
      tag: "timetrack-reminder",
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data.url;
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((windows) => {
      for (const w of windows) {
        if (w.url.includes(url) && "focus" in w) return w.focus();
      }
      return clients.openWindow(url);
    })
  );
});
"""


def service_worker(request):
    body = SERVICE_WORKER % {"index": reverse("timetrack:index")}
    return HttpResponse(body, content_type="application/javascript")


@login_required
@require_POST
def push_subscribe(request):
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
        keys = data["keys"]
        p256dh, auth = keys["p256dh"], keys["auth"]
    except ValueError, KeyError, TypeError:
        return HttpResponseBadRequest("Invalid subscription")
    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "p256dh": p256dh,
            "auth": auth,
            "user_agent": request.headers.get("User-Agent", "")[:300],
        },
    )
    return JsonResponse({"ok": True})


@login_required
@require_POST
def push_unsubscribe(request):
    try:
        endpoint = json.loads(request.body)["endpoint"]
    except ValueError, KeyError, TypeError:
        return HttpResponseBadRequest("Invalid subscription")
    PushSubscription.objects.filter(endpoint=endpoint).delete()
    return JsonResponse({"ok": True})


@login_required
@require_POST
def push_test(request):
    sent = push.send_to_all("Time Tracker", "Test reminder — notifications work!")
    if sent:
        messages.success(request, f"Sent a test notification to {sent} device(s).")
    else:
        messages.error(request, "No devices received the test notification.")
    return redirect("timetrack:index")
