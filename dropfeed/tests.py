import pathlib
import shutil
import tempfile
from io import StringIO

from constance import config
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Recording
from .views import _get_or_create_feed_path


class AudioFormatTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()
        # Pre-set the feed path so the views don't need to generate one.
        config.DROPFEED_URL_PATH = "test-feed-path-0123456789"
        self.user = User.objects.create_user("user", password="pw")
        self.client.force_login(self.user)

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root)

    def upload(self, filename):
        return self.client.post(
            reverse("dropfeed:index"),
            {
                "name": "Episode One",
                "description": "",
                "audio_file": SimpleUploadedFile(filename, b"audio data"),
            },
        )

    def test_upload_m4a(self):
        self.upload("episode.m4a")
        recording = Recording.objects.get()
        self.assertEqual(recording.file_extension, "m4a")
        self.assertEqual(recording.mime_type, "audio/x-m4a")

    def test_upload_mp3(self):
        self.upload("episode.MP3")
        self.assertEqual(Recording.objects.get().mime_type, "audio/mpeg")

    def test_rejects_non_audio(self):
        response = self.upload("notes.txt")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Recording.objects.exists())
        self.assertIn("audio_file", response.context["form"].errors)

    def test_feed_and_download_use_file_type(self):
        self.upload("episode.m4a")
        recording = Recording.objects.get()

        feed = self.client.get(
            reverse("dropfeed:feed", kwargs={"path": _get_or_create_feed_path()})
        )
        self.assertContains(feed, 'type="audio/x-m4a"')

        download = self.client.get(
            reverse("dropfeed:recording", kwargs={"id": recording.id})
        )
        self.assertEqual(download["Content-Type"], "audio/x-m4a")
        self.assertIn("episode-one.m4a", download["Content-Disposition"])

    def test_add_recording_command(self):
        source_dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, source_dir)
        (source_dir / "show.m4a").write_bytes(b"audio data")
        (source_dir / "notes.txt").write_bytes(b"text")

        err = StringIO()
        call_command(
            "add_recording",
            source_dir / "show.m4a",
            source_dir / "notes.txt",
            stdout=StringIO(),
            stderr=err,
        )

        recording = Recording.objects.get()
        self.assertEqual(recording.name, "show")
        self.assertEqual(recording.file_extension, "m4a")
        self.assertEqual(recording.file_size, len(b"audio data"))
        self.assertIn("notes.txt", err.getvalue())
