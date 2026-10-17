import datetime
import zoneinfo
from io import StringIO
from unittest import mock

from constance import config
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .management.commands.timetrack_remind import reminder_message
from .models import Interval, PushSubscription, round_time

TZ = zoneinfo.ZoneInfo("America/Toronto")


def local(*args):
    return datetime.datetime(*args, tzinfo=TZ)


class RoundTimeTests(TestCase):
    def test_rounds_to_nearest_five_minutes(self):
        self.assertEqual(
            round_time(local(2026, 1, 1, 9, 2, 29)), local(2026, 1, 1, 9, 0)
        )
        self.assertEqual(
            round_time(local(2026, 1, 1, 9, 2, 30)), local(2026, 1, 1, 9, 5)
        )
        self.assertEqual(round_time(local(2026, 1, 1, 9, 58)), local(2026, 1, 1, 10, 0))
        self.assertEqual(round_time(local(2026, 1, 1, 23, 59)), local(2026, 1, 2, 0, 0))

    def test_save_rounds(self):
        interval = Interval.objects.create(
            project="p", start=local(2026, 1, 1, 9, 3), end=local(2026, 1, 1, 9, 51)
        )
        interval.refresh_from_db()
        self.assertEqual(interval.start, local(2026, 1, 1, 9, 5))
        self.assertEqual(interval.end, local(2026, 1, 1, 9, 50))


