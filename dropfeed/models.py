import os
import uuid
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


# Audio formats accepted for upload, mapped to the MIME type used in the feed.
# MP3 and M4A (AAC) are supported by every major podcast app, including Apple
# Podcasts; the rest are supported by many (but not all) podcast players.
AUDIO_MIME_TYPES = {
    "mp3": "audio/mpeg",
    "m4a": "audio/x-m4a",
    "aac": "audio/aac",
    "ogg": "audio/ogg",
    "opus": "audio/ogg",
    "flac": "audio/flac",
    "wav": "audio/wav",
}

validate_audio_extension = FileExtensionValidator(
    allowed_extensions=list(AUDIO_MIME_TYPES)
)


def audio_extension(filename):
    return os.path.splitext(filename)[1].lstrip(".").lower()


def recording_upload_path(instance, filename):
    return f"media/recordings/{instance.id}"


class Recording(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    audio_file = models.FileField(
        upload_to=recording_upload_path, validators=[validate_audio_extension]
    )
    file_extension = models.CharField(max_length=10, default="mp3", editable=False)
    file_size = models.BigIntegerField(editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.name

    @property
    def mime_type(self):
        return AUDIO_MIME_TYPES.get(self.file_extension, "audio/mpeg")

    def save(self, *args, **kwargs):
        if self.audio_file and hasattr(self.audio_file, "size"):
            self.file_size = self.audio_file.size
        # A new upload still carries its original filename; once stored, the
        # file's name is just its ID, so remember the extension now.
        if self.audio_file and not self.audio_file._committed:
            self.file_extension = audio_extension(self.audio_file.name)
        super().save(*args, **kwargs)


@receiver(post_delete, sender=Recording)
def delete_recording_file(sender, instance, **kwargs):
    if instance.audio_file:
        if os.path.isfile(instance.audio_file.path):
            os.remove(instance.audio_file.path)
