from django.db import models
from taggit.managers import TaggableManager


class Bookmark(models.Model):
    name = models.CharField(max_length=2048)
    url = models.URLField()
    notes = models.TextField(blank=True)
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
