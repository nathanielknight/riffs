from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
import secrets

from .models import ShareFile


class ShareFileModelTests(TestCase):
    def test_create_sharefile(self):
        """Test creating a ShareFile instance"""
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")

        sharefile = ShareFile.objects.create(
            title="Test File",
            file=uploaded_file
        )

        self.assertEqual(sharefile.title, "Test File")
        self.assertIsNotNone(sharefile.share_key)
        self.assertIsInstance(sharefile.share_key, str)
        self.assertGreater(len(sharefile.share_key), 0)
        self.assertIsNone(sharefile.expiration)
        self.assertIsNotNone(sharefile.created_at)
        self.assertIsNotNone(sharefile.updated_at)

    def test_sharefile_not_expired_without_expiration(self):
        """Test that files without expiration are never expired"""
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")

        sharefile = ShareFile.objects.create(
            title="Test File",
            file=uploaded_file,
            expiration=None
        )

        self.assertFalse(sharefile.is_expired())

    def test_sharefile_not_expired_with_future_expiration(self):
        """Test that files with future expiration are not expired"""
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")
        future_time = timezone.now() + timedelta(days=1)

        sharefile = ShareFile.objects.create(
            title="Test File",
            file=uploaded_file,
            expiration=future_time
        )

        self.assertFalse(sharefile.is_expired())

    def test_sharefile_expired_with_past_expiration(self):
        """Test that files with past expiration are expired"""
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")
        past_time = timezone.now() - timedelta(days=1)

        sharefile = ShareFile.objects.create(
            title="Test File",
            file=uploaded_file,
            expiration=past_time
        )

        self.assertTrue(sharefile.is_expired())

    def test_share_key_is_unique(self):
        """Test that share_key is unique across instances"""
        file_content1 = b"Test file content 1"
        file_content2 = b"Test file content 2"
        uploaded_file1 = SimpleUploadedFile("test1.txt", file_content1, content_type="text/plain")
        uploaded_file2 = SimpleUploadedFile("test2.txt", file_content2, content_type="text/plain")

        sharefile1 = ShareFile.objects.create(title="File 1", file=uploaded_file1)
        sharefile2 = ShareFile.objects.create(title="File 2", file=uploaded_file2)

        self.assertNotEqual(sharefile1.share_key, sharefile2.share_key)


class ShareFileViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_serve_valid_file(self):
        """Test serving a valid, non-expired file"""
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")

        sharefile = ShareFile.objects.create(
            title="Test File",
            file=uploaded_file
        )

        url = reverse("fileshare:serve", kwargs={"share_key": sharefile.share_key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), file_content)

    def test_serve_expired_file(self):
        """Test serving an expired file returns 403"""
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")
        past_time = timezone.now() - timedelta(days=1)

        sharefile = ShareFile.objects.create(
            title="Expired File",
            file=uploaded_file,
            expiration=past_time
        )

        url = reverse("fileshare:serve", kwargs={"share_key": sharefile.share_key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        self.assertIn(b"expired", response.content.lower())

    def test_serve_nonexistent_file(self):
        """Test serving a non-existent share_key returns 404"""
        random_key = secrets.token_urlsafe(16)
        url = reverse("fileshare:serve", kwargs={"share_key": random_key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_file_download_disposition(self):
        """Test that file response includes proper Content-Disposition header"""
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("myfile.txt", file_content, content_type="text/plain")

        sharefile = ShareFile.objects.create(
            title="Test File",
            file=uploaded_file
        )

        url = reverse("fileshare:serve", kwargs={"share_key": sharefile.share_key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Content-Disposition", response.headers)
        self.assertIn("attachment", response["Content-Disposition"])


class ShareFileIntegrationTests(TestCase):
    """Integration tests for the full create → retrieve flow."""

    def test_create_and_retrieve_file_content(self):
        """Create a ShareFile and verify the retrieved content matches exactly."""
        file_content = b"Integration test: the quick brown fox jumps over the lazy dog."
        uploaded_file = SimpleUploadedFile(
            "integration_test.txt", file_content, content_type="text/plain"
        )

        sharefile = ShareFile.objects.create(
            title="Integration Test File",
            file=uploaded_file,
        )

        # Retrieve via the share URL
        url = reverse("fileshare:serve", kwargs={"share_key": sharefile.share_key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        retrieved_content = b"".join(response.streaming_content)
        self.assertEqual(retrieved_content, file_content)

    def test_create_and_retrieve_binary_file(self):
        """Verify binary file content survives the round trip."""
        file_content = bytes(range(256))  # all byte values 0-255
        uploaded_file = SimpleUploadedFile(
            "binary_test.bin", file_content, content_type="application/octet-stream"
        )

        sharefile = ShareFile.objects.create(
            title="Binary Test File",
            file=uploaded_file,
        )

        url = reverse("fileshare:serve", kwargs={"share_key": sharefile.share_key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        retrieved_content = b"".join(response.streaming_content)
        self.assertEqual(retrieved_content, file_content)

    def test_content_disposition_has_filename(self):
        """Verify the Content-Disposition header includes a filename."""
        uploaded_file = SimpleUploadedFile(
            "my_report.pdf", b"pdf content", content_type="application/pdf"
        )

        sharefile = ShareFile.objects.create(
            title="Test PDF",
            file=uploaded_file,
        )

        url = reverse("fileshare:serve", kwargs={"share_key": sharefile.share_key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        disposition = response["Content-Disposition"]
        self.assertIn("attachment", disposition)
        # Filename is based on the stored name (Django may add a suffix for dedup)
        self.assertIn(".pdf", disposition)

    def test_share_url_with_trailing_slash(self):
        """Verify that a trailing slash on the share URL still serves the file."""
        file_content = b"trailing slash test"
        uploaded_file = SimpleUploadedFile(
            "slash_test.txt", file_content, content_type="text/plain"
        )

        sharefile = ShareFile.objects.create(
            title="Slash Test",
            file=uploaded_file,
        )

        # Manually construct URL with trailing slash
        url_with_slash = f"/share/{sharefile.share_key}/"
        response = self.client.get(url_with_slash)

        # Should still serve the file (200) or redirect to the correct URL (301/302)
        if response.status_code in (301, 302):
            # Follow the redirect
            response = self.client.get(response["Location"])

        self.assertEqual(
            response.status_code,
            200,
            f"Trailing-slash URL returned {response.status_code}; "
            f"share_key={sharefile.share_key}",
        )

    def test_expired_file_not_accessible(self):
        """Create a file, expire it, and verify it's no longer accessible."""
        file_content = b"this will expire"
        uploaded_file = SimpleUploadedFile(
            "expiring.txt", file_content, content_type="text/plain"
        )
        past_time = timezone.now() - timedelta(hours=1)

        sharefile = ShareFile.objects.create(
            title="Expiring File",
            file=uploaded_file,
            expiration=past_time,
        )

        url = reverse("fileshare:serve", kwargs={"share_key": sharefile.share_key})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_multiple_files_isolated(self):
        """Verify that creating multiple shared files doesn't cause cross-talk."""
        files = {}
        for i in range(3):
            content = f"file {i} content".encode()
            uploaded = SimpleUploadedFile(
                f"file_{i}.txt", content, content_type="text/plain"
            )
            sf = ShareFile.objects.create(title=f"File {i}", file=uploaded)
            files[sf.share_key] = content

        for share_key, expected_content in files.items():
            url = reverse("fileshare:serve", kwargs={"share_key": share_key})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            retrieved = b"".join(response.streaming_content)
            self.assertEqual(retrieved, expected_content)
