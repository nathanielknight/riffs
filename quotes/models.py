import secrets

from django.db import models, connection
from django.db.models.signals import post_save
from django.dispatch import receiver


class Quote(models.Model):
    slug = models.SlugField(max_length=255, unique=True, default=secrets.token_urlsafe)
    content = models.TextField()
    source = models.TextField()
    link = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


@receiver(post_save, sender=Quote)
def regenerate_quotes_index(sender, **kwargs):
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS quotes_quoteindex")
        cursor.execute(
            "CREATE VIRTUAL TABLE quotes_quoteindex USING fts5 (source, link, content, slug UNINDEXED)"
        )
        cursor.execute(
            """
            INSERT INTO quotes_quoteindex(source, link, content, slug)
            SELECT source, link, content, slug FROM quotes_quote
            """
        )