class TimetrackViewTests(TestCase):
    def setUp(self):
        config.TIMETRACK_TIME_ZONE = "America/Toronto"
        self.user = User.objects.create_user("user", password="pw")
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("timetrack:index"))
        self.assertEqual(response.status_code, 302)

    def test_start_and_stop(self):
        self.client.post(reverse("timetrack:start"), {"project": "Acme remote"})
        running = Interval.running()
        self.assertEqual(running.project, "Acme remote")
        self.assertEqual(running.start.minute % 5, 0)

        self.client.post(reverse("timetrack:stop"))
        self.assertIsNone(Interval.running())
        self.assertIsNotNone(Interval.objects.get().end)

    def test_starting_stops_running_interval(self):
        self.client.post(
            reverse("timetrack:start"), {"project": "A", "start": "2026-10-14T09:00"}
        )
        self.client.post(
            reverse("timetrack:start"), {"project": "B", "start": "2026-10-14T11:30"}
        )
        a = Interval.objects.get(project="A")
        self.assertEqual(a.start, local(2026, 10, 14, 9, 0))
        self.assertEqual(a.end, local(2026, 10, 14, 11, 30))
        self.assertEqual(Interval.running().project, "B")

    def test_stop_at_explicit_time(self):
        Interval.objects.create(project="A", start=local(2026, 10, 14, 9, 0))
        self.client.post(reverse("timetrack:stop"), {"end": "2026-10-14T12:07"})
        self.assertEqual(Interval.objects.get().end, local(2026, 10, 14, 12, 5))

    def test_edit_rejects_end_before_start(self):
        interval = Interval.objects.create(
            project="A", start=local(2026, 10, 14, 9), end=local(2026, 10, 14, 10)
        )
        response = self.client.post(
            reverse("timetrack:edit", args=[interval.id]),
            {"project": "A", "start": "2026-10-14T09:00", "end": "2026-10-14T08:00"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("end", response.context["form"].errors)

    def test_edit_to_open_interval(self):
        interval = Interval.objects.create(
            project="A", start=local(2026, 10, 14, 9), end=local(2026, 10, 14, 10)
        )
        self.client.post(
            reverse("timetrack:edit", args=[interval.id]),
            {"project": "A", "start": "2026-10-14T09:00", "end": ""},
        )
        self.assertEqual(Interval.running(), interval)

    def test_add_and_delete(self):
        self.client.post(
            reverse("timetrack:add"),
            {
                "project": "A",
                "note": "n",
                "start": "2026-10-13T09:00",
                "end": "2026-10-13T10:00",
            },
        )
        interval = Interval.objects.get()
        self.assertEqual(interval.duration(), datetime.timedelta(hours=1))
        self.client.post(reverse("timetrack:delete", args=[interval.id]))
        self.assertFalse(Interval.objects.exists())

    def make_week(self):
        # Monday and Tuesday of the week of 2026-10-12, plus one the week before.
        Interval.objects.create(
            project="Acme", start=local(2026, 10, 12, 9), end=local(2026, 10, 12, 11)
        )
        Interval.objects.create(
            project="Acme",
            note="Standup",
            start=local(2026, 10, 13, 9),
            end=local(2026, 10, 13, 9, 30),
        )
        Interval.objects.create(
            project="Other", start=local(2026, 10, 13, 22), end=local(2026, 10, 13, 23)
        )
        Interval.objects.create(
            project="Old", start=local(2026, 10, 11, 9), end=local(2026, 10, 11, 10)
        )

    def test_week_view_totals(self):
        self.make_week()
        response = self.client.get(reverse("timetrack:week", args=["2026-10-15"]))
        ctx = response.context
        self.assertEqual(ctx["monday"], datetime.date(2026, 10, 12))
        self.assertEqual(
            ctx["week_total"].duration, datetime.timedelta(hours=3, minutes=30)
        )
        totals = {p: t.duration for p, t in ctx["project_totals"]}
        self.assertEqual(
            totals,
            {
                "Acme": datetime.timedelta(hours=2, minutes=30),
                "Other": datetime.timedelta(hours=1),
            },
        )
        days = {day: (total, dict(projects)) for day, total, projects in ctx["days"]}
        self.assertEqual(
            list(days), [datetime.date(2026, 10, 12), datetime.date(2026, 10, 13)]
        )
        # 22:00 Toronto on the 13th is the 14th in UTC; it should count on the 13th.
        total, projects = days[datetime.date(2026, 10, 13)]
        self.assertEqual(total.duration, datetime.timedelta(hours=1, minutes=30))
        self.assertEqual(
            projects["Acme"]["total"].duration, datetime.timedelta(minutes=30)
        )
        self.assertEqual(projects["Acme"]["notes"], ["Standup"])
        self.assertContains(response, "3:30")

    def test_week_view_rejects_bad_date(self):
        response = self.client.get(reverse("timetrack:week", args=["nope"]))
        self.assertEqual(response.status_code, 404)

    def test_weeks_list(self):
        self.make_week()
        response = self.client.get(reverse("timetrack:weeks"))
        weeks = [(w["monday"], w["total"].duration) for w in response.context["weeks"]]
        self.assertEqual(
            weeks,
            [
                (datetime.date(2026, 10, 12), datetime.timedelta(hours=3, minutes=30)),
                (datetime.date(2026, 10, 5), datetime.timedelta(hours=1)),
            ],
        )
        self.assertContains(response, reverse("timetrack:week", args=["2026-10-12"]))

    def test_index_shows_current_week_only(self):
        self.make_week()
        today = local(2026, 10, 14, 12)
        with mock.patch("django.utils.timezone.now", return_value=today):
            response = self.client.get(reverse("timetrack:index"))
        ctx = response.context
        self.assertEqual(ctx["monday"], datetime.date(2026, 10, 12))
        days = dict(ctx["days"])
        self.assertEqual(
            list(days), [datetime.date(2026, 10, 13), datetime.date(2026, 10, 12)]
        )
        self.assertEqual(
            ctx["week_total"].duration, datetime.timedelta(hours=3, minutes=30)
        )

    def test_index_start_controls_only_when_idle(self):
        response = self.client.get(reverse("timetrack:index"))
        self.assertContains(response, "Not tracking")
        self.assertNotContains(response, "Switch task")
        Interval.objects.create(project="A", start=local(2026, 10, 14, 9))
        response = self.client.get(reverse("timetrack:index"))
        self.assertNotContains(response, "Not tracking")
        self.assertContains(response, "Switch task")

    def test_editing_past_entry_returns_to_its_week(self):
        interval = Interval.objects.create(
            project="A", start=local(2020, 3, 4, 9), end=local(2020, 3, 4, 10)
        )
        response = self.client.post(
            reverse("timetrack:edit", args=[interval.id]),
            {"project": "B", "start": "2020-03-04T09:00", "end": "2020-03-04T10:00"},
        )
        self.assertRedirects(response, reverse("timetrack:week", args=["2020-03-02"]))

    def test_recent_tasks_offered_for_quick_start(self):
        Interval.objects.create(
            project="Old", start=local(2026, 10, 1, 9), end=local(2026, 10, 1, 10)
        )
        Interval.objects.create(
            project="Acme remote",
            note="Standup",
            start=local(2026, 10, 12, 9),
            end=local(2026, 10, 12, 10),
        )
        Interval.objects.create(
            project="Acme remote",
            note="Code review",
            start=local(2026, 10, 13, 9),
            end=local(2026, 10, 13, 10),
        )
        Interval.objects.create(
            project="Old", start=local(2026, 9, 1, 9), end=local(2026, 9, 1, 10)
        )
        response = self.client.get(reverse("timetrack:index"))
        self.assertEqual(
            response.context["recent_tasks"],
            [("Acme remote", "Code review"), ("Acme remote", "Standup"), ("Old", "")],
        )
        self.assertContains(
            response,
            '<span>Acme remote<span class="note">Code review</span></span>'
            '<span class="label">Start →</span>',
            html=False,
        )
        self.assertContains(
            response, '<input type="hidden" name="note" value="Standup">', html=False
        )

    def test_quick_start_carries_note(self):
        self.client.post(
            reverse("timetrack:start"), {"project": "Acme", "note": "Standup"}
        )
        running = Interval.running()
        self.assertEqual((running.project, running.note), ("Acme", "Standup"))

    def test_push_subscribe_and_unsubscribe(self):
        sub = {
            "endpoint": "https://push.example.com/abc",
            "keys": {"p256dh": "key", "auth": "secret"},
        }
        response = self.client.post(
            reverse("timetrack:push_subscribe"), sub, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PushSubscription.objects.get().auth, "secret")
        self.client.post(
            reverse("timetrack:push_unsubscribe"),
            {"endpoint": sub["endpoint"]},
            content_type="application/json",
        )
        self.assertFalse(PushSubscription.objects.exists())

    def test_service_worker_and_manifest(self):
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse("timetrack:service_worker"))["Content-Type"],
            "application/javascript",
        )
        self.assertEqual(
            self.client.get(reverse("timetrack:manifest")).json()["start_url"],
            "/timetrack/",
        )


