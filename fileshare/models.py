import uuid
from django.db import models
from django.utils import timezone


class ShareFile(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='sharefiles/')
    share_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
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
