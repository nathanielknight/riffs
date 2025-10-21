from django.db import models


class RawGame(models.Model):
    title = models.TextField(null=True, blank=True)
    authors = models.TextField(null=True, blank=True)
    tags = models.TextField(null=True, blank=True)
    path = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "rawgames"

    def __str__(self):
        return self.title or f"Game {self.id}"

    @property
    def tag_list(self):
        """Return tags as a list, splitting by comma"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
        return []

    @property
    def is_starred(self):
        """Check if this game is starred"""
        return Star.objects.filter(gameid=self.id).exists()


class Star(models.Model):
    gameid = models.IntegerField(unique=True, db_column="gameid")

    class Meta:
        managed = False
        db_table = "stars"

    def __str__(self):
        return f"Star for game {self.gameid}"
