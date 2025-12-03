import secrets
from django.db import models
from django.utils import timezone


def generate_share_key():
    """Generate a URL-safe token for sharing"""
    return secrets.token_urlsafe(16)


class ShareFile(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='sharefiles/')
    share_key = models.CharField(max_length=64, default=generate_share_key, unique=True, editable=False)
    expiration = models.DateTimeField(null=True, blank=True, help_text="Leave blank for no expiration")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_expired(self):
        """Check if the file has expired"""
        if self.expiration is None:
            return False
        return timezone.now() > self.expiration

    class Meta:
        ordering = ['-created_at']
