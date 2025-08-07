import os
import uuid
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


def recording_upload_path(instance, filename):
    return f"media/recordings/{instance.id}"


class Recording(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    audio_file = models.FileField(upload_to=recording_upload_path)
    file_size = models.BigIntegerField(editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.audio_file and hasattr(self.audio_file, "size"):
            self.file_size = self.audio_file.size
        super().save(*args, **kwargs)


@receiver(post_delete, sender=Recording)
def delete_recording_file(sender, instance, **kwargs):
    if instance.audio_file:
        if os.path.isfile(instance.audio_file.path):
            os.remove(instance.audio_file.path)