class BrowserTimeZoneTests(TestCase):
    def setUp(self):
        config.TIMETRACK_TIME_ZONE = ""
        self.client.force_login(User.objects.create_user("user", password="pw"))

    def test_defaults_to_server_time_zone(self):
        response = self.client.get(reverse("timetrack:index"))
        self.assertEqual(response.context["time_zone"], "America/Vancouver")

    def test_browser_time_zone_is_used_and_remembered(self):
        self.client.cookies["timetrack_tz"] = "Europe/Zurich"
        self.client.post(
            reverse("timetrack:start"), {"project": "A", "start": "2026-10-14T09:00"}
        )
        self.assertEqual(
            Interval.objects.get().start,
            datetime.datetime(
                2026, 10, 14, 9, tzinfo=zoneinfo.ZoneInfo("Europe/Zurich")
            ),
        )
        # Reminders run without a browser, so they use the remembered zone.
        self.assertEqual(config.TIMETRACK_TIME_ZONE, "Europe/Zurich")

    def test_url_encoded_cookie(self):
        self.client.cookies["timetrack_tz"] = "Europe%2FLondon"
        response = self.client.get(reverse("timetrack:index"))
        self.assertEqual(response.context["time_zone"], "Europe/London")

    def test_invalid_browser_time_zone_is_ignored(self):
        self.client.cookies["timetrack_tz"] = "Not/AZone"
        response = self.client.get(reverse("timetrack:index"))
        self.assertEqual(response.context["time_zone"], "America/Vancouver")
        self.assertEqual(config.TIMETRACK_TIME_ZONE, "")


class ReminderTests(TestCase):
    def setUp(self):
        config.TIMETRACK_TIME_ZONE = "America/Toronto"

    def test_reminds_when_nothing_tracked(self):
        now = local(2026, 10, 14, 17)
        Interval.objects.create(
            project="A", start=local(2026, 10, 13, 9), end=local(2026, 10, 13, 10)
        )
        self.assertIn("Nothing tracked", reminder_message(now))

    def test_quiet_when_tracked_today(self):
        now = local(2026, 10, 14, 17)
        Interval.objects.create(
            project="A", start=local(2026, 10, 14, 9), end=local(2026, 10, 14, 10)
        )
        self.assertIsNone(reminder_message(now))

    def test_nudges_long_running_interval(self):
        now = local(2026, 10, 14, 17)
        Interval.objects.create(project="A", start=local(2026, 10, 13, 9))
        self.assertIn("Still tracking A", reminder_message(now))

    def test_command_sends_push_and_prunes_expired(self):
        PushSubscription.objects.create(
            endpoint="https://push.example.com/gone", p256dh="k", auth="a"
        )
        from pywebpush import WebPushException

        gone = mock.Mock(status_code=410)
        with mock.patch(
            "timetrack.push.webpush",
            side_effect=WebPushException("gone", response=gone),
        ) as webpush:
            call_command("timetrack_remind", stdout=StringIO())
        webpush.assert_called_once()
        self.assertFalse(PushSubscription.objects.exists())
