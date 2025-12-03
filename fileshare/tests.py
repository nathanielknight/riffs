from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
import uuid

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
        self.assertIsInstance(sharefile.share_key, uuid.UUID)
        self.assertIsNone(sharefile.expiration)
        self.assertIsNotNone(sharefile.created_at)
        self.assertIsNotNone(sharefile.updated_at)

    def test_sharefile_string_representation(self):
        """Test __str__ method returns title"""
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")

        sharefile = ShareFile.objects.create(
            title="My Test File",
            file=uploaded_file
        )

        self.assertEqual(str(sharefile), "My Test File")

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
        random_uuid = uuid.uuid4()
        url = reverse("fileshare:serve", kwargs={"share_key": random_uuid})
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
